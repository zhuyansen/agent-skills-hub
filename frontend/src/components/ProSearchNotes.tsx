// Notes for /pro/ searches that stop at the server's time budget (migrations
// 038 and 042): either some rows came back flagged incomplete_results, or the
// search stopped before finding any (search_incomplete, or a timeout).

interface NoteProps {
  zh: boolean;
  filters: { query: string; category: string; grade: string };
}

const NOTE_CLASS =
  "mb-3 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/30 px-3 py-2 text-sm text-amber-700 dark:text-amber-400";

// Only what makes the search cheaper: a filter not yet set, or dropping the
// quotes (a phrase is checked row by row; the same words without quotes are not).
function narrowingSteps({ zh, filters }: NoteProps): string[] {
  const steps: string[] = [];
  if (!filters.category) steps.push(zh ? "选一个分类" : "pick a category");
  if (!filters.grade) steps.push(zh ? "选一个评级" : "pick a grade");
  if (filters.query.includes('"'))
    steps.push(
      zh
        ? "去掉引号(不再要求词语相邻)"
        : "remove the quotes (the words then need not be adjacent)",
    );
  if (steps.length === 0)
    steps.push(zh ? "换一个更具体的词" : "use a more specific word");
  return steps;
}

function joinSteps(steps: string[], zh: boolean): string {
  const last = steps[steps.length - 1];
  if (steps.length === 1) return last;
  const head = steps.slice(0, -1).join(zh ? "、" : ", ");
  if (zh) return `${head}或${last}`;
  return steps.length === 2 ? `${head} or ${last}` : `${head}, or ${last}`;
}

export function IncompleteResultsNote({
  count,
  ...props
}: NoteProps & { count: number }) {
  const steps = joinSteps(narrowingSteps(props), props.zh);
  return (
    <p role="status" className={NOTE_CLASS}>
      {props.zh
        ? `结果可能不完整:这次搜索到了时间上限,只列出了已找到的星数最高的 ${count} 条。${steps},更容易拿到完整结果。`
        : `Results may be incomplete: this search hit its time limit, so only the ${count} most-starred matches it found are listed. To get the full list, ${steps}.`}
    </p>
  );
}

export function SearchTooSlowNote(props: NoteProps) {
  const steps = joinSteps(narrowingSteps(props), props.zh);
  const capitalized = steps.charAt(0).toUpperCase() + steps.slice(1);
  return (
    <p role="status" className={`mt-6 ${NOTE_CLASS}`}>
      {props.zh
        ? `这次搜索到了时间上限,还没找到结果,不代表没有匹配。${steps}后再搜一次。`
        : `This search hit its time limit before it found a match, which doesn't mean there are none. ${capitalized} and search again.`}
    </p>
  );
}
