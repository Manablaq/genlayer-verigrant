# GenLayer Notes

This document records GenLayer-specific implementation choices for VeriGrant.

## Verified Features Used

- `gl.Contract` for the Intelligent Contract class.
- `@gl.public.write` and `@gl.public.view` for public methods.
- `@gl.public.write.payable` and `gl.message.value` for grant funding.
- `DynArray` storage for grants, milestones, and evidence records.
- `u256` for deadlines, counts, allocations, and accounting.
- `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` for non-deterministic review.
- `gl.nondet.exec_prompt(..., response_format="json")` for structured LLM output.
- `gl.nondet.web.get(...)` and `gl.nondet.web.render(...)` for public evidence fetching.
- `_Recipient(address).emit_transfer(value=...)` for EOA payout/refund messages.

## Storage Layout

VeriGrant uses top-level arrays:

```python
grants: DynArray[Grant]
milestones: DynArray[Milestone]
evidence_items: DynArray[EvidenceItem]
```

Milestones and evidence store explicit `grant_id` and `milestone_id` references. This avoids nested dynamic arrays and remains correct when multiple grants are active at the same time.

## Studio Compatibility

`create_grant` is non-payable. Funding is handled separately through `fund_grant`.

This mirrors the tested pattern from DisputeKit and avoids Studio payable-value ambiguity during object creation.

## Review Equivalence

Validators compare stable fields. Transfer-affecting fields must bind exactly:

- `decision` matches exactly.
- `payout_bps` matches exactly because `finalize_milestone` uses it to calculate
  the escrow transfer.
- `completion_bps`
- `confidence_bps`

The contract intentionally avoids comparing full summary prose.

## Nondeterministic Storage Boundary

Bradbury testing exposed an important boundary: contract storage must not be read from inside the `run_nondet_unsafe` leader or validator closures.

An earlier review transaction returned the correct review payload but ended as `UNDETERMINED` / `DISAGREE`. `gen_dbg_traceTransaction` showed:

```text
Reading storage in nondet mode is not supported
```

The final contract fixes this by:

- reading all grant, milestone, and evidence storage before entering nondeterministic execution;
- passing a plain Python snapshot into the leader and validator;
- using module-level helper functions for review, normalization, and equivalence checks.

This keeps nondeterministic consensus focused on the evidence review itself, not on pickled contract storage.

## Balance Notes

Use `accounted_balance()` for Studio escrow-liability checks.

`contract_balance()` exposes raw `self.balance`, which can differ from internal case accounting after EOA transfer messages in Studio's simulated environment.
