# Proposal summary (presented Oct 2026)

Slides: "Graduated, Still Connected". Rubric: background and motivation, objective, scope, methodology, deliverables (1 pt each) and delivery (5 pts).

## Story the proposal told
1. A friend graduated and still gets on eduroam. UNC registrations last up to 4 years; the Onyen check happens at setup.
2. Each school picks its own expiry: Charles Univ. (graduation day), UMB (next semester), Loughborough (1 yr), UNC (up to 4 yrs), Cracow UT (5 yrs). Georgia Tech went certificate-only Jan 2026.
3. One login crosses four networks; only the home server checks; the directory is asked only if configured.
4. Revocation works in two directions: revoking the student (easy, online verifier) and revoking the server (hard, offline verifier).
5. Goal: SoK on how federated Wi-Fi revokes access and where it falls short. Contributions: model, framework, systematization, gaps.
6. Scope in: the cryptography of revocation in both directions. Out: live networks, evil-twin theft (Hue et al.), network performance and link attacks, new protocols.
7. Method: build the framework from four deployment constraints, then test claims in one testbed. Four early results (see docs/PLAN.md section 5).

## Prof feedback to honor (from earlier sessions' Q&A)
- An SoK's contribution is identifying gaps, for example "no scheme has all three properties, or one does but is too slow".
- Fair comparison: run everything on the same system; apply or remove optimizations consistently.
- Spell out acronyms, say who holds which key, walk through the setting concretely, do not call a PRF or MAC "encryption", cite related attack work fully.

## Open questions to settle
- Does Muhammad's credential-scheme SoK overlap with the anonymous revocation part? Keep D2 narrow (revocation for roaming) if so.
- Final presentation date and demo format.
