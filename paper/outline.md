# SoK paper outline (8 to 10 pages)

1. Introduction: the graduate who stays connected; RQ1 to RQ3; contributions (model, framework, systematization, gaps).
2. Background: 802.1X, EAP-TLS and PEAP, RADIUS proxy chain, eduroam realm routing, onboarding CAs. Glossary in an appendix.
3. System and threat model: parties, what each holds, checks and learns (the model). Two revocation directions. Adversaries: departed user, holder of a leaked server key, curious proxy or responder.
4. Framework: constraints C1 to C4, properties P1 to P9, mapping from Chuat et al.
5. Systematization: the ten mechanisms as cryptographic objects; the main table (mechanisms x properties) with evidence.
6. Measurement: testbed design, fairness rules, results for windows, cost, server direction, staple replay, privacy, accumulator prototype.
7. Gaps and open problems: each tied to table cells.
8. Related work: eduroam security studies, PKI revocation, roaming authentication, anonymous credentials.
9. Ethics and limitations: localhost only, single machine, toy OCSP responder, no live supplicant testing.
10. Conclusion.
