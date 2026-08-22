# Reviewer Response: Enforceable Challenge Window

## Finding

The prior contract allowed any caller to finalize a reviewed milestone
immediately. That made the challenge method optional in practice: neither the
sponsor nor grantee was guaranteed time to submit counter-evidence.

## Correction

Every review now records `reviewed_at` and an on-chain
`challenge_deadline_ts` one hour in the future. `finalize_milestone` rejects
all callers while that deadline is open. Either sponsor or grantee can submit a
bonded challenge during the window; the challenge triggers a fresh consensus
review and resets the deadline. Up to two challenge rounds are allowed per
milestone.

Challenge bonds are stored separately from grant escrow, so they cannot change
the amount used to calculate milestone payouts. Every bond is indexed by grant,
milestone, and challenger, included in `accounted_balance()`, and refunded
exactly once when finalization occurs.

## Additional Hardening

- Milestones cannot be added after funding, preventing allocation changes after
  escrow is committed.
- Funding is rejected after any milestone has progressed beyond evidence
  submission, preventing reviewed state from being re-based on new funds.
- CLI address and empty optional evidence arguments are normalized consistently.
- Web/API/image evidence requires HTTPS and every evidence item must contain a
  URI or description.
- Exact `payout_bps` validator equivalence remains enforced.

## Verification

The local suite covers exact payout equivalence and the challenge-window
boundary. The fresh Bradbury deployment, immediate-finalization rejection,
challenge/re-review reset, post-deadline finalization, bond refund, and Explorer
source match will be recorded in `docs/TEST_REPORT.md` after deployment.
