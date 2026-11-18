import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { analyticsTags, extractAssetTags } from "./shared-utils.mjs";

const ROOT = new URL("..", import.meta.url).pathname;

function htmlFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...htmlFiles(p));
    else if (name.endsWith(".html")) out.push(p);
  }
  return out;
}

test("index.html and analyticsTags() both emit GA4, Clarity, and /ph.js", () => {
  const indexHtml = readFileSync(join(ROOT, "index.html"), "utf-8");
  const staticTags = analyticsTags();
  for (const snippet of ["/ph.js", "clarity.ms", "G-0F5GCX6MCV"]) {
    assert.ok(indexHtml.includes(snippet), `index.html missing ${snippet}`);
    assert.ok(staticTags.includes(snippet), `analyticsTags() missing ${snippet}`);
  }
  const { scriptTags } = extractAssetTags(indexHtml);
  assert.ok(
    scriptTags.some((t) => t.includes("/ph.js")),
    "extractAssetTags(index.html) must carry /ph.js into A-class static generators",
  );
});

test("static public/*.html files load /ph.js and have no dead plausible.io tags", () => {
  const files = htmlFiles(join(ROOT, "public"));
  assert.ok(files.length > 0);
  for (const f of files) {
    const html = readFileSync(f, "utf-8");
    assert.equal(html.includes("plausible.io"), false, `${f} still references plausible.io`);
  }
});
