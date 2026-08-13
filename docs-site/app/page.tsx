const correctedContractAddress = "0x6B7D4b407954629C34d628f31672f4129f1926D1";
const correctedDeploymentTx =
  "0x4ea22133cea28cfa94fcb9be6ffc34c99d9030ebc3b6bfda65a0947d367fadbf";

const lifecycle = [
  ["1", "Create", "Sponsor creates a grant with a grantee, scope, and review policy."],
  ["2", "Configure", "Sponsor adds milestones with criteria, evidence schema, and allocation bps."],
  ["3", "Fund", "Sponsor deposits escrow through the payable fund_grant method."],
  ["4", "Evidence", "Sponsor or grantee submits text, URL, API, image URL, or attestation evidence."],
  ["5", "Review", "GenLayer validators run nondeterministic evidence review and store a structured result."],
  ["6", "Finalize", "The contract pays the grantee, refunds the sponsor, or splits the allocation."],
];

const writeMethods = [
  ["create_grant", "Create a reusable grant record for one sponsor and grantee."],
  ["add_milestone", "Attach criteria, evidence schema, allocation_bps, and optional deadline."],
  ["fund_grant", "Payable escrow funding for a grant."],
  ["submit_milestone_evidence", "Add bounded milestone evidence."],
  ["request_milestone_review", "Run GenLayer nondeterministic consensus over milestone evidence."],
  ["challenge_milestone_review", "Bonded counter-evidence and re-review path."],
  ["finalize_milestone", "Apply payout/refund after a decided review."],
  ["cancel_unfunded_grant", "Cancel a grant with no escrow activity."],
  ["expire_milestone", "Refund an unfurnished milestone after a deadline."],
];

const readMethods = [
  ["get_grant_count", "Count grants."],
  ["get_grant", "Read sponsor, grantee, status, escrow, payout, and refund fields."],
  ["get_milestone", "Read milestone criteria, allocation, evidence count, and status."],
  ["get_evidence", "Read a specific evidence record."],
  ["get_review", "Read structured AI/validator review output."],
  ["contract_balance", "Raw GenLayer contract balance."],
  ["accounted_balance", "Internal escrow liability across active grants."],
];

const tests = [
  {
    title: "Negative Path",
    result: "Placeholder evidence rejected and refunded",
    details: [
      "decision: incomplete",
      "payout_bps: 0",
      "refunded: 1000000000000000000",
      "accounted_balance: 0",
    ],
  },
  {
    title: "Positive Path",
    result: "Valid evidence accepted and paid out",
    details: [
      "decision: complete",
      "payout_bps: 10000",
      "paid_out: 1000000000000000000",
      "accounted_balance: 0",
    ],
  },
];

const codeSample = `# Deploy contracts/veri_grant.py on Bradbury, then:

create_grant(
  grantee="0x5bB49021001200fE8156a81c7fcF097e535e7181",
  title="Milestone Grant",
  grant_spec="Deliver the agreed public artifact.",
  review_policy="Release funds only when evidence satisfies the milestone criteria."
)

add_milestone(
  grant_id=0,
  title="Deployment and Test Report",
  criteria="Evidence must include a deployed contract address and accepted transaction.",
  evidence_schema="Submit one text evidence item.",
  allocation_bps=10000,
  deadline_ts=0
)

fund_grant(grant_id=0)  # payable value in Studio
submit_milestone_evidence(0, 0, "text", "", "Evidence text...")
request_milestone_review(0, 0)
finalize_milestone(0, 0)`;

