# Usage Guide

This guide describes how to test VeriGrant in GenLayer Studio.

## Deploy

1. Open GenLayer Studio.
2. Select Bradbury Testnet.
3. Paste or upload `contracts/veri_grant.py`.
4. Deploy.
5. Confirm deployment returns `FINISHED_WITH_RETURN`.

## Initial Reads

Call:

```text
get_grant_count()
```

Expected:

```text
0
```

Call:

```text
accounted_balance()
```

Expected:

```text
0
```

## Create Grant

Call `create_grant`:

```text
grantee:
0x5bB49021001200fE8156a81c7fcF097e535e7181

title:
Bradbury Grant Verification Test

grant_spec:
Grantee must deliver a public GenLayer artifact with documentation, a deployed Bradbury contract address, and a test report.

review_policy:
Release milestone funds only when submitted evidence materially satisfies the milestone criteria. Reject placeholder evidence.
```

Expected:

```text
FINISHED_WITH_RETURN
get_grant_count: 1
```

## Add Milestone

Call `add_milestone`:

```text
grant_id:
0

title:
Deployment and Test Report

criteria:
Evidence must include a deployed Bradbury contract address, state that deployment was accepted, and mention a public test report.

evidence_schema:
Submit one text evidence item with the contract address and test report reference.

allocation_bps:
10000

deadline_ts:
0
```

Expected:

```text
get_milestone(0, 0).status: open
allocation_bps: 10000
```

## Fund Grant

Call `fund_grant`:

```text
grant_id:
0

Value:
1
```

In Studio, `Value: 1` was observed to map to `1000000000000000000` base units.

Expected:

```text
get_grant(0).escrowed: 1000000000000000000
accounted_balance: 1000000000000000000
```

## Submit Evidence

Call `submit_milestone_evidence`:

```text
grant_id:
0

milestone_id:
0

evidence_type:
text

uri:

description:
VeriGrant deployed at <YOUR_CONTRACT_ADDRESS>. The deployment transaction was accepted. The public test report is available in the repository docs.
```

Expected:

```text
get_milestone(0, 0).status: evidence_submitted
get_evidence(0, 0, 0).evidence_type: text
```

## Request Review

Call:

```text
request_milestone_review
grant_id: 0
milestone_id: 0
```

This is the non-deterministic AI/validator step. It can take longer than ordinary writes.

Expected for valid evidence:

```text
get_review(0, 0).decision: complete
get_review(0, 0).payout_bps: 10000
```

If Bradbury returns `LEADER_TIMEOUT`, retry the review call. This is a testnet consensus timeout, not necessarily a contract error.

## Finalize

Call:

```text
finalize_milestone
grant_id: 0
milestone_id: 0
```

Expected:

```text
get_milestone(0, 0).status: finalized
get_grant(0).status: completed
get_grant(0).paid_out: 1000000000000000000
accounted_balance: 0
```

