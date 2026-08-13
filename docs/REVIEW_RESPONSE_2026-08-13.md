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

## Deployment requirement

The existing Bradbury deployment at
`0x6CD27E9823dE3B7293AeC9C848cF0e1C131D54c9` contains the rejected tolerance
logic and is historical evidence only. The corrected source must be deployed as
a new Bradbury instance, then tested with matching-source evidence before this
contribution is resubmitted.
