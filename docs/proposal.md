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

## Feedback on the proposal presentation (graded Oct 13: 7/10, full marks on the five content items, 2/5 on delivery)
- Pick one focus. Too many directions were on the table.
- For an SoK, pick about four papers and read them in depth. Be able to say why each was chosen and how it fits this setting. Expect detailed questions about them at the final presentation.
- State the setting and threat model. Are all parties honest? Is it a correctness question or does it allow a malicious client? From Q&A: a client controls its own device and will not check itself, so revoking a user has to be enforced by the server.
- Explain the protocol: where CRL and OCSP are used, what is on them and who checks them. The login diagram was a good overview but needed more explanation.
- Response, Oct 22: the scope was narrowed to certificate revocation in eduroam's EAP-TLS login, with four core papers, a threat model and a protocol walkthrough (docs/PLAN.md section 1).

## Professor's guidance on structure (in person, Oct 23)
- Use eduroam, federated Wi-Fi at a university, as the lens.
- Start by explaining how it works now.
- Lay out the threat model and the security properties the setting needs: who the parties are, who is trusted and who is not, what each party can do.
- Compare the current protocol against that ideal.
- Read the papers through the same lens: if their ideas are applied to this setting, do they satisfy the properties? Many will work under different threat models or cover only pieces.
- Do not propose or build a new solution; it is too hard for the time left. Instead say where the literature falls short and what a new protocol would need.

## Open questions to settle
- Resolved Oct 22: anonymous revocation is out of scope, so there is no overlap with Muhammad's credential-scheme SoK.
- Final presentation date and demo format.
