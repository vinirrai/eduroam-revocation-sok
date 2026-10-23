# SoK paper outline (8 to 10 pages)

The structure follows the professor's guidance (Oct 23): describe the setting, define the security it needs, check the current protocol against that, read each paper's ideas through the same lens and end with what is still missing.

1. Introduction: the graduate who stays connected; the setting (eduroam, federated Wi-Fi at a university); RQ1 to RQ3; contributions.
2. The setting today: how eduroam works now. Onboarding, the EAP-TLS login across the proxy chain and where CRL, OCSP, stapling and the directory check would run and who runs them. One diagram.
3. Parties and threat model: who the parties are, what each holds and can do, who is trusted and who is not. Direction 1: device certificate, verified by the home server (honest graduate = correctness, malicious graduate = security). Direction 2: server certificate, verified by the laptop while offline.
4. Security properties: the ideal for this setting, derived from the threat model and checked against Chuat et al.'s criteria for completeness.
5. The current protocol against the ideal: what EAP-TLS with typical configuration gives for each property, backed by testbed numbers (revocation windows, per-login cost, stapling behavior, staple replay window).
6. The literature through this lens: apply each core paper's idea to the setting (Hue et al., Goldberg et al., the schemes in Chuat et al., CRLite) and ask whether it satisfies each property, under which threat model and where it falls short. The main table: ideas x properties, per direction, with evidence.
7. What is needed: where the literature falls short, stated as open problems and as requirements a future protocol would have to meet. No new protocol is designed or built here.
8. Ethics and limitations: localhost only, single machine, toy OCSP responder, no live supplicant testing, test devices only.
9. Conclusion.
