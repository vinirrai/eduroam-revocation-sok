#!/usr/bin/env python3
"""Server-direction experiment: does the laptop notice that the home server's
certificate was revoked? hostapd plays a RADIUS server that can staple OCSP
responses; eapol_test (wpa_supplicant's EAP code) plays the laptop with
ocsp=0 (default), 1 (ask, accept if missing) and 2 (require)."""
import json, os, subprocess, time

TB = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(TB, "pki_srv")
W = os.path.join(TB, "srv")
os.makedirs(W, exist_ok=True)
env = dict(os.environ, PKI_DIR=P)


def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True, env=env)


sh(f"{TB}/pki.sh init")
sh(f"{TB}/pki.sh issue-server srv_good 730")
sh(f"{TB}/pki.sh issue-server srv_leaked 730")
sh(f"{TB}/pki.sh issue laptop 1461")
sh(f"{TB}/pki.sh revoke srv_leaked")  # the server's key leaked, so its cert was revoked


def staple(name):
    req, resp = f"{W}/{name}.req", f"{W}/{name}.resp.der"
    sh(f"openssl ocsp -issuer {P}/ca.crt -cert {P}/{name}.crt -reqout {req} -no_nonce")
    sh(f"openssl ocsp -index {P}/index.txt -CA {P}/ca.crt -rsigner {P}/ocsp.crt -rkey {P}/ocsp.key "
       f"-reqin {req} -respout {resp} -ndays 1")
    st = sh(f"openssl ocsp -respin {resp} -issuer {P}/ca.crt -cert {P}/{name}.crt -CAfile {P}/ca.crt")
    line = st.stdout.strip().splitlines()[0] if st.stdout else "?"
    return resp, line.replace(TB + "/", "")  # keep paths relative to testbed/


open(f"{W}/eap_user", "w").write('* TLS\n')
open(f"{W}/radius_clients", "w").write('127.0.0.1/32 testing123\n')


def hostapd(cert, resp=None):
    conf = f"{W}/hostapd.conf"
    with open(conf, "w") as f:
        f.write(f"""driver=none
logger_stdout=-1
logger_stdout_level=2
eap_server=1
eap_user_file={W}/eap_user
ca_cert={P}/ca.crt
server_cert={P}/{cert}.crt
private_key={P}/{cert}.key
radius_server_clients={W}/radius_clients
radius_server_auth_port=18130
tls_flags=[DISABLE-TLSv1.3]
""")
        if resp:
            f.write(f"ocsp_stapling_response={resp}\n")
    p = subprocess.Popen(["hostapd", conf], stdout=open(f"{W}/hostapd.log", "w"), stderr=subprocess.STDOUT)
    time.sleep(1.0)
    return p


def laptop(ocsp):
    conf = f"{W}/laptop_ocsp{ocsp}.conf"
    with open(conf, "w") as f:
        f.write(f"""network={{
\tssid="eduroam"
\tkey_mgmt=WPA-EAP
\teap=TLS
\tidentity="anonymous@unc.test"
\tca_cert="{P}/ca.crt"
\tclient_cert="{P}/laptop.crt"
\tprivate_key="{P}/laptop.key"
\tphase1="tls_disable_tlsv1_3=1"
\tocsp={ocsp}
}}
""")
    r = subprocess.run(["eapol_test", "-c", conf, "-a", "127.0.0.1", "-p", "18130", "-s", "testing123", "-t", "6"],
                       capture_output=True, text=True)
    return "SUCCESS" in r.stdout


scenarios = [
    ("Valid server, no staple", "srv_good", False),
    ("Revoked server, no staple", "srv_leaked", False),
    ("Revoked server, staples its status", "srv_leaked", True),
    ("Valid server, staples its status", "srv_good", True),
]
out = []
for label, cert, do_staple in scenarios:
    resp, status = staple(cert) if do_staple else (None, None)
    hp = hostapd(cert, resp)
    row = {"scenario": label, "cert": cert, "stapled_status": status}
    for o in (0, 1, 2):
        row[f"ocsp={o}"] = laptop(o)
    hp.terminate(); hp.wait(); time.sleep(0.3)
    out.append(row)
    print(row, flush=True)
json.dump(out, open(os.path.join(TB, "results", "server_direction.json"), "w"), indent=1)
