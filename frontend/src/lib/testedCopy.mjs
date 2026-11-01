/**
 * Wording of the "Tested by Agent Skills Hub" block on a skill page, shared by the static
 * page (scripts/skill-tested.mjs) and the React page (components/TestedByUs.tsx), so the
 * two say the same thing. A plain module so the Node page generators can import it too.
 * Every export is an [English, Chinese] pair, or a function returning one (null when the
 * entry has nothing to say there). The entry shape is TestedEntry in testedCopy.d.mts.
 */

export const TESTED_TITLE = ["Tested by Agent Skills Hub", "我们实测过"];
export const TESTED_SEE_ALL = ["See the whole test →", "看完整实测 →"];
export const TESTED_IMAGE_ALT = ["What it made in our test", "它在实测里做出来的东西"];

export function testedIntro(e) {
  return [`One of ${e.tested} tools we ran end to end on the same task for our ${e.pageTitle[0]} page (${e.date}).`,
    `${e.date}，我们在「${e.pageTitle[1]}」页把 ${e.tested} 个工具用同一个任务从头跑了一遍，它是其中之一。`];
}

/** Its place in the page's list of the best by our test ("The 5 best PPT skills ..."). */
export function testedTop(e) {
  if (!e.top) return null;
  return [`No. ${e.top.place} in "${e.top.title[0]}".`, `「${e.top.title[1]}」第 ${e.top.place} 名。`];
}

/** Our pick for a situation: "For a PowerPoint file a colleague will edit" reads "Our pick for a ...". */
export function testedPick(e) {
  if (!e.pick) return null;
  const [role, roleZh] = e.pick.role;
  const lead = /^For /.test(role) ? `Our pick ${role.replace(/^For /, "for ")}` : `Our pick (${role})`;
  return [`${lead}: ${e.pick.why[0]}`, `我们的推荐（${roleZh}）：${e.pick.why[1]}`];
}

export function testedResult(e) {
  return [`Result: ${e.bits.map((b) => b[0]).join(" · ")}`, `结果：${e.bits.map((b) => b[1]).join(" · ")}`];
}
