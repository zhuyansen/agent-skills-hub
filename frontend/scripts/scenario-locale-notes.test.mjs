import { test } from "node:test";
import assert from "node:assert/strict";
import { localeNotesHtml } from "./scenario-locale-notes.mjs";

test("no locale notes, nothing written", () => {
  assert.equal(localeNotesHtml({}), "");
});

test("a note carries its language, heading, paragraphs and questions, escaped", () => {
  const html = localeNotesHtml({ locale_notes: [{ lang: "id", heading: "Ringkasan", paragraphs: ["Satu <b>"], faq: [{ q: "Apa?", a: "Itu & ini" }] }] });
  assert.match(html, /<section lang="id"/);
  assert.match(html, /Ringkasan<\/h2>/);
  assert.match(html, /Satu &lt;b&gt;/);
  assert.match(html, /<summary[^>]*>Apa\?<\/summary>/);
  assert.match(html, /Itu &amp; ini/);
});
