/**
 * Writes the A–Z directory (browse-pages.mjs) from the pages this build already wrote: every
 * /skill/ page without a robots noindex (sub-skill pages included) and every /audit/ page, minus
 * the redirect pages left at old repository names. Reading dist/ instead of the catalog means the
 * directory lists exactly what the build published, with no extra Supabase read.
 *
 * Runs after the skill, sub-skill, redirect and audit generators and before generate-sitemap.mjs,
 * which lists the directory pages in sitemap-top.xml.
 *
 * Run: node scripts/generate-browse-pages.mjs  (after the page generators)
 */
import { closeSync, existsSync, mkdirSync, openSync, readSync, readdirSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { BROWSE_PATH, hubHtml, listHtml, paginate } from "./browse-pages.mjs";

const DIST = "dist";
const HEAD_BYTES = 8192;
const STUB = /http-equiv="refresh"/i;
const NOINDEX = /<meta name="robots" content="[^"]*noindex/i;

/** The first HEAD_BYTES of a file: enough for the <head> tags this script checks. */
function readHead(file) {
  const fd = openSync(file, "r");
  try {
    const buf = Buffer.alloc(HEAD_BYTES);
    const n = readSync(fd, buf, 0, HEAD_BYTES, 0);
    return buf.toString("utf-8", 0, n);
  } finally {
    closeSync(fd);
  }
}

const dirs = (path) => (existsSync(path) ? readdirSync(path, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name) : []);

/** owner/repo (and owner/repo/sub, depth 3) of every index.html under dist/<section>/. */
function pagesUnder(section, depth) {
  const names = [];
  const walk = (rel, level) => {
    for (const name of dirs(join(DIST, section, ...rel))) {
      const parts = [...rel, name];
      if (level >= 2 && existsSync(join(DIST, section, ...parts, "index.html"))) names.push(parts.join("/"));
      if (level < depth) walk(parts, level + 1);
    }
  };
  walk([], 1);
  return names;
}

/** Splits page names into those to list and the counts of those left out. */
function listable(section, names) {
  const keep = [];
  const left = { stub: 0, noindex: 0 };
  for (const name of names) {
    const head = readHead(join(DIST, section, ...name.split("/"), "index.html"));
    if (STUB.test(head)) left.stub++;
    else if (NOINDEX.test(head)) left.noindex++;
    else keep.push(name);
  }
  return { keep, left };
}

function write(path, html) {
  const dir = join(DIST, ...path.split("/").filter(Boolean));
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "index.html"), html);
}

function main() {
  // A rebuild on the same dist must not keep a letter page that no longer has links.
  rmSync(join(DIST, BROWSE_PATH), { recursive: true, force: true });
  const skills = listable("skill", pagesUnder("skill", 3));
  const audits = listable("audit", pagesUnder("audit", 2));
  const sections = { skills: paginate("skills", skills.keep), audits: paginate("audits", audits.keep) };
  write(BROWSE_PATH, hubHtml(sections));
  for (const pages of Object.values(sections)) for (const page of pages) write(page.path, listHtml(page, pages));
  const pageCount = 1 + sections.skills.length + sections.audits.length;
  console.log(`Directory: ${pageCount} pages under ${BROWSE_PATH}; ${skills.keep.length} skill links `
    + `(left out: ${skills.left.noindex} noindex, ${skills.left.stub} redirect pages), ${audits.keep.length} audit links `
    + `(left out: ${audits.left.stub} redirect pages, ${audits.left.noindex} noindex)`);
}

main();
