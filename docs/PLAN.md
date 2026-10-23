# Project plan: eduroam revocation SoK

This file is the single source of truth for the repo: goals, rules, how to run things and the work plan.

## 1. What this project is

COMP 790-194 (Applied Cryptography, UNC, Fall 2026) course project by Vinir Rai, solo.

**Title:** Graduated, Still Connected. SoK: certificate revocation in eduroam's EAP-TLS login.

**Scope change (Oct 22, after the proposal feedback).** The professor asked for one clear focus, about four papers read in depth, an explicit threat model and a walkthrough of where revocation checks happen. The project is now narrowed to certificate revocation in EAP-TLS as eduroam uses it. Out: privacy and anonymous credentials (old RQ3 and work items D1 to D3), the 5G and DNS comparison papers and the 12-paper corpus. The feedback is in `docs/proposal.md`.

**Focus.** One EAP-TLS login checks two certificates, so revocation has two verifiers:
- the student's device certificate, checked by the home RADIUS server, which is online at login time;
- the home server's certificate, checked by the laptop, which is offline until the login finishes.

The question: once a certificate is revoked, how long can it still be used to complete a login, and what does each mechanism (CRL, OCSP, OCSP stapling, short-lived certificates, pushed revocation lists) actually guarantee to each verifier?

**Approach (professor's guidance, Oct 23).** Use the setting as the lens and analyze papers through it, rather than surveying the literature directly:
1. Explain how eduroam works today (protocol walkthrough below).
2. Define the threat model: the parties, who is trusted and who is not, what each party can do.
3. Derive the security properties the setting needs: the ideal.
4. Check the current protocol against that ideal, with testbed numbers as evidence.
5. Apply each core paper's idea to the setting and ask whether it satisfies the properties, under which threat model and where it falls short.
6. End with what is needed: where the literature falls short and what a future protocol would have to meet. No new protocol is designed or built; the professor said that is not worth it in the time left.

**Motivation:** a friend graduated a year ago and his laptop still joins UNC eduroam. UNC device registrations last up to 4 years and the Onyen check happens at setup. The network checks that the credential is valid, not that the person still belongs.

**Research questions**
- RQ1 Systematize: what does each revocation mechanism prove, to which verifier and under which threat model?
- RQ2 Measure: how long does a revoked certificate keep working on each side, and what does each check cost per login?
- RQ3 Gaps: for which verifier and threat model does no mechanism work today?

**Contributions the final paper must deliver**
1. A model of the login: who holds, checks and relays what (laptop, access point, visited RADIUS server, eduroam proxies, home RADIUS server, onboarding CA, directory), with the walkthrough below.
2. A framework: the properties revocation needs in this setting (`sok/framework.yaml`), derived from the setting and threat model and checked against Chuat et al.
3. A systematization: the current protocol and each paper's idea applied to this setting, graded per verifier (`sok/mechanisms.yaml`, `sok/table.csv`), with testbed numbers behind the claims.
4. The gaps: where the literature falls short and what a future protocol would need, stated as open problems.

**This must stay a cryptography project.** The network is only the setting. Every mechanism is analyzed as a cryptographic object: what is signed, by whom, how freshness is bounded and who verifies it. The directory lookup is the explicit non-crypto baseline.

### Protocol walkthrough (the paper and the final talk must explain this)

1. **Setup, once.** The student signs in with their Onyen on the onboarding portal. The onboarding CA signs a device certificate for the laptop. The profile also installs the CA that the home server's certificate chains to and the expected server name.
2. **Each login.** Laptop to visited access point to visited RADIUS server to eduroam proxies to home RADIUS server, routed by the realm (@unc.edu). Inside EAP the laptop and the home server run TLS. The laptop checks the server certificate against the installed CA and name. The home server checks the device certificate's chain and validity period, and the laptop proves it holds the device key by signing the handshake.
3. **Revocation checks.** All optional and set by configuration.
   - CRL: a list of revoked serial numbers signed by the CA, with thisUpdate and nextUpdate. The home server loads the onboarding CA's CRL to check device certificates. It is only as fresh as the last reload.
   - OCSP: the CA's signed good or revoked answer about one certificate, with a validity window and an optional nonce. The home server can ask at every login. The laptop cannot ask anything during login.
   - OCSP stapling: the home server attaches a recent OCSP response about its own certificate to the handshake and the laptop verifies it. wpa_supplicant `ocsp=0/1/2` means ignore, check if present, require.
   - Short-lived certificates: expiry acts as revocation.
   - Directory lookup: the home server asks whether the user is still enrolled. Nothing is signed.
4. **The answer.** The home server returns Access-Accept or Access-Reject through the proxies, and the access point admits the laptop or not.

Password logins (PEAP, TTLS) are out of scope. There revocation means disabling the account, which is not a cryptographic mechanism; the paper gives them one paragraph.

### Threat model

**Trusted.** The onboarding CA, its CRL and OCSP responder and the directory (they define who is valid). The home server is honest; which checks it runs is the configuration variable under study. The visited network and the eduroam proxies relay messages faithfully and do not change the home server's answer; Goldberg et al. (USENIX Security 2024) is the reference for when that assumption holds. Attacks on the Wi-Fi link, on the RADIUS transport and on implementations are out of scope.

**Direction 1: device certificate (verifier: home server, online).**
- Honest graduate, a correctness question: the laptop keeps connecting after graduation. Does the system enforce its own policy, and how long after revocation?
- Malicious graduate, a security question: the graduate controls the device, keeps the certificate and key, skips any local check and retries at will. Checks on the laptop give nothing here; only checks run by the home server count. Property: no Access-Accept later than a bound after revocation, whatever the client does.

**Direction 2: server certificate (verifier: laptop, offline during login).**
- The laptop is honest, since the check protects its own user. The adversary holds a copy of a home server key whose certificate the CA has revoked. Property: an honest laptop refuses that certificate no later than a bound after revocation. The laptop cannot reach a CRL or OCSP responder during login, so only what arrives in the handshake (stapling) or what it received earlier (a pushed list, a short lifetime) can help.

**Rule that falls out of this:** a check only protects the party that runs it.

### Paper set (sent to the professor Oct 22)

Core papers, read in full, notes in `sok/corpus.yaml`:
1. Hue et al., "All your Credentials are Belong to Us: On Insecure WPA2-Enterprise Configurations", ACM CCS 2021. The closest paper to this setting: server certificate validation on WPA2-Enterprise devices, in institutions' setup guides, in eduroam CAT profiles and on eduroam servers. It does not cover revocation; this project starts where it stops.
2. Goldberg et al., "RADIUS/UDP Considered Harmful", USENIX Security 2024. RADIUS carries every eduroam login and the home server's answer. Used to state when the relay assumption in the threat model holds.
3. Chuat et al., "SoK: Delegation and Revocation, the Missing Links in the Web's Chain of Trust", IEEE EuroS&P 2020. The evaluation criteria, adapted to eduroam's two verifiers.
4. Larisch et al., "CRLite: A Scalable System for Pushing All TLS Revocations to All Browsers", IEEE S&P 2017. The main design for a verifier that cannot go online when it checks. It builds its filter from publicly logged certificates, so part of the analysis is whether it carries over when the server certificate comes from a private CA.

Background only (cite, do not survey): RFC 7593 (eduroam), RFC 5216 and RFC 9190 (EAP-TLS), RFC 5280 (certificates and CRLs), RFC 6960 (OCSP), RFC 6066 (TLS status_request), Smith et al. NDSS 2020 (Let's Revoke), Appana and Vanhoef, WiSec 2026 (trust on first use for enterprise Wi-Fi; it states that it does not support CRL or OCSP) and Jisc guidance on eduroam server certificates. WiSec is not on the course venue list, so it can only be background.

## 2. Hard rules

- **Ethics:** never touch a real network. No probing UNC's or any live eduroam/RADIUS/OCSP service. Everything runs on localhost in this repo's testbed. Policy data only from public documentation. Anything UNC-specific gets reported to UNC ITS Security before it goes in a slide or the paper.
- **No new protocols.** The course requires full formal proofs for any new or modified protocol. Prototypes must implement published constructions faithfully (cite the paper and section) and only measure them.
- **Venues:** surveyed papers must come from IEEE S&P, ACM CCS, USENIX Security, NDSS, PETS, IEEE EuroS&P, IACR Crypto, Eurocrypt, Asiacrypt, TCC or PKC. Anything else (RFCs, measurement workshops, journals) is background only and must be labeled that way. Verify venue and year before adding to `sok/corpus.yaml`.
- **Fair comparison:** all mechanisms run on the same machine, same FreeRADIUS build, same key types and sizes, one variable changed at a time. Report medians plus spread, number of trials and the machine.
- **Never fabricate numbers.** If an experiment was not run, the table cell says "not measured". Keep raw JSON for every number in `results/`.
- **Writing style for anything Vinir will present or submit:** no em dashes, no Oxford commas, no generic AI-sounding phrasing. First person, plain sentences.

## 3. Repo layout

```
README.md               short public description
testbed/                runnable experiments (see section 5)
  setup.sh              apt packages for Ubuntu 24.04
  pki.sh                test CA: init, issue, issue-server, revoke, crl (PKI_DIR env overrides ./pki)
  ldap.sh               stand-in Onyen directory (slapd on 127.0.0.1:3890)
  gen.py                generates a FreeRADIUS config dir per mechanism
  harness.py            selftest | latency N | window T  (student-direction experiments)
  server_exp.py         server-direction experiment (hostapd + OCSP stapling vs eapol_test ocsp=0/1/2)
  privacy_exp.py        relay that checks if the device cert name is visible under TLS 1.2 vs 1.3 (side note only)
results/early/          first results shown in the proposal (single trials, localhost)
sok/
  corpus.yaml           the 4 core papers plus background sources, venue, role, reading status
  framework.yaml        deployment constraints + security properties with definitions
  mechanisms.yaml       the mechanisms in scope (M0 to M5) as cryptographic objects
  table.csv             mechanisms x properties grid to fill (the core SoK table)
docs/PLAN.md            this file
docs/setting.md         protocol walkthrough and threat model (task E0)
docs/proposal.md        what was proposed, prof feedback to honor, open questions
paper/outline.md        SoK paper outline (8 to 10 pages)
```

Generated at runtime and gitignored: `testbed/pki*/`, `testbed/ldap/`, `testbed/rad_*/`, `testbed/srv/`, `testbed/clients/`, `testbed/results/`.

## 4. Environment

Ubuntu 24.04, run as root (FreeRADIUS and slapd are started with root and local paths). `testbed/setup.sh` installs:
`freeradius freeradius-ldap eapoltest hostapd slapd ldap-utils openssl tcpdump python3`.
Versions used so far: FreeRADIUS 3.2.5, wpa_supplicant/eapol_test 2.10, hostapd 2.10, OpenSSL 3.0.13.

Ports: FreeRADIUS auth 18120, hostapd RADIUS 18130, privacy relay 18131, OCSP responder 8888, LDAP 3890.

## 5. What already works (and gotchas learned the hard way)

Run order: `./pki.sh init && ./ldap.sh start && python3 harness.py selftest`. On macOS (or anywhere with Docker) use `./run_all.sh selftest` from the repo root, which runs the same steps in an Ubuntu 24.04 container.

- **Mechanisms in `gen.py`:** `baseline` (default FreeRADIUS EAP-TLS, no revocation checks), `crl` (check_crl + ca_path_reload_interval), `ocsp` (FreeRADIUS ocsp block against `openssl ocsp`), `directory` (check-eap-tls virtual server queries LDAP for employeeType of the cert CN), `all`. Short-lived certs use `baseline` with a cert issued via `pki.sh issue name +SECONDS`.
- **"Graduation"** = `pki.sh revoke <name>` (CA index + CRL republished) and `ldap.sh set <name> alumni`.
- FreeRADIUS **refuses `ca_path_reload_interval` below 300 s** and resets it to 300. Default is 0 = CRLs only reload on restart. This is itself a finding.
- The check-eap-tls virtual server must set `&control:Auth-Type := Accept` after the check or every login fails.
- `gen.py` sets `reject_delay = 0` so reject timing is not padded by 1 s.
- `openssl ocsp` (the toy responder) reloads its index **one request late**. `harness.prime_ocsp()` sends a throwaway query after each CA change. A production responder would not need this. Do not hide this in results.
- FreeRADIUS 3.2.5 as configured never sends OCSP stapled responses, so an `ocsp=2` client cannot log in to it. hostapd's internal RADIUS server can staple via `ocsp_stapling_response`.
- In a shell, never `pkill -f "<pattern>"` where the pattern also appears in your own command line; it kills the shell. Use `pkill -x freeradius` or saved PIDs.
- `harness.window()` merges into `results/window.json`; use env `ONLY=ocsp,directory` to rerun a subset.

**Early results (single trials, localhost; see results/early):**
- Window after graduation: baseline never cut off in 330 s (cert valid to 2030); CRL 293 s (min reload 300 s); 2-minute cert 109 s; OCSP and directory on first retry.
- Median full login, n=40: baseline 16.6 ms, CRL 16.9, directory 19.0, OCSP 20.8.
- Server direction: ocsp=0 connects to a revoked server always; ocsp=1 blocks only if the server staples; ocsp=2 safe but locks out non-stapling servers.
- Privacy: device-cert name visible to relays in EAP payloads under TLS 1.2, hidden under TLS 1.3.

## 6. Work plan (in order). Check items off here as you go.

Milestones (revised Oct 22): setting and framework Oct 22 to Nov 1 · measurements Nov 2 to 15 · table and gaps Nov 16 to 29 · paper, slides and demo Nov 30 on.

### A. Testbed
- [x] A1. Package: `testbed/setup.sh`, a `Makefile` or `run_all.sh`, pin versions in README, `.gitignore` generated dirs. Done Oct 13: `Dockerfile` + `run_all.sh` (Ubuntu 24.04 container, works on macOS); selftest, server and privacy reproduce the early results on arm64.
- A2. Dropped Oct 22: the refactor is not needed for the narrowed scope.
- [ ] A3. Repeatability: every experiment takes `--trials N --seed S`, writes one JSON per run with machine info, tool versions and config hash.

### B. Direction 1: device certificate, verified by the home server
- [ ] B1. Window, N >= 20 trials per mechanism, graduation at a random offset within the CRL reload cycle. Report median, min, max. Add CRL with a realistic publish + fetch cadence (cron-style fetch into ca_path, then reload).
- [ ] B2. Short-lived certificates at several lifetimes (1 h, 1 day, 7 days) analytically plus one short live run; also measure reissue cost (CA signatures per day per 10k devices).
- [ ] B3. Latency, n >= 200, plus simulated network delay to the OCSP responder and LDAP (a small TCP delay proxy in Python; `tc netem` may not be allowed in containers).
- [ ] B4. Password logins (PEAP, TTLS): no experiment. One paragraph in the paper on why their revocation is account-based, not cryptographic.

### C. Direction 2: server certificate, verified by the laptop
- [ ] C1. Rerun `server_exp.py` with N trials and with TLS 1.3 (hostapd `tls_flags=[ENABLE-TLSv1.3]`, client `tls_disable_tlsv1_3=0`).
- [ ] C2. **Staple replay window:** after revoking the server cert, keep serving an old "good" OCSP response that is still within nextUpdate. Measure how long an `ocsp=2` client accepts the revoked server. This is the freshness bound of stapling as a signed, timestamped statement.
- [ ] C3. Document which real supplicants support stapling (wpa_supplicant ocsp setting, plus vendor documentation for Windows, macOS/iOS, Android). Documentation only, no live testing.
- [ ] C4. Pushed revocation list for the laptop (was B5): a small CRLite-style filter cascade (Larisch et al., S&P 2017) built from the CA index, next to a plain signed list, since one institution has only a few server certificates. Measure size and lookup time, and write down how the list would reach the laptop before login.

### D. Dropped Oct 22
Privacy measurements (old D1), the accumulator prototype (old D2) and verifier-local revocation (old D3) are out of scope. `privacy_exp.py` and its early result stay in the repo as a side note only.

### E. The SoK itself
- [ ] E0. Write `docs/setting.md`: the protocol walkthrough and threat model from section 1, plus one diagram showing where each check runs. This becomes paper sections 2 and 3 and two slides in the final talk.
- [ ] E1. Update `sok/corpus.yaml` to the four core papers plus the background list in section 1. Fill `notes` and `claims` for each core paper with section references as Vinir reads it.
- [ ] E2. Derive the properties from the setting and threat model first, then check them against Chuat et al.'s criteria in `sok/framework.yaml`; record what was kept, merged or dropped and why. Mark the privacy-only items (constraint C4, properties P7 and P8) out of scope. Grade the failure-mode property against each direction's adversary: can that adversary force a soft fail?
- [ ] E3. Trim `sok/mechanisms.yaml` and `sok/table.csv` to M0 to M5, with rows for each verifier. Each cell gets a value, the evidence source (paper section or results file) and a confidence level.
- [ ] E4. Write the gaps as open problems, each tied to empty or weak cells.
- [ ] E5. Draft the paper per `paper/outline.md` (restructured Oct 23); generate figures from `results/` with a script, never by hand.

### F. Final talk
- [ ] F1. Demo: one command that shows a test graduate log in, get revoked and then get blocked by each fix, with a live timer. Test certificates and devices only, never a real person's laptop or credentials.
- [ ] F2. Slides: protocol walkthrough and threat model before any results, plus one slide on the four papers and why each is there.
