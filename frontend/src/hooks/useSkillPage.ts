import { useEffect, useReducer, type Dispatch } from "react";
import { useNavigate } from "react-router-dom";
import { fetchSkillBySlug, fetchSkillDetail } from "../api/client";
import { fetchSkillRedirect } from "../api/skillRedirects";
import {
  loadingSkillPage, skillPageFor, skillPageReducer,
  type SkillPageEvent, type SkillPageState,
} from "../lib/skillPageState.mjs";
import type { SkillDetail } from "../types/skill";

type State = SkillPageState<SkillDetail>;
type Event = SkillPageEvent<SkillDetail>;
const reduce = (state: State, event: Event): State => skillPageReducer(state, event);

const NUMERIC_ID = /^\d+$/;
const isRepoName = (key: string) => key.includes("/");
const messageOf = (err: unknown) => (err instanceof Error ? err.message : String(err));

/** /skill/:id takes a numeric id or a slug; /skill/:owner/:repo is a slug. */
function fetchSkill(key: string): Promise<SkillDetail> {
  return NUMERIC_ID.test(key) ? fetchSkillDetail(Number(key)) : fetchSkillBySlug(key);
}

/** The name a renamed repository has now (backend/renamed_repos.py), or null. */
async function movedTo(key: string): Promise<string | null> {
  if (!isRepoName(key)) return null;
  try {
    return await fetchSkillRedirect(key);
  } catch {
    return null;
  }
}

async function load(key: string, dispatch: Dispatch<Event>) {
  try {
    dispatch({ type: "loaded", key, detail: await fetchSkill(key) });
  } catch (err) {
    const to = await movedTo(key);
    dispatch(to ? { type: "moved", key, to } : { type: "failed", key, message: messageOf(err) });
  }
}

/** The state of the skill page for these route params (lib/skillPageState.mjs). */
export function useSkillPage(id?: string, owner?: string, repo?: string): State {
  const key = owner && repo ? `${owner}/${repo}` : (id ?? "");
  const [state, dispatch] = useReducer(reduce, key, loadingSkillPage);
  const navigate = useNavigate();
  const page = skillPageFor(state, key);
  const movedToName = page.kind === "redirecting" ? page.to : null;

  useEffect(() => {
    if (!key) return;
    dispatch({ type: "requested", key });
    window.scrollTo(0, 0);
    void load(key, dispatch);
  }, [key]);

  useEffect(() => {
    if (movedToName) navigate(`/skill/${movedToName}/`, { replace: true });
  }, [movedToName, navigate]);

  return page;
}
