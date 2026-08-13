# Bradbury Test Plan

Use this plan after deploying VeriGrant to GenLayer Bradbury Testnet.

The corrected Bradbury execution record is available in
[TEST_REPORT.md](TEST_REPORT.md). It includes the exact-payout correction and
both completed milestone paths on the deployed instance.

## Test 0: Exact Payout Equivalence

Purpose: prove validators cannot accept two review payloads that produce
different escrow transfers.

From the repository root, run:

```bash
python3 -m unittest tests/test_review_equivalence.py -v
```

Expected result: all tests pass. The suite verifies identical payout values are
equivalent, while a one-basis-point difference and the formerly permitted
500-basis-point difference are rejected.

## Test 1: Negative Milestone Review

Purpose: prove VeriGrant rejects placeholder or insufficient evidence.

1. Create a grant.
2. Add one milestone with `allocation_bps = 10000`.
3. Fund the grant.
4. Submit placeholder evidence:

```text
VeriGrant deployed at <YOUR_CONTRACT_ADDRESS> and has a test report.
```

5. Request milestone review.

Expected review:

```text
decision: incomplete
payout_bps: 0
```

6. Finalize the milestone.

Expected final state:

```text
milestone.status: finalized
grant.refunded: funded amount
grant.paid_out: 0
accounted_balance: 0
```

## Test 2: Positive Milestone Review

Purpose: prove valid evidence releases the milestone payout.

1. Create a new grant.
2. Add one milestone with `allocation_bps = 10000`.
3. Fund the grant.
4. Submit valid evidence:

```text
VeriGrant deployed at <ACTUAL_BRADBURY_CONTRACT_ADDRESS>.
The deployment transaction was accepted.
The public test report is available in the repository docs.
```

5. Request milestone review.

Expected review:

```text
decision: complete
payout_bps: 10000
```

6. Finalize the milestone.

Expected final state:

```text
milestone.status: finalized
grant.status: completed
grant.paid_out: funded amount
grant.refunded: 0
accounted_balance: 0
```

## Evidence To Record

For each transaction, record:

- transaction hash;
- `statusName`;
- `resultName`;
- `txExecutionResultName`;
- final `get_grant`;
- final `get_milestone`;
- final `get_review`;
- final `accounted_balance`.

## Debugging

If a transaction returns `FINISHED_WITH_ERROR`, use Bradbury's debug trace endpoint:

```text
gen_dbg_traceTransaction
```

If a non-deterministic review returns `LEADER_TIMEOUT`, retry the review call before changing contract code.

If a review returns `UNDETERMINED` / `DISAGREE`, trace the transaction before changing test inputs. During VeriGrant testing, one such case was traced to storage being captured inside nondeterministic execution. The final contract avoids this by snapshotting storage before `run_nondet_unsafe`.
