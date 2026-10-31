/**
 * Renames the repositories the curated /best/ files name (scenario-keywords.json, the kinds map
 * and the description maps) to their current GitHub names, from skill_redirects
 * (scripts/skill-redirects.mjs). A featured repository under its old name drops off its page once
 * backend/renamed_repos.py removes the old row, and an excluded one comes back under the new name.
 *
 * Run it after backend/renamed_repos.py --apply and commit the files. The renamed-repos workflow
 * runs it with --check, which writes nothing and fails while a curated file names an old name.
 *
 * Run: node scripts/rename-curated.mjs [--check]
 */
import { readFileSync, writeFileSync } from "fs";
import { basename } from "path";
import { fetchSkillRedirects, renameMap, renameNames, curatedJson, CURATED_FILES } from "./skill-redirects.mjs";

const check = process.argv.includes("--check");
const renames = renameMap(await fetchSkillRedirects());
let found = 0;
for (const file of CURATED_FILES) {
  const changes = [];
  const data = renameNames(JSON.parse(readFileSync(file, "utf-8")), renames, changes);
  if (!changes.length) continue;
  found += changes.length;
  console.log(`${basename(file)}: ${changes.map(([from, to]) => `${from} -> ${to}`).join(", ")}`);
  if (!check) writeFileSync(file, curatedJson(data));
}
if (!found) console.log("The curated files name no old repository names.");
else if (check) console.log(`${found} old names: run node frontend/scripts/rename-curated.mjs and commit the files.`);
else console.log(`${found} names renamed: commit the files.`);
process.exitCode = check && found ? 1 : 0;
