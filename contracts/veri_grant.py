# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import typing


MAX_TEXT_FIELD = 7000
MAX_TITLE = 180
MAX_MILESTONES_PER_GRANT = 20
MAX_EVIDENCE_PER_MILESTONE = 12
MAX_FETCHED_EVIDENCE = 5
MAX_FETCHED_CHARS = 5000
MAX_IMAGE_EVIDENCE = 2
MIN_CHALLENGE_BOND_WEI = u256(10**16)
CHALLENGE_WINDOW_SECONDS = 60 * 60
MAX_CHALLENGES_PER_MILESTONE = 2


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


@allow_storage
@dataclass
class EvidenceItem:
    grant_id: u256
    milestone_id: u256
    submitter: Address
    evidence_type: str
    uri: str
    description: str
    submitted_at: str


@allow_storage
@dataclass
class Review:
    decided: bool
    decision: str
    completion_bps: u256
    payout_bps: u256
    confidence_bps: u256
    summary: str
    reason_codes_json: str
    evidence_used_json: str
    decided_at: str
    challenger: Address


@allow_storage
@dataclass
class ChallengeBond:
    grant_id: u256
    milestone_id: u256
    challenger: Address
    amount: u256


@allow_storage
@dataclass
class Milestone:
    grant_id: u256
    milestone_id: u256
    title: str
    criteria: str
    evidence_schema: str
    allocation_bps: u256
    deadline_ts: u256
    status: str
    paid_out: u256
    refunded: u256
    evidence_count: u256
    reviewed_at: u256
    challenge_deadline_ts: u256
    challenge_bond: u256
    challenge_count: u256
    review: Review


@allow_storage
@dataclass
class Grant:
    sponsor: Address
    grantee: Address
    title: str
    grant_spec: str
    review_policy: str
    status: str
    created_at: str
    escrowed: u256
    paid_out: u256
    refunded: u256
    milestone_count: u256
    allocation_bps_total: u256


def _normalize_review_payload(raw: dict[str, typing.Any], allocation_bps: int) -> dict[str, typing.Any]:
    if not isinstance(raw, dict):
        raise gl.vm.UserError("review must be an object")

    decision = str(raw.get("decision", "")).strip().lower()
    if decision not in ["complete", "incomplete", "partial", "needs_more_evidence"]:
        raise gl.vm.UserError("invalid decision")

    completion_bps = int(raw.get("completion_bps", 0))
    payout_bps = int(raw.get("payout_bps", 0))
    confidence_bps = int(raw.get("confidence_bps", 0))
    if completion_bps < 0 or completion_bps > 10000:
        raise gl.vm.UserError("invalid completion_bps")
    if payout_bps < 0 or payout_bps > allocation_bps:
        raise gl.vm.UserError("invalid payout_bps")
    if confidence_bps < 0 or confidence_bps > 10000:
        raise gl.vm.UserError("invalid confidence_bps")
    if decision in ["incomplete", "needs_more_evidence"] and payout_bps > 0:
        raise gl.vm.UserError("non-complete decisions cannot pay out")
    if decision == "complete" and payout_bps < allocation_bps:
        raise gl.vm.UserError("complete decision must release full milestone allocation")

    reason_codes = raw.get("reason_codes", [])
    if not isinstance(reason_codes, list):
        reason_codes = []
    clean_reasons = []
    for reason in reason_codes[:10]:
        code = str(reason).strip().lower().replace(" ", "_")[:56]
        if code:
            clean_reasons.append(code)

    evidence_used = raw.get("evidence_used", [])
    if not isinstance(evidence_used, list):
        evidence_used = []
    clean_evidence = []
    for evidence in evidence_used[:12]:
        clean_evidence.append(str(evidence)[:180])

    summary = str(raw.get("summary", "")).strip()[:900]
    if not summary:
        summary = "No summary provided."

    return {
        "decision": decision,
        "completion_bps": completion_bps,
        "payout_bps": payout_bps,
        "confidence_bps": confidence_bps,
        "reason_codes": clean_reasons,
        "evidence_used": clean_evidence,
        "summary": summary,
    }


