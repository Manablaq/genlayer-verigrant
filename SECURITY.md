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
- The current implementation supports a challenge action but does not enforce a time-boxed challenge window.
- `contract_balance()` can differ from internal accounting in Studio; use `accounted_balance()` for escrow-liability checks.
- The historical Bradbury deployment does not contain the exact-payout consensus correction. Use a newly deployed instance of the current source.

## Recommended Production Hardening

- Add explicit challenge windows.
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
