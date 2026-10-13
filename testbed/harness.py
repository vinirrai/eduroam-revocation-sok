#!/usr/bin/env python3
"""Testbed harness: start a home RADIUS server under one revocation mechanism,
'graduate' a user, and measure how long their device keeps getting on.

usage:
  harness.py selftest
  harness.py latency  [N]
  harness.py window   [timeout_s]
"""
import json, os, signal, socket, statistics, subprocess, sys, time

TB = os.path.dirname(os.path.abspath(__file__))
PKI = os.path.join(TB, "pki")
RES = os.path.join(TB, "results")
os.makedirs(RES, exist_ok=True)
os.makedirs(os.path.join(TB, "clients"), exist_ok=True)


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


def wait_port(port, udp=True, t=5):
    # FreeRADIUS has no readiness probe we can poll cheaply over UDP; give it a moment.
    time.sleep(1.2)


class Server:
    def __init__(self, mech, tls_max="1.2", crl_reload="30"):
        self.dir = os.path.join(TB, f"rad_{mech}_{tls_max}")
        env = dict(os.environ, CRL_RELOAD=str(crl_reload))
        subprocess.run([sys.executable, "-I", os.path.join(TB, "gen.py"), self.dir, mech, tls_max],
                       check=True, capture_output=True, env=env)
        self.log = open(os.path.join(self.dir, "server.log"), "w")
        self.p = subprocess.Popen(["freeradius", "-f", "-d", self.dir, "-l", "stdout"],
                                  stdout=self.log, stderr=subprocess.STDOUT)
        wait_port(18120)
        if self.p.poll() is not None:
            raise RuntimeError(f"freeradius failed, see {self.dir}/server.log")

    def stop(self):
        self.p.terminate()
        try:
            self.p.wait(5)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.log.close()
        time.sleep(0.3)