def _reviews_equivalent_payload(
    proposed: dict[str, typing.Any],
    validator_result: dict[str, typing.Any],
    allocation_bps: int,
) -> bool:
    a = _normalize_review_payload(proposed, allocation_bps)
    b = _normalize_review_payload(validator_result, allocation_bps)
    if a["decision"] != b["decision"]:
        return False
    # payout_bps is consumed by finalize_milestone to calculate an escrow
    # transfer, so validators must bind the exact amount rather than a range.
    if a["payout_bps"] != b["payout_bps"]:
        return False
    if abs(a["completion_bps"] - b["completion_bps"]) > 1500:
        return False
    if a["decision"] in ["complete", "incomplete"] and abs(a["confidence_bps"] - b["confidence_bps"]) > 2500:
        return False
    return True


def _challenge_window_open(challenge_deadline_ts: int, now_ts: int) -> bool:
    return int(challenge_deadline_ts) > 0 and int(now_ts) < int(challenge_deadline_ts)


def _judge_snapshot_payload(snapshot: dict[str, typing.Any]) -> dict[str, typing.Any]:
    fetched = []
    images = []
    fetch_count = 0
    for item in snapshot["evidence"]:
        if fetch_count >= MAX_FETCHED_EVIDENCE:
            break
        if item["evidence_type"] in ["url", "api", "image_url"] and item["uri"]:
            fetch_count += 1
            try:
                if item["evidence_type"] == "api":
                    response = gl.nondet.web.get(item["uri"])
                    body = response.body.decode("utf-8")[:MAX_FETCHED_CHARS]
                elif item["evidence_type"] == "image_url":
                    if len(images) < MAX_IMAGE_EVIDENCE:
                        screenshot = gl.nondet.web.render(
                            item["uri"],
                            mode="screenshot",
                            wait_after_loaded="2s",
                        )
                        images.append(screenshot)
                        body = "Screenshot captured for visual milestone review."
                    else:
                        body = "Image evidence skipped because image limit was reached."
                else:
                    body = gl.nondet.web.render(
                        item["uri"],
                        mode="text",
                        wait_after_loaded="2s",
                    )[:MAX_FETCHED_CHARS]
                fetched.append(
                    {
                        "uri": item["uri"],
                        "evidence_type": item["evidence_type"],
                        "content_excerpt": body,
                    }
                )
            except Exception as exc:
                fetched.append(
                    {
                        "uri": item["uri"],
                        "evidence_type": item["evidence_type"],
                        "fetch_error": str(exc)[:240],
                    }
                )

    prompt = f"""
You are a milestone reviewer for VeriGrant, a reusable GenLayer grant primitive.
Evaluate whether the grantee satisfied this milestone.

Return JSON exactly matching this schema:
{{
  "decision": "complete" | "incomplete" | "partial" | "needs_more_evidence",
  "completion_bps": integer from 0 to 10000,
  "payout_bps": integer from 0 to the milestone allocation_bps,
  "confidence_bps": integer from 0 to 10000,
  "reason_codes": array of short snake_case strings,
  "evidence_used": array of evidence indexes or URIs,
  "summary": concise explanation under 900 characters
}}

Decision rules:
- complete means the milestone criteria are materially satisfied.
- incomplete means the evidence materially fails the criteria.
- partial means enough work is complete to justify partial release under review_policy.
- needs_more_evidence means the current record cannot support a reliable decision.
- payout_bps is denominated against the total grant, not only this milestone.
- payout_bps must never exceed milestone allocation_bps.
- If decision is complete, payout_bps must equal allocation_bps.
- If decision is incomplete or needs_more_evidence, payout_bps must be 0.
- Compare evidence against the milestone criteria and review_policy, not unstated preferences.

Milestone review packet:
{json.dumps(snapshot, sort_keys=True)}

Fetched public evidence excerpts:
{json.dumps(fetched, sort_keys=True)}
"""
    if len(images) > 0:
        raw = gl.nondet.exec_prompt(prompt, images=images, response_format="json")
    else:
        raw = gl.nondet.exec_prompt(prompt, response_format="json")
    return _normalize_review_payload(raw, int(snapshot["allocation_bps"]))


