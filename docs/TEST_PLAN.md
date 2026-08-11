# Bradbury Test Plan

Use this plan after deploying VeriGrant to GenLayer Bradbury Testnet.

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

