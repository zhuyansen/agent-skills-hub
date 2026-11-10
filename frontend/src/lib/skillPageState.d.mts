export type SkillPageState<T> =
  | { kind: "loading"; key: string }
  | { kind: "ready"; key: string; detail: T }
  | { kind: "redirecting"; key: string; to: string }
  | { kind: "failed"; key: string; message: string };
export type SkillPageEvent<T> =
  | { type: "requested"; key: string }
  | { type: "loaded"; key: string; detail: T }
  | { type: "moved"; key: string; to: string }
  | { type: "failed"; key: string; message: string };
export function loadingSkillPage(key: string): { kind: "loading"; key: string };
export function skillPageReducer<T>(state: SkillPageState<T>, event: SkillPageEvent<T>): SkillPageState<T>;
export function skillPageFor<T>(state: SkillPageState<T>, key: string): SkillPageState<T>;
