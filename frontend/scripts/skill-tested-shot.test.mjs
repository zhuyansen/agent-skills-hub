/**
 * shotFor in scripts/skill-tested.mjs: the picture of what a tool made that the "Tested by
 * Agent Skills Hub" block on its /skill/ page shows.
 *
 * Run: node --test scripts/skill-tested-shot.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { shotFor, testedEntries, testedHtml } from "./skill-tested.mjs";

const there = () => true;
const missing = () => false;

test("a result that is itself a picture (the PPT slide sheet) is the shot", () => {
  const run = { dir: "/best-runs/ppt/" };
  assert.deepEqual(shotFor("ppt-presentation", run, { sheet: "a__b.jpg" }, missing),
    { src: "/best-runs/ppt/a__b.jpg", w: 1200, h: 675 });
});

test("video, 3D and interface tests show the picture saved beside the result page", () => {
  assert.deepEqual(shotFor("claude-video-skills", { dir: "/best-runs/video/" }, { sheet: "a__b.html" }, there),
    { src: "/best-runs/video/a__b.jpg", w: 640, h: 360 });
  assert.deepEqual(shotFor("3d-mcp", { dir: "/best-runs/3d/" }, { sheet: "a__b.html" }, there),
    { src: "/best-runs/3d/a__b.webp", w: 640, h: 480 });
  assert.deepEqual(shotFor("anti-slop-ui", { dir: "/best-runs/slop-ui/" }, { sheet: "a__b.html" }, there),
    { src: "/best-runs/slop-ui/a__b-fold.webp", w: 640, h: 400 });
});

test("no picture on disk, no shot", () => {
  assert.equal(shotFor("3d-mcp", { dir: "/best-runs/3d/" }, { sheet: "a__b.html" }, missing), null);
});

test("the image test shows its strip of six pictures at the size it was saved", () => {
  const r = { sheet: "a__b.html", strip: { src: "strips/a__b.webp", w: 264, h: 42 } };
  assert.deepEqual(shotFor("image-generation", { dir: "/best-runs/image/" }, r, missing),
    { src: "/best-runs/image/strips/a__b.webp", w: 528, h: 84 });
});

test("a test with nothing to look at (code review) has no shot", () => {
  assert.equal(shotFor("code-review", { dir: "/best-runs/review/" }, { sheet: "a__b.html" }, there), null);
});

test("real pages: a video pick and a 3D tool get a picture in the block", () => {
  const video = testedEntries("vincentsch/explainroo");
  assert.equal(video[0].evidence.shot.src, "/best-runs/video/vincentsch__explainroo.jpg");
  assert.match(testedHtml(video), /<img src="\/best-runs\/video\/vincentsch__explainroo\.jpg"[^>]* width="640" height="360"/);
  assert.equal(testedEntries("CloudAI-X/threejs-skills")[0].evidence.shot.w, 640);
});
