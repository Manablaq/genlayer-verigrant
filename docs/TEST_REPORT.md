# Corrected Bradbury Test Report

This report records the Bradbury deployment and end-to-end execution evidence
for VeriGrant's exact-payout consensus correction.

## Corrected Deployment

Contract:

```text
0x6B7D4b407954629C34d628f31672f4129f1926D1
```

Deployment transaction:

```text
0x4ea22133cea28cfa94fcb9be6ffc34c99d9030ebc3b6bfda65a0947d367fadbf
```

Deployment result:

```text
statusName: ACCEPTED
resultName: AGREE
txExecutionResultName: FINISHED_WITH_RETURN
```

The deployment transaction embeds source that matches
`contracts/veri_grant.py` at commit `4e43896` byte-for-byte.

```text
source_sha256: 6ce54502485bc483b79a6b777845da622290fd0f4232f2b8bb4a39ab13e737f7
```

The prior deployment at `0x6CD27E9823dE3B7293AeC9C848cF0e1C131D54c9`
is historical only. It allowed a payout tolerance and is not evidence for this
release.

## Baseline

```text
get_grant_count: 0
accounted_balance: 0
```

## Negative Path: Placeholder Evidence Is Refunded

The contract created and funded a `10000`-bps milestone with `1 GEN` escrow.
It received deliberately invalid evidence containing `YOUR_CONTRACT_ADDRESS`
and only a vague success claim.

| Step | Transaction |
| --- | --- |
| Create grant | `0x2fad34e2bd96c2a7d77f7c38e8da3f991a70672a80e86c4c725ad436ab044cf1` |
| Add milestone | `0xe2f438375fed904f434e363cc4bb37d205aa2c83aeca355f13320b64e478b93a` |
| Fund `1 GEN` | `0xdab196cb6eab7411efd092a83192f7ee8b089f295503fab24e5f82b52e296016` |
| Submit placeholder evidence | `0xa8cee0bdc9875552e427c66814563386dbc29e724ddca3655d31e5a286eb4173` |
| Request review | `0x5d0f6bcaafcd1cfc622af40291f72a59d5e9ef7afb410778eb1c2e49139bc8b0` |
| Finalize | `0x070f573338ee11a837e890d58402661e23d18fe273eae5d7ab8bb794b817c699` |

Every transaction was `ACCEPTED`, `AGREE`, and `FINISHED_WITH_RETURN`.

Review result:

```text
decision: incomplete
completion_bps: 0
payout_bps: 0
reason_codes: ["placeholder_address", "vague_deployment_claim", "no_explicit_acceptance"]
```

Final state:

```text
grant_id: 0
status: completed
escrowed: 1000000000000000000
paid_out: 0
refunded: 1000000000000000000
accounted_balance: 0
```

## Positive Path: Valid Evidence Is Paid In Full

The contract created and funded a second `10000`-bps milestone with `1 GEN`
escrow. Evidence named the corrected contract, stated that its deployment
transaction was accepted, identified the exact-payout source revision, and
linked to the public test plan.

| Step | Transaction |
| --- | --- |
| Create grant | `0xcf1364a191f9eddb006199e357cf9236fa7b28e6c296cbe018170b5b6b7d0604` |
| Add milestone | `0x0df7d3c984f41651eec7d1dcb5dd2de64f5be68613d01dc8103e739d12fde7fc` |
| Fund `1 GEN` | `0x4274b8f94f340c36130f9f20dd26f559dc1ffae562ecfde6005123361ce49a1b` |
| Submit valid evidence | `0x511f226e4d01249b69d3e0996ebc1ccc6b514347f41f9d6e2a4760bac6ef6dc6` |
| Request review | `0x86302e0f44a40091edb848e46bfc1c2c9de438ae992095b8ba722d4500f1eeb3` |
| Finalize | `0x7798156ee245ec77776c6aeb9fdb0976862f754b10e9560a5583e816675a66cc` |

Every transaction was `ACCEPTED`, `AGREE`, and `FINISHED_WITH_RETURN`.

Review result:

```text
decision: complete
completion_bps: 10000
payout_bps: 10000
confidence_bps: 10000
reason_codes: ["all_criteria_met"]
```

Final state:

```text
grant_id: 1
status: completed
escrowed: 1000000000000000000
paid_out: 1000000000000000000
refunded: 0
accounted_balance: 0
```

## Conclusion

The corrected source binds `payout_bps` exactly during validator equivalence,
and the deployed matching contract completed both escrow outcomes on Bradbury:

- invalid evidence produced `payout_bps: 0` and a full refund;
- valid evidence produced `payout_bps: 10000` and a full payout;
- internal escrow liability returned to zero after each outcome.
