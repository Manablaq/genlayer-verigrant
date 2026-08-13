# Developer Guide

This guide explains how to deploy, configure, integrate, and test VeriGrant.

VeriGrant is a reusable GenLayer Intelligent Contract primitive for milestone-based grant escrow. It lets a sponsor define a grant, add milestone criteria, fund escrow, receive evidence, ask GenLayer validators to review the evidence, and finalize payout or refund.

## When To Use VeriGrant

Use VeriGrant when a workflow needs evidence-backed milestone review before funds are released:

- ecosystem grants;
- DAO funding rounds;
- public-goods sponsorships;
- hackathon milestone awards;
- AI-agent work orders;
- open-source maintenance contracts;
- research or audit deliverables.

Do not use VeriGrant as a simple storage contract. Its value comes from combining structured escrow accounting with GenLayer nondeterministic consensus over ambiguous public evidence.

## Corrected Contract Address

Corrected Bradbury deployment:

```text
0x6B7D4b407954629C34d628f31672f4129f1926D1
```

Deployment transaction:

```text
0x4ea22133cea28cfa94fcb9be6ffc34c99d9030ebc3b6bfda65a0947d367fadbf
```

Source:

```text
contracts/veri_grant.py
```

The deployed source byte-for-byte matches the contract source at commit
`4e43896`. Before deploying a new instance, run the exact-payout regression
suite:

```bash
python3 -m unittest tests/test_review_equivalence.py -v
```

The source requires exact equality for `payout_bps` because that field is used
to calculate the escrow transfer in `finalize_milestone`. The complete review
response and verified Bradbury execution are recorded in
[REVIEW_RESPONSE_2026-08-13.md](REVIEW_RESPONSE_2026-08-13.md).

## Core Concepts

### Grant

A grant stores the sponsor, grantee, title, grant specification, review policy, escrowed amount, paid amount, refunded amount, and milestone count.

### Milestone

A milestone stores its criteria, evidence schema, allocation in basis points, optional deadline, evidence count, review result, and final accounting.

`allocation_bps` is measured against the whole grant. A single-milestone grant normally uses `10000`.

### Evidence

Evidence can be one of:

```text
text
url
api
image_url
attestation
```

Text evidence is stored directly. URL/API/image evidence can be fetched or rendered during nondeterministic review, subject to contract bounds.

### Review

A review stores:

```text
decision
completion_bps
payout_bps
confidence_bps
reason_codes
evidence_used
summary
decided_at
challenger
```

Valid decisions are:

```text
complete
incomplete
partial
needs_more_evidence
```

## Standard Flow

1. Deploy `contracts/veri_grant.py` in GenLayer Studio.
2. Confirm `get_grant_count()` returns `0`.
3. Confirm `accounted_balance()` returns `0`.
4. Call `create_grant`.
5. Call `add_milestone`.
6. Call payable `fund_grant`.
7. Call `submit_milestone_evidence`.
8. Call `request_milestone_review`.
9. Read `get_review`.
10. Call `finalize_milestone`.
11. Confirm `accounted_balance()` returns `0` after all milestones are closed.

## Studio Usage Example

### Create Grant

```text
create_grant

grantee:
0x5bB49021001200fE8156a81c7fcF097e535e7181

title:
Bradbury Positive Grant Test

grant_spec:
Grantee must provide valid VeriGrant deployment evidence on GenLayer Bradbury, including the deployed contract address, accepted deployment transaction, and repository test documentation.

review_policy:
Release the milestone when evidence includes the actual deployed VeriGrant contract address, explicitly states that the deployment transaction was accepted, and references public test documentation.
```

Expected:

```text
FINISHED_WITH_RETURN
```

### Add Milestone

```text
add_milestone

grant_id:
0

title:
Valid Deployment Evidence Test

criteria:
Evidence must include the actual deployed VeriGrant Bradbury contract address, explicitly state that the deployment transaction was accepted, and reference public test documentation.

evidence_schema:
Submit one text evidence item with the contract address, accepted deployment transaction, and public test documentation reference.

allocation_bps:
10000

deadline_ts:
0
```

Expected:

```text
get_milestone(0, 0).status: open
get_milestone(0, 0).allocation_bps: 10000
```

### Fund Grant

```text
fund_grant

grant_id:
0

Value:
1
```

In GenLayer Studio, `Value: 1` was observed as:

