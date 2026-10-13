# Project plan: eduroam revocation SoK

This file is the single source of truth for the repo: goals, rules, how to run things and the work plan.

## 1. What this project is

COMP 790-194 (Applied Cryptography, UNC, Fall 2026) course project by Vinir Rai, solo.

**Title:** Graduated, Still Connected. SoK: credential revocation in federated Wi-Fi, with eduroam as the case study.

**Goal:** a Systematization of Knowledge (SoK) on how federated Wi-Fi (eduroam-style 802.1X/EAP) revokes access, backed by a testbed that measures each mechanism under identical conditions, ending in a list of open gaps.

**Motivation:** a friend graduated a year ago and his laptop still joins UNC eduroam. UNC device registrations last up to 4 years and the Onyen check happens at setup. The network checks that the credential is valid, not that the person still belongs.

**Research questions**
- RQ1 Systematize: what does each revocation tool prove, and to whom?
- RQ2 Measure: how long does a revoked device stay on, and what does each check cost per login?
- RQ3 Gaps: can a revocation check stay fresh without revealing who you are?

**Contributions the final paper must deliver**
1. A model: who holds, checks and learns what in federated Wi-Fi (laptop, access point, proxies, home RADIUS server, onboarding CA, directory).
2. A framework: the security properties revocation needs in this setting (`sok/framework.yaml`).
3. A systematization: ten mechanisms graded against the framework in one table (`sok/mechanisms.yaml`, `sok/table.csv`), with testbed numbers behind the claims.
4. The gaps, stated as open problems.

**This must stay a cryptography project.** The network is only the setting. Every mechanism is analyzed as a cryptographic object: what is signed or proved, by whom, how freshness is bounded, what a verifier learns. The directory lookup is the explicit non-crypto baseline.

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
  privacy_exp.py        relay that checks if the device cert name is visible under TLS 1.2 vs 1.3
results/early/          first results shown in the proposal (single trials, localhost)
sok/
  corpus.yaml           the 12 starting papers, venue, role, reading status
  framework.yaml        4 deployment constraints + 9 security properties with definitions
  mechanisms.yaml       10 mechanisms as cryptographic objects
  table.csv             mechanisms x properties grid to fill (the core SoK table)
docs/PLAN.md            this file
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

Run order: `./pki.sh init && ./ldap.sh start && python3 harness.py selftest`.

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

Milestones: framework Oct 14 to 26 · mechanisms Oct 27 to Nov 9 · measurements Nov 10 to 23 · writing and demo Nov 24 on.

### A. Make the testbed solid
- [ ] A1. Package: `testbed/setup.sh`, a `Makefile` or `run_all.sh`, pin versions in README, `.gitignore` generated dirs.
- [ ] A2. Refactor harness into a small module (`tb/` package): server lifecycle, PKI, directory, client, experiment runners. Keep current CLI working.
- [ ] A3. Repeatability: every experiment takes `--trials N --seed S`, writes one JSON per run with machine info, tool versions and config hash.

### B. Student direction (revoking a graduate)
- [ ] B1. Window, N >= 20 trials per mechanism, graduation at a random offset within the CRL reload cycle. Report median, min, max. Add CRL with a realistic publish + fetch cadence (cron-style fetch into ca_path, then reload).
- [ ] B2. Short-lived certificates at several lifetimes (1 h, 1 day, 7 days) analytically plus one short live run; also measure reissue cost (CA signatures per day per 10k devices).
- [ ] B3. Latency, n >= 200, plus simulated network delay to the OCSP responder and LDAP (a small TCP delay proxy in Python; `tc netem` may not be allowed in containers).
- [ ] B4. Password logins (PEAP-MSCHAPv2 and TTLS-PAP) with the directory check, to show revocation for password credentials is account-based, not cryptographic.
- [ ] B5. Pushed revocation sets: a small CRLite-style Bloom filter cascade built from the CA index; measure size and lookup time at 10k to 1M certificates. Cite Larisch et al. S&P 2017.

### C. Server direction (the crypto gap)
- [ ] C1. Rerun `server_exp.py` with N trials and with TLS 1.3 (hostapd `tls_flags=[ENABLE-TLSv1.3]`, client `tls_disable_tlsv1_3=0`).
- [ ] C2. **Staple replay window:** after revoking the server cert, keep serving an old "good" OCSP response that is still within nextUpdate. Measure how long an `ocsp=2` client accepts the revoked server. This is the freshness bound of stapling as a signed, timestamped statement.
- [ ] C3. Document which real supplicants support stapling (wpa_supplicant ocsp setting, plus vendor documentation for Windows, macOS/iOS, Android). Documentation only, no live testing.

### D. Privacy and anonymous revocation (RQ3)
- [ ] D1. Extend `privacy_exp.py`: outer identity (anonymous@ vs real), PEAP vs EAP-TLS, TLS 1.2 vs 1.3. Table of what each hop learns.
- [ ] D2. **Accumulator prototype** of a published construction, no new protocol: start with the RSA dynamic accumulator of Camenisch and Lysyanskaya (CRYPTO 2002): add, delete, witness update, and the zero-knowledge proof of knowledge of an accumulated value, in Python with gmpy2. Measure proof generation, verification, proof size and witness update cost vs number of revocations. If the ZK proof is too much, ship the accumulator plus witness updates and state the gap honestly. Optionally compare with Baldimtsi et al. (EuroS&P 2017).
- [ ] D3. Short write-up of verifier-local revocation (Boneh and Shacham, CCS 2004): verification cost grows with the revocation list. A back-of-envelope or small benchmark is enough.

### E. The SoK itself
- [ ] E1. Read each paper in `sok/corpus.yaml`; fill its `notes` and `claims` fields with page or section references.
- [ ] E2. Read Chuat et al. (EuroS&P 2020) closely and map their 19 criteria onto `sok/framework.yaml`; record which were kept, merged or dropped and why.
- [ ] E3. Fill `sok/table.csv`: each cell gets a value, the evidence source (paper section or results file) and a confidence level.
- [ ] E4. Write the gaps as open problems, each tied to empty or weak cells.
- [ ] E5. Draft the paper per `paper/outline.md`; generate figures from `results/` with a script, never by hand.

### F. Demo for the final talk
- [ ] F1. One command that shows: a graduate logs in, graduation happens, then each fix blocks the next login, with a live timer.