class VeriGrant(gl.Contract):
    """
    Reusable milestone grant verifier for GenLayer.

    Sponsors define grants and milestone criteria, fund escrow, and ask GenLayer
    validators to review public evidence before milestone funds are released.
    """

    grants: DynArray[Grant]
    milestones: DynArray[Milestone]
    evidence_items: DynArray[EvidenceItem]
    challenge_bonds: DynArray[ChallengeBond]

    def __init__(self):
        pass

    @gl.public.write
    def create_grant(
        self,
        grantee: str,
        title: str,
        grant_spec: str,
        review_policy: str,
    ) -> u256:
        grantee_text = str(grantee)
        self._require_nonempty(grantee_text, "grantee")
        self._require_nonempty(title, "title")
        self._require_nonempty(grant_spec, "grant_spec")
        self._require_nonempty(review_policy, "review_policy")
        self._require_short(title, MAX_TITLE, "title")
        self._require_short(grant_spec, MAX_TEXT_FIELD, "grant_spec")
        self._require_short(review_policy, MAX_TEXT_FIELD, "review_policy")

        grant_id = u256(len(self.grants))
        grant = Grant(
            sponsor=gl.message.sender_address,
            grantee=Address(grantee_text),
            title=title,
            grant_spec=grant_spec,
            review_policy=review_policy,
            status="draft",
            created_at=self._now_iso(),
            escrowed=u256(0),
            paid_out=u256(0),
            refunded=u256(0),
            milestone_count=u256(0),
            allocation_bps_total=u256(0),
        )
        self.grants.append(grant)
        return grant_id

    @gl.public.write
    def add_milestone(
        self,
        grant_id: int,
        title: str,
        criteria: str,
        evidence_schema: str,
        allocation_bps: u256,
        deadline_ts: u256,
    ) -> u256:
        grant = self._grant(grant_id)
        if gl.message.sender_address != grant.sponsor:
            raise gl.vm.UserError("only sponsor can add milestones")
        if grant.status not in ["draft", "active"]:
            raise gl.vm.UserError("grant is closed")
        if grant.escrowed > u256(0):
            raise gl.vm.UserError("cannot add milestones after funding")
        if grant.milestone_count >= u256(MAX_MILESTONES_PER_GRANT):
            raise gl.vm.UserError("too many milestones")
        if allocation_bps == u256(0):
            raise gl.vm.UserError("allocation_bps is required")
        if grant.allocation_bps_total + allocation_bps > u256(10000):
            raise gl.vm.UserError("grant allocations exceed 10000 bps")
        self._require_nonempty(title, "title")
        self._require_nonempty(criteria, "criteria")
        self._require_nonempty(evidence_schema, "evidence_schema")
        self._require_short(title, MAX_TITLE, "title")
        self._require_short(criteria, MAX_TEXT_FIELD, "criteria")
        self._require_short(evidence_schema, MAX_TEXT_FIELD, "evidence_schema")

        milestone_id = grant.milestone_count
        review = self._empty_review()
        milestone = Milestone(
            grant_id=u256(grant_id),
            milestone_id=milestone_id,
            title=title,
            criteria=criteria,
            evidence_schema=evidence_schema,
            allocation_bps=allocation_bps,
            deadline_ts=deadline_ts,
            status="open",
            paid_out=u256(0),
            refunded=u256(0),
            evidence_count=u256(0),
            reviewed_at=u256(0),
            challenge_deadline_ts=u256(0),
            challenge_bond=u256(0),
            challenge_count=u256(0),
            review=review,
        )
        self.milestones.append(milestone)
        grant.milestone_count = grant.milestone_count + u256(1)
        grant.allocation_bps_total = grant.allocation_bps_total + allocation_bps
        if grant.status == "draft":
            grant.status = "active"
        return milestone_id

    @gl.public.write.payable
    def fund_grant(self, grant_id: int) -> None:
        grant = self._grant(grant_id)
        if gl.message.sender_address != grant.sponsor:
            raise gl.vm.UserError("only sponsor can fund grant")
        if grant.status not in ["draft", "active"]:
            raise gl.vm.UserError("grant is closed")
        for i in range(int(grant.milestone_count)):
            existing = self._milestone(grant_id, grant, i)
            if existing.status not in ["open", "evidence_submitted"]:
                raise gl.vm.UserError("grant has progressed beyond funding")
        if gl.message.value == u256(0):
            raise gl.vm.UserError("no value sent")
        grant.escrowed = grant.escrowed + gl.message.value
        if grant.status == "draft":
            grant.status = "active"

    @gl.public.write
    def submit_milestone_evidence(
        self,
        grant_id: int,
        milestone_id: int,
        evidence_type: str,
        uri: str,
        description: str,
    ) -> None:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        if milestone.status not in ["open", "evidence_submitted", "challenged"]:
            raise gl.vm.UserError("milestone is not accepting evidence")
        if gl.message.sender_address not in [grant.sponsor, grant.grantee]:
            raise gl.vm.UserError("only sponsor or grantee can submit evidence")
        if gl.message.sender_address == grant.grantee and self._deadline_passed(milestone):
            raise gl.vm.UserError("milestone deadline has passed")
        self._append_evidence(u256(grant_id), u256(milestone_id), milestone, evidence_type, uri, description)
        if milestone.status == "open":
            milestone.status = "evidence_submitted"

    @gl.public.write
    def request_milestone_review(self, grant_id: int, milestone_id: int) -> None:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        if milestone.status not in ["evidence_submitted", "challenged"]:
            raise gl.vm.UserError("milestone has no evidence ready for review")
        if milestone.evidence_count == u256(0):
            raise gl.vm.UserError("no evidence submitted")
        if grant.escrowed == u256(0):
            raise gl.vm.UserError("grant must be funded before review")
        if gl.message.sender_address not in [grant.sponsor, grant.grantee]:
            raise gl.vm.UserError("only sponsor or grantee can request review")

        review = self._review_milestone(grant, milestone)
        milestone.review = review
        self._start_challenge_window(milestone)
        milestone.status = "reviewed"

    @gl.public.write.payable
    def challenge_milestone_review(
        self,
        grant_id: int,
        milestone_id: int,
        evidence_type: str,
        uri: str,
        description: str,
    ) -> None:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        if milestone.status != "reviewed":
            raise gl.vm.UserError("only reviewed milestones can be challenged")
        if not self._challenge_window_is_open(milestone):
            raise gl.vm.UserError("challenge window is closed")
        if gl.message.sender_address not in [grant.sponsor, grant.grantee]:
            raise gl.vm.UserError("only sponsor or grantee can challenge")
        if gl.message.value < MIN_CHALLENGE_BOND_WEI:
            raise gl.vm.UserError("challenge bond too small")
        if milestone.challenge_count >= u256(MAX_CHALLENGES_PER_MILESTONE):
            raise gl.vm.UserError("milestone challenge limit reached")

        milestone.challenge_bond = milestone.challenge_bond + gl.message.value
        milestone.challenge_count = milestone.challenge_count + u256(1)
        self.challenge_bonds.append(
            ChallengeBond(
                grant_id=u256(grant_id),
                milestone_id=u256(milestone_id),
                challenger=gl.message.sender_address,
                amount=gl.message.value,
            )
        )
        milestone.status = "challenged"
        self._append_evidence(u256(grant_id), u256(milestone_id), milestone, evidence_type, uri, description)
        review = self._review_milestone(grant, milestone)
        review.challenger = gl.message.sender_address
        milestone.review = review
        self._start_challenge_window(milestone)
        milestone.status = "reviewed"

    @gl.public.write
    def finalize_milestone(self, grant_id: int, milestone_id: int) -> None:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        if milestone.status != "reviewed":
            raise gl.vm.UserError("milestone must be reviewed before finalization")
        if not milestone.review.decided:
            raise gl.vm.UserError("milestone review is not decided")
        if self._challenge_window_is_open(milestone):
            raise gl.vm.UserError("challenge window is still open")

        allocated = (grant.escrowed * milestone.allocation_bps) // u256(10000)
        if milestone.paid_out + milestone.refunded > allocated:
            raise gl.vm.UserError("milestone accounting exceeds allocation")
        remaining_allocation = allocated - milestone.paid_out - milestone.refunded
        if remaining_allocation == u256(0):
            milestone.status = "finalized"
            self._refund_challenge_bond(milestone)
            self._close_grant_if_complete(grant_id, grant)
            return

        payout_target = (grant.escrowed * milestone.review.payout_bps) // u256(10000)
        if payout_target > remaining_allocation:
            payout_target = remaining_allocation
        refund = remaining_allocation - payout_target

        if payout_target > u256(0):
            milestone.paid_out = milestone.paid_out + payout_target
            grant.paid_out = grant.paid_out + payout_target
            _Recipient(grant.grantee).emit_transfer(value=payout_target)
        if refund > u256(0):
            milestone.refunded = milestone.refunded + refund
            grant.refunded = grant.refunded + refund
            _Recipient(grant.sponsor).emit_transfer(value=refund)

        milestone.status = "finalized"
        self._refund_challenge_bond(milestone)
        self._close_grant_if_complete(grant_id, grant)

    @gl.public.write
    def cancel_unfunded_grant(self, grant_id: int) -> None:
        grant = self._grant(grant_id)
        if gl.message.sender_address != grant.sponsor:
            raise gl.vm.UserError("only sponsor can cancel")
        if grant.escrowed > u256(0):
            raise gl.vm.UserError("funded grant cannot be cancelled here")
        if grant.paid_out > u256(0) or grant.refunded > u256(0):
            raise gl.vm.UserError("grant has accounting activity")
        grant.status = "cancelled"

    @gl.public.write
    def expire_milestone(self, grant_id: int, milestone_id: int) -> None:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        if milestone.status != "open" or milestone.evidence_count > u256(0):
            raise gl.vm.UserError("milestone is not an unsubmitted open milestone")
        if not self._deadline_passed(milestone):
            raise gl.vm.UserError("deadline has not passed")

        allocated = (grant.escrowed * milestone.allocation_bps) // u256(10000)
        remaining_allocation = allocated - milestone.paid_out - milestone.refunded
        if remaining_allocation > u256(0):
            milestone.refunded = milestone.refunded + remaining_allocation
            grant.refunded = grant.refunded + remaining_allocation
            _Recipient(grant.sponsor).emit_transfer(value=remaining_allocation)
        milestone.status = "expired"
        self._close_grant_if_complete(grant_id, grant)

    @gl.public.view
    def get_grant_count(self) -> u256:
        return u256(len(self.grants))

    @gl.public.view
    def get_grant(self, grant_id: int) -> dict[str, typing.Any]:
        grant = self._grant(grant_id)
        return {
            "id": u256(grant_id),
            "sponsor": str(grant.sponsor),
            "grantee": str(grant.grantee),
            "title": grant.title,
            "grant_spec": grant.grant_spec,
            "review_policy": grant.review_policy,
            "status": grant.status,
            "created_at": grant.created_at,
            "escrowed": grant.escrowed,
            "paid_out": grant.paid_out,
            "refunded": grant.refunded,
            "milestone_count": grant.milestone_count,
            "allocation_bps_total": grant.allocation_bps_total,
        }

    @gl.public.view
    def get_milestone(self, grant_id: int, milestone_id: int) -> dict[str, typing.Any]:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        return {
            "grant_id": milestone.grant_id,
            "milestone_id": milestone.milestone_id,
            "title": milestone.title,
            "criteria": milestone.criteria,
            "evidence_schema": milestone.evidence_schema,
            "allocation_bps": milestone.allocation_bps,
            "deadline_ts": milestone.deadline_ts,
            "deadline_passed": self._deadline_passed(milestone),
            "status": milestone.status,
            "reviewed_at": milestone.reviewed_at,
            "challenge_deadline_ts": milestone.challenge_deadline_ts,
            "challenge_window_open": self._challenge_window_is_open(milestone),
            "challenge_bond": milestone.challenge_bond,
            "challenge_count": milestone.challenge_count,
            "paid_out": milestone.paid_out,
            "refunded": milestone.refunded,
            "evidence_count": milestone.evidence_count,
        }

    @gl.public.view
    def get_evidence(self, grant_id: int, milestone_id: int, evidence_index: int) -> dict[str, typing.Any]:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        if evidence_index < 0 or evidence_index >= int(milestone.evidence_count):
            raise gl.vm.UserError("evidence not found")
        item = self._evidence(grant_id, milestone_id, evidence_index)
        return {
            "grant_id": item.grant_id,
            "milestone_id": item.milestone_id,
            "submitter": str(item.submitter),
            "evidence_type": item.evidence_type,
            "uri": item.uri,
            "description": item.description,
            "submitted_at": item.submitted_at,
        }

    @gl.public.view
    def get_review(self, grant_id: int, milestone_id: int) -> dict[str, typing.Any]:
        grant = self._grant(grant_id)
        milestone = self._milestone(grant_id, grant, milestone_id)
        review = milestone.review
        return {
            "decided": review.decided,
            "decision": review.decision,
            "completion_bps": review.completion_bps,
            "payout_bps": review.payout_bps,
            "confidence_bps": review.confidence_bps,
            "summary": review.summary,
            "reason_codes": review.reason_codes_json,
            "evidence_used": review.evidence_used_json,
            "decided_at": review.decided_at,
            "challenger": str(review.challenger),
        }

    @gl.public.view
    def contract_balance(self) -> u256:
        return self.balance

    @gl.public.view
    def accounted_balance(self) -> u256:
        total = u256(0)
        for i in range(len(self.grants)):
            grant = self.grants[i]
            total = total + grant.escrowed - grant.paid_out - grant.refunded
            for milestone_id in range(int(grant.milestone_count)):
                milestone = self._milestone(i, grant, milestone_id)
                total = total + milestone.challenge_bond
        return total

    def _review_milestone(self, grant: Grant, milestone: Milestone) -> Review:
        snapshot = self._milestone_snapshot(grant, milestone)
        allocation_bps = int(milestone.allocation_bps)

        def leader_fn():
            return _judge_snapshot_payload(snapshot)

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            try:
                proposed = leaders_res.calldata
                validator_result = _judge_snapshot_payload(snapshot)
                return _reviews_equivalent_payload(proposed, validator_result, allocation_bps)
            except Exception:
                return False

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        normalized = _normalize_review_payload(result, allocation_bps)
        return Review(
            decided=True,
            decision=normalized["decision"],
            completion_bps=u256(normalized["completion_bps"]),
            payout_bps=u256(normalized["payout_bps"]),
            confidence_bps=u256(normalized["confidence_bps"]),
            summary=normalized["summary"],
            reason_codes_json=json.dumps(normalized["reason_codes"], sort_keys=True),
            evidence_used_json=json.dumps(normalized["evidence_used"], sort_keys=True),
            decided_at=self._now_iso(),
            challenger=Address("0x0000000000000000000000000000000000000000"),
        )

    def _judge_snapshot(self, snapshot: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return _judge_snapshot_payload(snapshot)

    def _milestone_snapshot(self, grant: Grant, milestone: Milestone) -> dict[str, typing.Any]:
        evidence = []
        for i in range(int(milestone.evidence_count)):
            item = self._evidence(int(milestone.grant_id), int(milestone.milestone_id), i)
            evidence.append(
                {
                    "index": i,
                    "submitter": str(item.submitter),
                    "evidence_type": item.evidence_type,
                    "uri": item.uri,
                    "description": item.description,
                    "submitted_at": item.submitted_at,
                }
            )
        return {
            "sponsor": str(grant.sponsor),
            "grantee": str(grant.grantee),
            "grant_title": grant.title,
            "grant_spec": grant.grant_spec,
            "review_policy": grant.review_policy,
            "grant_escrowed": int(grant.escrowed),
            "milestone_title": milestone.title,
            "criteria": milestone.criteria,
            "evidence_schema": milestone.evidence_schema,
            "allocation_bps": int(milestone.allocation_bps),
            "deadline_ts": int(milestone.deadline_ts),
            "evidence": evidence,
        }

    def _normalize_review(self, raw: dict[str, typing.Any], allocation_bps: int) -> dict[str, typing.Any]:
        return _normalize_review_payload(raw, allocation_bps)

    def _reviews_equivalent(
        self,
        proposed: dict[str, typing.Any],
        validator_result: dict[str, typing.Any],
        allocation_bps: int,
    ) -> bool:
        return _reviews_equivalent_payload(proposed, validator_result, allocation_bps)

    def _grant(self, grant_id: int) -> Grant:
        if grant_id < 0 or grant_id >= len(self.grants):
            raise gl.vm.UserError("grant not found")
        return self.grants[grant_id]

    def _milestone(self, grant_id: int, grant: Grant, milestone_id: int) -> Milestone:
        if milestone_id < 0 or milestone_id >= int(grant.milestone_count):
            raise gl.vm.UserError("milestone not found")
        for i in range(len(self.milestones)):
            milestone = self.milestones[i]
            if milestone.grant_id == u256(grant_id) and milestone.milestone_id == u256(milestone_id):
                return milestone
        raise gl.vm.UserError("milestone not found")

    def _evidence(self, grant_id: int, milestone_id: int, evidence_index: int) -> EvidenceItem:
        seen = 0
        for i in range(len(self.evidence_items)):
            item = self.evidence_items[i]
            if item.grant_id == u256(grant_id) and item.milestone_id == u256(milestone_id):
                if seen == evidence_index:
                    return item
                seen += 1
        raise gl.vm.UserError("evidence not found")

    def _append_evidence(
        self,
        grant_id: u256,
        milestone_id: u256,
        milestone: Milestone,
        evidence_type: str,
        uri: str,
        description: str,
    ) -> None:
        if milestone.evidence_count >= u256(MAX_EVIDENCE_PER_MILESTONE):
            raise gl.vm.UserError("too many evidence items")
        evidence_type_text = str(evidence_type)
        uri_text = "" if uri == 0 else str(uri)
        description_text = "" if description == 0 else str(description)
        self._require_nonempty(evidence_type_text, "evidence_type")
        self._require_short(evidence_type_text, 32, "evidence_type")
        self._require_short(uri_text, 600, "uri")
        self._require_short(description_text, MAX_TEXT_FIELD, "description")
        if evidence_type_text not in ["text", "url", "api", "image_url", "attestation"]:
            raise gl.vm.UserError("unsupported evidence_type")
        if evidence_type_text in ["url", "api", "image_url"] and not uri_text.startswith("https://"):
            raise gl.vm.UserError("web evidence requires an HTTPS URI")
        if not uri_text and not description_text:
            raise gl.vm.UserError("evidence requires a URI or description")

        self.evidence_items.append(
            EvidenceItem(
                grant_id=grant_id,
                milestone_id=milestone_id,
                submitter=gl.message.sender_address,
                evidence_type=evidence_type_text,
                uri=uri_text,
                description=description_text,
                submitted_at=self._now_iso(),
            )
        )
        milestone.evidence_count = milestone.evidence_count + u256(1)

    def _empty_review(self) -> Review:
        return Review(
            decided=False,
            decision="pending",
            completion_bps=u256(0),
            payout_bps=u256(0),
            confidence_bps=u256(0),
            summary="",
            reason_codes_json="[]",
            evidence_used_json="[]",
            decided_at="",
            challenger=Address("0x0000000000000000000000000000000000000000"),
        )

    def _close_grant_if_complete(self, grant_id: int, grant: Grant) -> None:
        for i in range(int(grant.milestone_count)):
            milestone = self._milestone(grant_id, grant, i)
            if milestone.status not in ["finalized", "expired"]:
                return
        remaining = grant.escrowed - grant.paid_out - grant.refunded
        if remaining > u256(0):
            grant.refunded = grant.refunded + remaining
            _Recipient(grant.sponsor).emit_transfer(value=remaining)
        grant.status = "completed"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _now_ts(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _deadline_passed(self, milestone: Milestone) -> bool:
        return milestone.deadline_ts > u256(0) and self._now_ts() > int(milestone.deadline_ts)

    def _start_challenge_window(self, milestone: Milestone) -> None:
        milestone.reviewed_at = u256(self._now_ts())
        milestone.challenge_deadline_ts = milestone.reviewed_at + u256(CHALLENGE_WINDOW_SECONDS)

    def _challenge_window_is_open(self, milestone: Milestone) -> bool:
        return _challenge_window_open(milestone.challenge_deadline_ts, self._now_ts())

    def _refund_challenge_bond(self, milestone: Milestone) -> None:
        if milestone.challenge_bond == u256(0):
            return
        refunded = u256(0)
        for i in range(len(self.challenge_bonds)):
            bond = self.challenge_bonds[i]
            if (
                bond.grant_id == milestone.grant_id
                and bond.milestone_id == milestone.milestone_id
                and bond.amount > u256(0)
            ):
                amount = bond.amount
                bond.amount = u256(0)
                refunded = refunded + amount
                _Recipient(bond.challenger).emit_transfer(value=amount)
        if refunded != milestone.challenge_bond:
            raise gl.vm.UserError("challenge bond accounting mismatch")
        milestone.challenge_bond = u256(0)

    def _require_nonempty(self, value: str, field: str) -> None:
        if len(value.strip()) == 0:
            raise gl.vm.UserError(f"{field} is required")

    def _require_short(self, value: str, max_len: int, field: str) -> None:
        if len(value) > max_len:
            raise gl.vm.UserError(f"{field} is too long")