class OCSPResponder:
    def __init__(self):
        self.p = subprocess.Popen(
            ["openssl", "ocsp", "-index", f"{PKI}/index.txt", "-port", "8888",
             "-rsigner", f"{PKI}/ocsp.crt", "-rkey", f"{PKI}/ocsp.key", "-CA", f"{PKI}/ca.crt",
             "-nmin", "1"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.8)

    def restart(self):
        self.stop()
        self.__init__()

    def stop(self):
        self.p.terminate()
        self.p.wait()


def client_conf(user, tls13=False, extra=""):
    path = os.path.join(TB, "clients", f"{user}{'_13' if tls13 else ''}.conf")
    with open(path, "w") as f:
        f.write(f"""network={{
\tssid="eduroam"
\tkey_mgmt=WPA-EAP
\teap=TLS
\tidentity="anonymous@unc.test"
\tca_cert="{PKI}/ca.crt"
\tclient_cert="{PKI}/{user}.crt"
\tprivate_key="{PKI}/{user}.key"
\tphase1="tls_disable_tlsv1_3={0 if tls13 else 1}"
{extra}}}
""")
    return path


def login(user, port=18120, tls13=False, conf=None):
    conf = conf or client_conf(user, tls13)
    t0 = time.perf_counter()
    r = subprocess.run(["eapol_test", "-c", conf, "-a", "127.0.0.1", "-p", str(port), "-s", "testing123", "-t", "6"],
                       capture_output=True, text=True)
    dt = (time.perf_counter() - t0) * 1000
    return r.returncode == 0 and "SUCCESS" in r.stdout, dt, r.stdout


def new_user(name, validity="1461"):
    sh(f"{TB}/pki.sh issue {name} {validity}")
    sh(f"""ldapadd -x -H ldap://127.0.0.1:3890 -D cn=admin,dc=unc,dc=test -w secret <<EOF
dn: uid={name},ou=people,dc=unc,dc=test
objectClass: inetOrgPerson
uid: {name}
cn: {name}
sn: {name}
mail: {name}@unc.test
employeeType: student
EOF""")
    client_conf(name)


def prime_ocsp(name):
    """openssl's toy responder reloads its database on the request after a change.
    Send one throwaway query so later answers reflect the CA's current state."""
    for _ in range(2):
        sh(f"openssl ocsp -issuer {PKI}/ca.crt -cert {PKI}/{name}.crt -url http://127.0.0.1:8888 -CAfile {PKI}/ca.crt")
        time.sleep(1.1)


def graduate(name):
    """What should happen on graduation day: the CA revokes the device cert
    (CRL republished, OCSP database updated) and the directory marks the person alumni."""
    sh(f"{TB}/pki.sh revoke {name}")
    sh(f"{TB}/ldap.sh set {name} alumni")


MECHS = ["baseline", "crl", "ocsp", "directory"]


def selftest():
    ocsp = OCSPResponder()
    out = {}
    for m in MECHS:
        u = f"st_{m}_{int(time.time())}"
        new_user(u)
        if m == "ocsp":
            ocsp.restart()
        s = Server(m, crl_reload="2")
        before = login(u)[0]
        graduate(u)
        if m == "ocsp":
            ocsp.restart()
        time.sleep(3)
        after = login(u)[0]
        s.stop()
        out[m] = {"before_graduation": before, "after_graduation": after}
        print(m, out[m], flush=True)
    ocsp.stop()
    json.dump(out, open(os.path.join(RES, "selftest.json"), "w"), indent=1)


def latency(n=40):
    ocsp = OCSPResponder()
    new_user("lat_alice")
    ocsp.restart()
    rows = {}
    for m in MECHS:
        s = Server(m, crl_reload="3600")
        login("lat_alice")  # warm up
        ts = []
        for _ in range(n):
            ok, dt, _ = login("lat_alice")
            assert ok, m
            ts.append(dt)
        s.stop()
        rows[m] = {"median_ms": statistics.median(ts), "p10": sorted(ts)[n // 10],
                   "p90": sorted(ts)[(9 * n) // 10], "all": ts}
        print(m, round(rows[m]["median_ms"], 1), flush=True)
    ocsp.stop()
    json.dump(rows, open(os.path.join(RES, "latency.json"), "w"), indent=1)


def window(timeout=330, crl_reload=300, step=2.0):
    """Graduate a user at t=0 and retry their login every `step` seconds."""
    ocsp = OCSPResponder()
    path = os.path.join(RES, "window.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    only = os.environ.get("ONLY")
    plans = [("baseline", None), ("crl", None), ("ocsp", None), ("directory", None), ("shortlived", None)]
    for m, _ in plans:
        if only and m not in only.split(","):
            continue
        u = f"w_{m}_{int(time.time())}"
        validity = "+120" if m == "shortlived" else "1461"
        new_user(u, validity)
        prime_ocsp(u)
        s = Server("baseline" if m == "shortlived" else m, crl_reload=str(crl_reload))
        assert login(u)[0], f"{m}: fresh user should get on"
        # let the CRL reload clock run so graduation lands at a random point in the cycle
        time.sleep(7)
        graduate(u)
        if m == "ocsp":
            prime_ocsp(u)
        t0 = time.time()
        trace = []
        rejected_at = None
        while time.time() - t0 < timeout:
            ok, dt, _ = login(u)
            trace.append([round(time.time() - t0, 2), ok])
            if not ok:
                rejected_at = round(time.time() - t0, 2)
                break
            time.sleep(step)
        s.stop()
        res[m] = {"rejected_after_s": rejected_at, "trace": trace,
                  "cert_lifetime": validity}
        print(m, rejected_at, len(trace), flush=True)
        json.dump(res, open(path, "w"), indent=1)
    ocsp.stop()
    json.dump(res, open(os.path.join(RES, f"window.json"), "w"), indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "selftest":
        selftest()
    elif cmd == "latency":
        latency(int(sys.argv[2]) if len(sys.argv) > 2 else 40)
    elif cmd == "window":
        window(int(sys.argv[2]) if len(sys.argv) > 2 else 330)
