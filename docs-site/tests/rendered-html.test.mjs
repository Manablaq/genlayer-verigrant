import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the exact-payout correction status", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>VeriGrant Documentation<\/title>/i);
  assert.match(html, /EXACT PAYOUT/);
  assert.match(html, /REDEPLOY REQUIRED/);
  assert.match(html, /HISTORICAL SOURCE/);
  assert.match(html, /Validators must match payout_bps exactly/);
  assert.match(html, /0x6CD27E9823dE3B7293AeC9C848cF0e1C131D54c9/);
  assert.doesNotMatch(html, /payout_bps differs by no more than 500/i);
});

test("keeps the deployed-address status unambiguous in both site sources", async () => {
  const [page, staticHtml] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../index.html", import.meta.url), "utf8"),
  ]);

  for (const source of [page, staticHtml]) {
    assert.match(source, /HISTORICAL SOURCE/);
    assert.match(source, /exact payout agreement/);
    assert.doesNotMatch(source, /V1 HISTORICAL/);
    assert.doesNotMatch(source, /payout_bps differs by no more than 500/i);
  }

  assert.doesNotMatch(page, /historicalDeploymentTx/);
});
