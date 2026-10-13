#!/usr/bin/env python3
"""What does a login reveal to anyone relaying it? A UDP relay sits between the
laptop and the home server (where the access point and proxies sit) and records
every RADIUS packet. We then search the EAP payloads for the name in the device
certificate, under TLS 1.2 and TLS 1.3."""
import json, os, socket, subprocess, threading, time

TB = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(TB, "pki_srv")
W = os.path.join(TB, "srv")
NAME = b"laptop@unc.test"


def relay(listen, upstream, log, stop):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", listen))
    s.settimeout(0.2)
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    u.settimeout(0.2)
    client = None
    while not stop.is_set():
        try:
            data, addr = s.recvfrom(65535)
            client = addr
            log.append(("to_server", data))
            u.sendto(data, ("127.0.0.1", upstream))
        except socket.timeout:
            pass
        try:
            data, _ = u.recvfrom(65535)
            log.append(("to_laptop", data))
            if client:
                s.sendto(data, client)
        except socket.timeout:
            pass
    s.close(); u.close()


def eap_payload(pkt):
    """Concatenate EAP-Message (type 79) attributes of one RADIUS packet."""
    out, i = b"", 20
    while i + 2 <= len(pkt):
        t, l = pkt[i], pkt[i + 1]
        if l < 2:
            break
        if t == 79:
            out += pkt[i + 2:i + l]
        i += l
    return out


def run(tls13):
    conf = f"{W}/hostapd_priv.conf"
    with open(conf, "w") as f:
        f.write(f"""driver=none
logger_stdout=-1
logger_stdout_level=2
eap_server=1
eap_user_file={W}/eap_user
ca_cert={P}/ca.crt
server_cert={P}/srv_good.crt
private_key={P}/srv_good.key
radius_server_clients={W}/radius_clients
radius_server_auth_port=18130
tls_flags={'[ENABLE-TLSv1.3]' if tls13 else '[DISABLE-TLSv1.3]'}
""")
    hp = subprocess.Popen(["hostapd", conf], stdout=open(f"{W}/hostapd_priv.log", "w"), stderr=subprocess.STDOUT)
    time.sleep(1)
    log, stop = [], threading.Event()
    th = threading.Thread(target=relay, args=(18131, 18130, log, stop)); th.start()
    lc = f"{W}/laptop_priv.conf"
    with open(lc, "w") as f:
        f.write(f"""network={{
\tssid="eduroam"
\tkey_mgmt=WPA-EAP
\teap=TLS
\tidentity="anonymous@unc.test"
\tca_cert="{P}/ca.crt"
\tclient_cert="{P}/laptop.crt"
\tprivate_key="{P}/laptop.key"
\tphase1="tls_disable_tlsv1_3={0 if tls13 else 1}"
}}
""")
    r = subprocess.run(["eapol_test", "-c", lc, "-a", "127.0.0.1", "-p", "18131", "-s", "testing123", "-t", "6"],
                       capture_output=True, text=True)
    stop.set(); th.join(); hp.terminate(); hp.wait()
    up = b"".join(eap_payload(p) for d, p in log if d == "to_server")
    ver = "TLS 1.3" if "TLSv1.3" in r.stdout or "TLS 1.3" in r.stdout else "?"
    for line in r.stdout.splitlines():
        if "tls_version" in line.lower() or "TLSv1." in line:
            ver = line.strip(); break
    return {"tls13_enabled": tls13, "login_ok": "SUCCESS" in r.stdout,
            "packets": len(log), "bytes_from_laptop": len(up),
            "name_visible_to_relays": NAME in up, "version_hint": ver}


res = {"TLS 1.2": run(False), "TLS 1.3": run(True)}
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(TB, "results", "privacy.json"), "w"), indent=1)
