"""Build the Obsidian test vault and its 15 questions.

  python ops/obsidian-runs/make_vault.py     # writes in/input/vault, in/input/questions.md, truth.json

The questions follow LongMemEval's five abilities (ICLR 2025, arXiv 2410.10813), three
each: finding one fact, reasoning across notes, reasoning about time, keeping up with an
update (an older note says one thing, a later note changes it), and abstaining when the
vault does not hold the answer. The vault is about 560 Markdown notes with wikilinks and
frontmatter: daily notes, projects, meetings, people, filler that never matters, and near
misses (a second project with its own budget and moved launch, another price rise).
truth.json stays outside in/, so the sandbox never sees the answers.
"""
import json
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
VAULT = HERE / "in" / "input" / "vault"
random.seed(7)
FILLER_DAYS, FILLER_MEETINGS = 480, 50   # January 2025 to late April 2026

PEOPLE = {"Mira Okafor": "designer", "Jonas Field": "backend engineer", "Priya Raman": "product lead",
          "Tomasz Lind": "data analyst", "Elena Voss": "customer support lead", "Dev Mehta": "mobile engineer"}
TOPICS = ["onboarding flow", "billing page", "search latency", "export feature", "dark mode", "invoice emails",
          "API rate limits", "mobile crashes", "pricing experiment", "support backlog", "weekly digest", "team offsite"]

# Notes that carry the answers. (path, frontmatter dict, body)
KEY = [
    ("Projects/Harbor.md", {"status": "active", "owner": "Priya Raman"},
     "# Harbor\n\nRebuild of the customer dashboard. Owner: [[Priya Raman]]. Design by [[Mira Okafor]].\n\n- Budget approved: 48,000 euros.\n- Launch target: see [[2026-03-02 Harbor kickoff]].\n"),
    ("Meetings/2026-03-02 Harbor kickoff.md", {"date": "2026-03-02", "type": "meeting"},
     "# Harbor kickoff\n\nAttendees: [[Priya Raman]], [[Mira Okafor]], [[Jonas Field]].\n\n- Launch target set for 15 May 2026.\n- [[Jonas Field]] will migrate the reports API first.\n- Staging URL: harbor-staging.example.invalid\n"),
    ("Meetings/2026-04-20 Harbor review.md", {"date": "2026-04-20", "type": "meeting"},
     "# Harbor review\n\nThe reports API migration slipped two weeks. **Launch moved from 15 May to 9 June 2026.** [[Priya Raman]] informed sales.\n\nBudget unchanged.\n"),
    ("People/Mira Okafor.md", {"role": "designer"},
     "# Mira Okafor\n\nDesigner. Based in Lisbon. Works Tuesday to Friday.\n\nPrefers feedback as comments in Figma, not in chat.\n"),
    ("People/Jonas Field.md", {"role": "backend engineer"},
     "# Jonas Field\n\nBackend engineer. On call every second week. Manager: [[Priya Raman]].\n\nAllergic to peanuts (relevant for team lunches).\n"),
    ("Projects/Lantern.md", {"status": "paused", "owner": "Tomasz Lind"},
     "# Lantern\n\nUsage analytics pipeline. Owner: [[Tomasz Lind]]. Paused on 2026-02-10 until Harbor ships.\n\nWarehouse: we chose ClickHouse over BigQuery, see [[2026-01-14 Lantern warehouse decision]].\n"),
    ("Meetings/2026-01-14 Lantern warehouse decision.md", {"date": "2026-01-14", "type": "meeting"},
     "# Lantern warehouse decision\n\nDecision: ClickHouse. Reasons: query cost at our volume and self-hosting on the existing cluster.\n\nRejected: BigQuery (per-query cost), Postgres (too slow past 200 million rows).\n"),
    ("Daily/2026-02-03.md", {"date": "2026-02-03"},
     "# 2026-02-03\n\n- Renewed the domain; the registrar account is under [[Elena Voss]]'s work email.\n- Vendor call: the SMS provider raises prices on 1 April, from 0.04 to 0.055 euros per message.\n"),
    ("Daily/2026-03-18.md", {"date": "2026-03-18"},
     "# 2026-03-18\n\n- Switched SMS provider to Corvid after the price rise. New price: 0.031 euros per message.\n- [[Dev Mehta]] shipped the Android crash fix (build 4.12.1).\n"),
    ("Daily/2026-04-02.md", {"date": "2026-04-02"},
     "# 2026-04-02\n\n- Support backlog: 212 open tickets. [[Elena Voss]] wants it under 80 before the offsite.\n- Offsite booked: 21 to 23 May in Porto.\n"),
    ("Daily/2026-05-06.md", {"date": "2026-05-06"},
     "# 2026-05-06\n\n- Support backlog down to 64 open tickets.\n- Offsite moved to Braga, same dates; the Porto venue cancelled.\n"),
    ("Reference/Team rituals.md", {},
     "# Team rituals\n\n- Planning: Mondays 10:00.\n- Demo: every second Thursday 15:00.\n- Retro: last Friday of the month.\n"),
]

