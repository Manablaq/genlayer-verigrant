import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const RPC_URL = "https://rpc-bradbury.genlayer.com";
const CONTRACT_ADDRESS = process.env.VERIGRANT_CONTRACT_ADDRESS;
const DEPLOYMENT_TX = process.env.VERIGRANT_DEPLOYMENT_TX;
const SOURCE_COMMIT = process.env.VERIGRANT_SOURCE_COMMIT;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(CONTRACT_ADDRESS, "VERIGRANT_CONTRACT_ADDRESS is required");
assert(DEPLOYMENT_TX, "VERIGRANT_DEPLOYMENT_TX is required");
assert(SOURCE_COMMIT, "VERIGRANT_SOURCE_COMMIT is required");

async function rpc(method, params) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
  });
  assert(response.ok, `Bradbury RPC returned HTTP ${response.status}`);
  const payload = await response.json();
  if (payload.error) throw new Error(`${payload.error.code}: ${payload.error.message}`);
  return payload.result;
}

const contractPath = fileURLToPath(new URL("../contracts/veri_grant.py", import.meta.url));
const repositorySource = await readFile(contractPath);
const receipt = await rpc("gen_getTransactionReceipt", [{ txId: DEPLOYMENT_TX }]);

assert(receipt, "Deployment transaction was not found");
assert(receipt.result === 1, `Consensus result is ${receipt.result}, expected AGREE (1)`);
assert(
  receipt.txExecutionResult === 1,
  `Execution result is ${receipt.txExecutionResult}, expected FINISHED_WITH_RETURN (1)`,
);
assert(
  receipt.recipient?.toLowerCase() === CONTRACT_ADDRESS.toLowerCase(),
  `Receipt recipient ${receipt.recipient} does not match ${CONTRACT_ADDRESS}`,
);

const transactionBytes = Buffer.from(receipt.txCallData, "hex");
const sourceStart = transactionBytes.indexOf(Buffer.from('# { "Depends"'));
assert(sourceStart >= 0, "Could not locate Python source in deployment calldata");
const deployedSource = transactionBytes.subarray(sourceStart, sourceStart + repositorySource.length);
assert(deployedSource.equals(repositorySource), "Deployed source does not match contracts/veri_grant.py byte-for-byte");

console.log(JSON.stringify({
  network: "Bradbury",
  contractAddress: CONTRACT_ADDRESS,
  deploymentTransaction: DEPLOYMENT_TX,
  sourceCommit: SOURCE_COMMIT,
  receiptStatus: receipt.status,
  consensus: "AGREE",
  execution: "FINISHED_WITH_RETURN",
  sourceMatchesRepository: true,
  sourceBytes: repositorySource.length,
  sourceSha256: createHash("sha256").update(repositorySource).digest("hex"),
}, null, 2));
