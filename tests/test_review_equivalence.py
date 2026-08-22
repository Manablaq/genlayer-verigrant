"""Regression tests for transfer-bearing VeriGrant review fields.

These tests load the contract's pure normalization/equivalence helpers with a
minimal SDK stub. They intentionally exercise the same helper used by the
nondeterministic validator without requiring a local GenVM node.
"""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _UserError(Exception):
    pass


class _DynArray:
    @classmethod
    def __class_getitem__(cls, _item):
        return cls


def _identity(value):
    return value


def _load_contract_module():
    if "genlayer" not in sys.modules:
        genlayer = types.ModuleType("genlayer")
        genlayer.u256 = int
        genlayer.Address = str
        genlayer.DynArray = _DynArray
        genlayer.allow_storage = _identity
        genlayer.gl = types.SimpleNamespace(
            Contract=object,
            evm=types.SimpleNamespace(contract_interface=_identity),
            public=types.SimpleNamespace(
                write=_identity,
                view=_identity,
            ),
            vm=types.SimpleNamespace(UserError=_UserError),
        )
        genlayer.gl.public.write.payable = _identity
        sys.modules["genlayer"] = genlayer

    path = Path(__file__).parents[1] / "contracts" / "veri_grant.py"
    spec = importlib.util.spec_from_file_location("veri_grant_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


CONTRACT = _load_contract_module()


def _review(payout_bps: int, completion_bps: int = 5_000) -> dict[str, object]:
    return {
        "decision": "partial",
        "completion_bps": completion_bps,
        "payout_bps": payout_bps,
        "confidence_bps": 9_500,
        "reason_codes": ["criteria_partially_satisfied"],
        "evidence_used": ["0"],
        "summary": "The review has a valid, bounded partial-completion result.",
    }


class ReviewEquivalenceTests(unittest.TestCase):
    def test_challenge_window_is_open_before_deadline(self):
        self.assertTrue(CONTRACT._challenge_window_open(3_600, 3_599))

    def test_challenge_window_closes_at_deadline(self):
        self.assertFalse(CONTRACT._challenge_window_open(3_600, 3_600))

    def test_zero_deadline_never_allows_challenge(self):
        self.assertFalse(CONTRACT._challenge_window_open(0, 0))

    def test_exact_payout_matches(self):
        leader = _review(5_000)
        validator = _review(5_000, completion_bps=6_000)

        self.assertTrue(CONTRACT._reviews_equivalent_payload(leader, validator, 10_000))

    def test_one_basis_point_payout_difference_is_not_equivalent(self):
        leader = _review(5_000)
        validator = _review(5_001)

        self.assertFalse(CONTRACT._reviews_equivalent_payload(leader, validator, 10_000))

    def test_former_500_basis_point_tolerance_is_not_equivalent(self):
        leader = _review(5_000)
        validator = _review(5_500)

        self.assertFalse(CONTRACT._reviews_equivalent_payload(leader, validator, 10_000))


if __name__ == "__main__":
    unittest.main()