# Near misses: the same kind of fact about something else, so a search has to tell them apart.
DISTRACT = [
    ("Projects/Beacon.md", {"status": "active", "owner": "Tomasz Lind"},
     "# Beacon\n\nPartner portal. Owner: [[Tomasz Lind]]. Budget approved: 84,000 euros.\n\nLaunch target: 30 June 2026, see [[2026-02-16 Beacon kickoff]].\n"),
    ("Meetings/2026-02-16 Beacon kickoff.md", {"date": "2026-02-16", "type": "meeting"},
     "# Beacon kickoff\n\nAttendees: [[Tomasz Lind]], [[Dev Mehta]].\n\n- Launch target set for 30 June 2026.\n- [[Dev Mehta]] will build the partner login first.\n"),
    ("Meetings/2026-04-27 Beacon review.md", {"date": "2026-04-27", "type": "meeting"},
     "# Beacon review\n\nPartner login is late. **Launch moved from 30 June to 14 July 2026.**\n"),
    ("Daily/2026-04-10.md", {"date": "2026-04-10"},
     "# 2026-04-10\n\n- Engineering backlog: 97 open issues. Not the support queue.\n- Email provider raises prices on 1 May, from 0.90 to 1.10 euros per thousand emails.\n"),
    ("Reference/Offsites.md", {},
     "# Offsites\n\n- 2024: Valencia.\n- 2025: Seville, 14 to 16 May.\n- 2026: see the daily notes.\n"),
    ("People/Tomasz Lind.md", {"role": "data analyst"},
     "# Tomasz Lind\n\nData analyst. Owns [[Lantern]] and [[Beacon]]. Email: tomasz@example.invalid. Works from Gdansk.\n"),
    ("Projects/Harbor budget notes.md", {"tags": "finance"},
     "# Harbor budget notes\n\nFirst ask was 60,000 euros; finance cut it. The approved figure is on [[Harbor]]. Spend is tracked in the finance system, not here.\n"),
]