export default function Home() {
  return (
    <main>
      <nav className="topbar" aria-label="Primary">
        <a href="#overview" className="brand" aria-label="VeriGrant overview">
          <span className="brand-mark">VG</span>
          <span>VeriGrant</span>
        </a>
        <div className="navlinks">
          <a href="#developer-guide">Guide</a>
          <a href="#api">API</a>
          <a href="#testing">Testing</a>
          <a href="https://github.com/Manablaq/genlayer-verigrant">GitHub</a>
        </div>
      </nav>

      <section className="hero" id="overview">
        <div className="hero-copy">
          <p className="eyebrow">GenLayer Intelligent Contract Primitive</p>
          <h1>AI-reviewed milestone grants with escrow-safe payouts.</h1>
          <p className="lede">
            VeriGrant lets sponsors fund milestone-based work, collect evidence,
            use GenLayer consensus to review completion, and finalize deterministic
            payout or refund accounting.
          </p>
          <div className="hero-actions" aria-label="Project links">
            <a className="primary-link" href="#developer-guide">
              Start building
            </a>
            <a className="secondary-link" href="https://github.com/Manablaq/genlayer-verigrant/blob/main/docs/TEST_REPORT.md">
              View Bradbury report
            </a>
          </div>
        </div>
        <aside className="deployment-panel" aria-label="Bradbury deployment">
          <div>
            <span className="label">Corrected Deployment</span>
            <code>{correctedContractAddress}</code>
          </div>
          <div>
            <span className="label">Deployment Transaction</span>
            <code>{correctedDeploymentTx}</code>
          </div>
          <div className="status-grid">
            <span>EXACT PAYOUT</span>
            <span>BRADBURY VERIFIED</span>
            <span>SOURCE MATCHED</span>
          </div>
        </aside>
      </section>

      <section className="section" id="why">
        <div className="section-heading">
          <p className="eyebrow">Purpose</p>
          <h2>Built as a reusable primitive, not a one-off demo.</h2>
        </div>
        <div className="two-column">
          <p>
            Grant programs, DAO funding, open-source sponsorships, research
            awards, and AI-agent work orders all need the same core primitive:
            evidence-backed milestone review before escrow is released.
          </p>
          <p>
            VeriGrant models that primitive directly in contract state. It uses
            deterministic storage and accounting for funds, and GenLayer
            nondeterministic consensus for evidence interpretation.
          </p>
        </div>
      </section>

      <section className="section" id="developer-guide">
        <div className="section-heading">
          <p className="eyebrow">Developer Guide</p>
          <h2>How builders integrate VeriGrant.</h2>
        </div>
        <div className="timeline">
          {lifecycle.map(([step, title, body]) => (
            <article key={step} className="timeline-item">
              <span>{step}</span>
              <div>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
            </article>
          ))}
        </div>
        <div className="code-block" aria-label="VeriGrant usage sample">
          <pre>{codeSample}</pre>
        </div>
      </section>

      <section className="section" id="architecture">
        <div className="section-heading">
          <p className="eyebrow">Architecture</p>
          <h2>Deterministic accounting, nondeterministic review.</h2>
        </div>
        <div className="feature-grid">
          <article>
            <h3>Flat Storage</h3>
            <p>
              Grants, milestones, and evidence use top-level arrays with explicit
              IDs, avoiding nested dynamic arrays while supporting interleaved
              grant activity.
            </p>
          </article>
          <article>
            <h3>Structured Review</h3>
            <p>
              Reviews normalize LLM output into decision, completion_bps,
              payout_bps, confidence, reason codes, evidence used, and summary.
            </p>
          </article>
          <article>
            <h3>Exact Escrow Binding</h3>
            <p>
              Validators must match payout_bps exactly before finalization can
              calculate an escrow transfer. Narrative metrics may vary within
              bounded policy rules, but the transfer amount cannot.
            </p>
          </article>
          <article>
            <h3>Consensus Boundary</h3>
            <p>
              Storage is snapshotted before run_nondet_unsafe. Leader and
              validator closures operate on plain data to avoid nondeterministic
              storage reads.
            </p>
          </article>
          <article>
            <h3>Escrow Liability</h3>
            <p>
              accounted_balance reports remaining internal liability as
              escrowed minus paid out minus refunded across all grants.
            </p>
          </article>
        </div>
      </section>

      <section className="section" id="api">
        <div className="section-heading">
          <p className="eyebrow">Contract API</p>
          <h2>Public methods exposed in Studio.</h2>
        </div>
        <div className="api-grid">
          <div>
            <h3>Write Methods</h3>
            <ul>
              {writeMethods.map(([name, body]) => (
                <li key={name}>
                  <code>{name}</code>
                  <span>{body}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Read Methods</h3>
            <ul>
              {readMethods.map(([name, body]) => (
                <li key={name}>
                  <code>{name}</code>
                  <span>{body}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="section" id="testing">
        <div className="section-heading">
          <p className="eyebrow">Bradbury Evidence</p>
          <h2>Corrected deployment verified on testnet.</h2>
        </div>
        <div className="test-grid">
          {tests.map((test) => (
            <article key={test.title}>
              <h3>{test.title}</h3>
              <p>{test.result}</p>
              <ul>
                {test.details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <p>
          The corrected Bradbury contract at {correctedContractAddress} matches
          commit 4e43896 byte-for-byte. Its placeholder-evidence path refunded
          the full escrow and its valid-evidence path paid the full escrow, with
          accounted_balance returning to zero after each finalization.
        </p>
      </section>

      <section className="section final-section" id="resources">
        <div className="section-heading">
          <p className="eyebrow">Resources</p>
          <h2>Source, docs, and proof.</h2>
        </div>
        <div className="resource-row">
          <a href="https://github.com/Manablaq/genlayer-verigrant">Repository</a>
          <a href="https://github.com/Manablaq/genlayer-verigrant/blob/main/docs/DEVELOPER_GUIDE.md">
            Developer Guide
          </a>
          <a href="https://github.com/Manablaq/genlayer-verigrant/blob/main/docs/TEST_REPORT.md">
            Test Report
          </a>
          <a href="https://github.com/Manablaq/genlayer-verigrant/blob/main/docs/REVIEW_RESPONSE_2026-08-13.md">
            Payout Consensus Correction
          </a>
          <a href="https://github.com/Manablaq/genlayer-verigrant/blob/main/contracts/veri_grant.py">
            Contract Source
          </a>
        </div>
      </section>
    </main>
  );
}
