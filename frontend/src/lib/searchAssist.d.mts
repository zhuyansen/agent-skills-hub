export interface ScenarioLink {
  slug: string;
  en: string;
  zh: string;
}

export function githubRepoFromInput(input: string | null | undefined): string | null;
export function normalizeTerm(term: string | null | undefined): string;
export function correctTerm(term: string, vocab: readonly string[]): string | null;
export function scenarioForTerm(
  term: string,
  table: Readonly<Record<string, ScenarioLink>>,
): ScenarioLink | null;
