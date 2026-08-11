# Bradbury Test Report

This report records the final VeriGrant deployment and execution evidence from GenLayer Bradbury Testnet.

## Final Deployment

Contract:

```text
0x6CD27E9823dE3B7293AeC9C848cF0e1C131D54c9
```

Deployment transaction:

```text
0xb6218d6006b1c0787b5bd18155445c7b958ae945e537d9d92dc03f81f1250362
```

Deployment result:

```text
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

The deployed source includes the final nondeterministic review fix: module-level review, normalization, and equivalence helpers that operate on plain milestone snapshots.

## Pre-Fix Trace Finding

An earlier deployment produced the correct negative review payload but the transaction ended as:

```text
statusName: UNDETERMINED
resultName: DISAGREE
```

Bradbury debug trace showed the real cause:

```text
Reading storage in nondet mode is not supported
```

The final deployed contract avoids this by building a deterministic snapshot before `run_nondet_unsafe` and avoiding contract-storage captures inside leader and validator closures.

## Negative Path: Placeholder Evidence Rejected

Grant:

```text
grant_id: 0
title: Bradbury Negative Grant Test
```

Milestone:

```text
milestone_id: 0
title: Placeholder Rejection Test
allocation_bps: 10000
deadline_ts: 0
```

Funding transaction:

```text
0x4d4fb67e078c064cd1434bf1eb238f94e869718b403ee204b4bf2001fc8a113d
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Evidence transaction:

```text
0xb99ad395b5776d39af06515ee84a6941bd833c0e2b94075c28cab78121f4c826
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Evidence:

```text
VeriGrant deployed at YOUR_CONTRACT_ADDRESS and the deployment was successful.
```

Review transaction:

```text
0x2c20abe6b181653c881a351db30a3e1a86aaf0730fcf63c555bdb047ab62cc72
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Review result:

```text
decided: true
decision: incomplete
completion_bps: 0
payout_bps: 0
confidence_bps: 9900
reason_codes: ["placeholder_address", "missing_actual_contract_address", "missing_accepted_transaction_statement"]
```

Finalization transaction:

```text
0x7a632eccad787fcf8f14a1bf7ff6a1f2f2de7efd06e82e4ae44cc8270fcd85b3
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Final grant state:

```text
status: completed
escrowed: 1000000000000000000
paid_out: 0
refunded: 1000000000000000000
accounted_balance: 0
```

## Positive Path: Valid Evidence Paid Out

Grant:

```text
grant_id: 1
title: Bradbury Positive Grant Test
```

Milestone:

```text
milestone_id: 0
title: Valid Deployment Evidence Test
allocation_bps: 10000
deadline_ts: 0
```

Funding transaction:

```text
0xd803b85c182da8818cd3dda62ee8ece6a51f0e03600c4d3ecbe093f144ac552d
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Evidence transaction:

```text
0x3cb9c8bcbb60e88a0cab0392266a44d0871331752cf86a275ed38bf3a7bdbaab
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Evidence:

```text
VeriGrant deployed at 0x6CD27E9823dE3B7293AeC9C848cF0e1C131D54c9.
The deployment transaction 0xb6218d6006b1c0787b5bd18155445c7b958ae945e537d9d92dc03f81f1250362 was accepted.
Public test documentation is recorded in the repository test report.
```

Review transaction:

```text
0x31edf837ee1c53bfe29e60a9e0008a1e22a42d2a6b1e7a9071761b2dd6515051
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Review result:

```text
decided: true
decision: complete
completion_bps: 10000
payout_bps: 10000
confidence_bps: 9500
reason_codes: ["contract_address_provided", "deployment_tx_accepted_stated", "test_documentation_referenced", "all_criteria_met"]
```

Finalization transaction:

```text
0x2d49f2e752d5cd405a16c87a7ff2deb72ca7cecf0dafc3cf369ffabe2dd7ec2a
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

Final grant state:

```text
status: completed
escrowed: 1000000000000000000
paid_out: 1000000000000000000
refunded: 0
accounted_balance: 0
```

## Conclusion

VeriGrant passed both reviewer-critical execution paths on Bradbury:

- invalid placeholder evidence is rejected and refunded;
- valid milestone evidence is accepted and paid out;
- internal escrow liability returns to zero after finalization.