QUESTIONS = [
    # (ability, question, answer the judge checks against)
    ("extraction", "What budget was approved for the Harbor project?", "48,000 euros."),
    ("extraction", "Which warehouse did the team choose for Lantern?", "ClickHouse."),
    ("extraction", "How does Mira Okafor prefer to receive feedback?", "As comments in Figma, not in chat."),
    ("multi-note", "Who is the manager of the engineer who was assigned to migrate the reports API for Harbor?", "Priya Raman (Jonas Field migrates the reports API; his manager is Priya Raman)."),
    ("multi-note", "Lantern is paused until another project ships. Who owns that other project?", "Priya Raman (Lantern is paused until Harbor ships; Harbor's owner is Priya Raman)."),
    ("multi-note", "The registrar account is under one person's email. What is that person's role?", "Customer support lead (Elena Voss)."),
    ("temporal", "Which happened first: the Lantern warehouse decision or the Harbor kickoff?", "The Lantern warehouse decision (14 January 2026), before the Harbor kickoff (2 March 2026)."),
    ("temporal", "How many days passed between the Harbor kickoff and the Harbor review?", "49 days (2 March to 20 April 2026)."),
    ("temporal", "By how many open tickets did the support backlog fall between 2 April and 6 May 2026?", "By 148 tickets (212 on 2 April to 64 on 6 May 2026)."),
    ("update", "When is Harbor's launch date?", "9 June 2026 (moved from 15 May at the 20 April review)."),
    ("update", "What does the team currently pay per SMS?", "0.031 euros per message (switched to Corvid on 18 March 2026; the older provider's 0.04 and 0.055 no longer apply)."),
    ("update", "Where is the team offsite?", "Braga, 21 to 23 May (moved from Porto after the venue cancelled)."),
    ("abstain", "What is Tomasz Lind's phone number?", "Not in the vault; the correct answer is that the notes do not say."),
    ("abstain", "How much did the Harbor project actually spend?", "Not in the vault; only the approved budget (48,000 euros) is recorded, not the spend."),
    ("abstain", "Which CI system does the team use?", "Not in the vault; the notes do not say."),
]


def fm(d: dict) -> str:
    return ("---\n" + "".join(f"{k}: {v}\n" for k, v in d.items()) + "---\n\n") if d else ""


def filler() -> list[tuple[str, dict, str]]:
    notes, start = [], date(2025, 1, 6)
    names = list(PEOPLE)
    taken = {path for path, _, _ in KEY + DISTRACT}
    for i in range(FILLER_DAYS):   # daily notes that never hold an answer
        d = start + timedelta(days=i)
        if f"Daily/{d.isoformat()}.md" in taken:
            continue
        a, b = random.sample(names, 2)
        t1, t2 = random.sample(TOPICS, 2)
        body = (f"# {d.isoformat()}\n\n- Talked with [[{a}]] about the {t1}; no decision yet.\n"
                f"- [[{b}]] is looking into the {t2}.\n- Inbox at {random.randint(3, 40)} unread.\n")
        notes.append((f"Daily/{d.isoformat()}.md", {"date": d.isoformat()}, body))
    for name, role in PEOPLE.items():
        if f"People/{name}.md" not in taken:
            notes.append((f"People/{name}.md", {"role": role}, f"# {name}\n\n{role.capitalize()}.\n"))
    for i, t in enumerate(TOPICS):
        notes.append((f"Notes/{t.title()}.md", {"tags": "idea"},
                      f"# {t.title()}\n\nLoose thoughts on the {t}. Nothing decided. See also [[{random.choice(TOPICS).title()}]].\n"))
    for i in range(FILLER_MEETINGS):
        d = date(2025, 1, 9) + timedelta(days=9 * i)
        t = random.choice(TOPICS)
        notes.append((f"Meetings/{d.isoformat()} {t} sync.md", {"date": d.isoformat(), "type": "meeting"},
                      f"# {t} sync\n\nAttendees: [[{random.choice(names)}]], [[{random.choice(names)}]].\n\n- Reviewed the {t}. Follow up next time.\n"))
    return notes


def main() -> None:
    shutil.rmtree(VAULT, ignore_errors=True)
    notes = KEY + DISTRACT + filler()
    for path, front, body in notes:
        f = VAULT / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(fm(front) + body)
    (VAULT / ".obsidian").mkdir(exist_ok=True)
    (VAULT / ".obsidian" / "app.json").write_text("{}\n")
    qs = "\n".join(f"{n}. {q}" for n, (_, q, _) in enumerate(QUESTIONS, 1))
    (HERE / "in" / "input" / "questions.md").write_text(qs + "\n")
    (HERE / "truth.json").write_text(json.dumps([{"n": n, "ability": a, "question": q, "answer": ans}
                                                 for n, (a, q, ans) in enumerate(QUESTIONS, 1)], indent=1))
    print(f"{len(notes)} notes, {len(QUESTIONS)} questions -> {VAULT}")


if __name__ == "__main__":
    main()
