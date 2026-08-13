# VeriGrant payout-consensus correction

## Reviewer finding

The prior VeriGrant deployment allowed `payout_bps` values within 500 basis
points of the leader value during validator equivalence. That was unsafe because
`finalize_milestone` uses the exact stored `payout_bps` to calculate the escrow
transfer. A validator could therefore accept a materially different transfer.

## Correction

`_reviews_equivalent_payload` now requires exact equality for `payout_bps`.
The contract still permits bounded differences in non-transfer narrative metrics,
but it rejects any disagreement, including one basis point, in the amount that
can be paid from escrow. `decision` remains exact as before.

The review prompt was also strengthened: a `complete` decision must request the
full milestone allocation, while `incomplete` and `needs_more_evidence` must
request zero. Partial reviews remain supported, but leader and validator must
select the identical payout basis-point value.

## Regression evidence

`tests/test_review_equivalence.py` executes the real normalization and
equivalence helpers and proves that:

- identical payout values are accepted;
- a one-basis-point difference is rejected;
- the formerly permitted 500-basis-point difference is rejected.

Run it with:

```bash
python3 -m unittest tests/test_review_equivalence.py -v
```

## Deployment and Bradbury verification

The prior Bradbury deployment at
`0x6CD27E9823dE3B7293AeC9C848cF0e1C131D54c9` contains the rejected tolerance
logic and is historical evidence only.

The corrected source was deployed to Bradbury at
`0x6B7D4b407954629C34d628f31672f4129f1926D1` in deployment transaction
`0x4ea22133cea28cfa94fcb9be6ffc34c99d9030ebc3b6bfda65a0947d367fadbf`.
The deployment was accepted, agreed, and finished with return. Its embedded
source byte-for-byte matches `contracts/veri_grant.py` at commit `4e43896`.

The new contract completed both required paths:

- placeholder evidence was reviewed as `incomplete` with `payout_bps: 0`, then
  refunded in full;
- valid evidence was reviewed as `complete` with `payout_bps: 10000`, then paid
  in full;
- `accounted_balance()` returned `0` after each finalization.

The complete transaction record is in [TEST_REPORT.md](TEST_REPORT.md).
