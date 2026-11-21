import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { videoLd, videoUploadDate } from "./scenario-video.mjs";

// Google's VideoObject report wants a date, a time and a UTC offset (2026-11-20, URL
// Inspection on /best/claude-video-skills/ and /best/ppt-presentation/: "uploadDate is
// missing a timezone", "Invalid datetime value").
const WITH_OFFSET = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$/;

const ldOf = (scenario) => JSON.parse(videoLd(scenario).match(/<script[^>]*>\n([\s\S]*?)\n\s*<\/script>/)[1]);

test("videoUploadDate keeps a full timestamp as written", () => {
  assert.equal(videoUploadDate("2026-10-06T00:36:34-07:00"), "2026-10-06T00:36:34-07:00");
  assert.equal(videoUploadDate("2026-10-06T07:36:34Z"), "2026-10-06T07:36:34Z");
});

test("videoUploadDate turns a bare date into midnight UTC", () => {
  assert.equal(videoUploadDate("2026-10-06"), "2026-10-06T00:00:00+00:00");
});

test("videoUploadDate takes the other ways a full timestamp is written", () => {
  assert.equal(videoUploadDate("2026-10-06T07:36:34.000Z"), "2026-10-06T07:36:34.000Z");
  assert.equal(videoUploadDate("2026-10-06T07:36:34+0000"), "2026-10-06T07:36:34+0000");
});

test("videoUploadDate gives null for anything that is not a date", () => {
  assert.equal(videoUploadDate("October 6"), null);
  assert.equal(videoUploadDate(undefined), null);
});

// A typo in one date must not stop the deploy: the build chain ends at the first script that throws.
test("videoLd leaves out a date it cannot read, and still writes the rest", (t) => {
  t.mock.method(console, "warn", () => {});
  const ld = ldOf({ slug: "x", video: { id: "abc", title: "T", uploadDate: "soon", duration: "PT2M4S" } });
  assert.equal(ld["@type"], "VideoObject");
  assert.ok(!("uploadDate" in ld));
  assert.equal(ld.duration, "PT2M4S");
  assert.equal(console.warn.mock.callCount(), 1);
});

test("videoLd writes an uploadDate with a time and an offset", () => {
  const ld = ldOf({ video: { id: "abc", title: "T", uploadDate: "2026-10-06", duration: "PT2M4S" } });
  assert.equal(ld["@type"], "VideoObject");
  assert.match(ld.uploadDate, WITH_OFFSET);
});

test("videoLd is empty when the scenario has no video", () => {
  assert.equal(videoLd({}), "");
});

test("every video in scenario-keywords.json states when it was published, to the second", () => {
  const scenarios = JSON.parse(readFileSync(new URL("./scenario-keywords.json", import.meta.url), "utf-8"));
  const videos = scenarios.filter((s) => s.video);
  assert.ok(videos.length > 0, "expected at least one scenario with a video");
  for (const s of videos) assert.match(s.video.uploadDate, WITH_OFFSET, `${s.slug}: ${s.video.uploadDate}`);
});