```text
1000000000000000000
```

Expected:

```text
get_grant(0).escrowed: 1000000000000000000
accounted_balance: 1000000000000000000
```

### Submit Evidence

```text
submit_milestone_evidence

grant_id:
0

milestone_id:
0

evidence_type:
text

uri:

description:
VeriGrant deployed at 0x6B7D4b407954629C34d628f31672f4129f1926D1. The deployment transaction 0x4ea22133cea28cfa94fcb9be6ffc34c99d9030ebc3b6bfda65a0947d367fadbf was accepted. Public test documentation is recorded in the repository test report.
```

Expected:

```text
get_milestone(0, 0).status: evidence_submitted
get_evidence(0, 0, 0).evidence_type: text
```

### Request Review

```text
request_milestone_review

grant_id:
0

milestone_id:
0
```

Expected for valid evidence:

```text
get_review(0, 0).decided: true
get_review(0, 0).decision: complete
get_review(0, 0).payout_bps: 10000
```

### Finalize

```text
finalize_milestone

grant_id:
0

milestone_id:
0
```

Expected for a complete review:

```text
get_grant(0).status: completed
get_grant(0).paid_out: 1000000000000000000
accounted_balance: 0
```

Expected for an incomplete review:

```text
get_grant(0).status: completed
get_grant(0).refunded: 1000000000000000000
accounted_balance: 0
```

## Public API Reference

### Write Methods

| Method | Payable | Purpose |
| --- | --- | --- |
| `create_grant(grantee, title, grant_spec, review_policy)` | No | Create a grant record. |
| `add_milestone(grant_id, title, criteria, evidence_schema, allocation_bps, deadline_ts)` | No | Add a milestone to a draft or active grant. |
| `fund_grant(grant_id)` | Yes | Deposit escrow for a grant. |
| `submit_milestone_evidence(grant_id, milestone_id, evidence_type, uri, description)` | No | Submit milestone evidence. |
| `request_milestone_review(grant_id, milestone_id)` | No | Run GenLayer evidence review. |
| `challenge_milestone_review(grant_id, milestone_id, evidence_type, uri, description)` | Yes | Add bonded counter-evidence and rerun review. |
| `finalize_milestone(grant_id, milestone_id)` | No | Apply payout and refund after review. |
| `cancel_unfunded_grant(grant_id)` | No | Cancel a grant that has no escrow activity. |
| `expire_milestone(grant_id, milestone_id)` | No | Refund an unsubmitted milestone after deadline. |

### Read Methods

| Method | Purpose |
| --- | --- |
| `get_grant_count()` | Return total grant count. |
| `get_grant(grant_id)` | Return grant metadata and accounting. |
| `get_milestone(grant_id, milestone_id)` | Return milestone metadata, status, and accounting. |
| `get_evidence(grant_id, milestone_id, evidence_index)` | Return one evidence item. |
| `get_review(grant_id, milestone_id)` | Return milestone review result. |
| `contract_balance()` | Return raw contract balance. |
| `accounted_balance()` | Return internal escrow liability. |

## Integration Guidance

Frontends and scripts should treat these as the key state transitions:

```text
draft -> active -> completed
open -> evidence_submitted -> reviewed -> finalized
```

Recommended UI checks:

- do not show review actions until `evidence_count > 0`;
- do not show finalize until `get_review(...).decided == true`;
- use `accounted_balance()` for contract liability, not raw `contract_balance()`;
- show `reason_codes` and `summary` in reviewer/audit views;
- treat `LEADER_TIMEOUT` as retryable on Bradbury;
- trace `UNDETERMINED` or `FINISHED_WITH_ERROR` before changing test inputs.

## Nondeterministic Review Boundary

The final contract snapshots storage before calling `run_nondet_unsafe`.

This is important. During Bradbury testing, a pre-fix transaction produced the correct review payload but returned `UNDETERMINED` / `DISAGREE`. `gen_dbg_traceTransaction` showed:

```text
Reading storage in nondet mode is not supported
```

The final implementation avoids storage capture inside nondeterministic leader and validator closures by using module-level helper functions over plain snapshot data.

## Bradbury Test Proof

The final deployment passed:

- negative path: placeholder evidence rejected, full refund, `accounted_balance() == 0`;
- positive path: valid evidence accepted, full payout, `accounted_balance() == 0`.

See:

```text
docs/TEST_REPORT.md
```
