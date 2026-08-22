# Security

VeriGrant is an experimental GenLayer Intelligent Contract intended for testnet use and ecosystem contribution review.

## Status

- Tested locally with Python syntax checks.
- Designed from Bradbury-tested DisputeKit patterns.
- Not audited.

## Known Limitations

- Non-deterministic LLM review can time out on testnet. Retrying may be required.
- Public web evidence can change over time. Prefer stable URLs and immutable artifacts where possible.
- Review quality depends on clear milestone criteria and evidence schemas.
- Challenge bond size is fixed and may need adjustment for production.
- Each reviewed milestone has an on-chain one-hour challenge window. Up to two
  bonded challenge rounds are allowed, and finalization is rejected until the
  active window closes.
- `contract_balance()` can differ from internal accounting in Studio; use `accounted_balance()` for escrow-liability checks.
- The current exact-payout correction is deployed and tested at `0x6B7D4b407954629C34d628f31672f4129f1926D1`. The prior deployment at `0x6CD27E9823dE3B7293AeC9C848cF0e1C131D54c9` is historical only.

## Recommended Production Hardening

- Add role transfer or sponsor multisig support.
- Add optional third-party reviewer roles.
- Add stricter URI allowlists for high-value grants.
- Add event-like logging when GenLayer supports the desired indexing pattern.

## Reporting Issues

Open an issue with:

- method called;
- transaction hash;
- expected behavior;
- observed behavior;
- read state used in Studio;
- debug trace output, if available.
