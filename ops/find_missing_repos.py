"""Diff GitHub's top repos in our categories against the catalog.

Why this exists (2026-08-20): three coverage gaps surfaced by hand in three
days — hugohe3/ppt-master (47,547 stars, absent), s1dashu/ip-as-logo-skill
(recorded 46 stars against GitHub's 562), only-cli/oc (56 stars, absent). Each
was found by a person noticing, not by the pipeline.

Sync discovers repos through a fixed set of GitHub search queries. Anything the
queries do not phrase its way never enters the catalog, and nothing measures
what is being missed. The first run of this script found 201 of 711 matches
absent — a 28% gap that included google/skills (18,520) and
openai/codex-plugin-cc (32,065). For a directory whose whole claim is
completeness, first-party repos from Google and OpenAI being absent is not a
long-tail problem.

Run periodically; it writes the diff and never mutates the catalog. Ingestion is
a separate, reviewed step via extra_repos.

NOTE on filtering the results: match keywords by SUBSTRING, not \\b word
boundaries. Chinese characters and underscores are word characters in Python's
Unicode \\b, so "多agent实现" and "servasyy_skills" both fail a \\bagent\\b /
\\bskills\\b test — three in-domain repos were wrongly filtered out that way on
the first pass.
"""
import json, os, subprocess, time, urllib.request, urllib.error
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
def github_token():
    """Env first, gh CLI second — and verify before using either.

    CI has GITHUB_TOKEN and no gh login; a laptop has the reverse, and its
    backend/.env may carry an expired token that `gh` will happily echo back
    because it honours GH_TOKEN/GITHUB_TOKEN from the environment. Assuming one
    or the other is how sync stayed broken for two days on 2026-08-06.
    """
    clean = {k: v for k, v in os.environ.items()
             if k not in ('GH_TOKEN', 'GITHUB_TOKEN')}
    candidates = [('GITHUB_TOKEN env', os.environ.get('GITHUB_TOKEN', ''))]
    try:
        candidates.append(('gh auth token', subprocess.run(
            ['gh', 'auth', 'token'], capture_output=True, text=True,
            env=clean, timeout=10).stdout.strip()))
    except (OSError, subprocess.SubprocessError):
        pass
    for label, t in candidates:
        if not t:
            continue
        try:
            req = urllib.request.Request(
                'https://api.github.com/rate_limit',
                headers={'Authorization': f'Bearer {t}'})
            remaining = json.load(urllib.request.urlopen(req, timeout=15))[
                'resources']['search']['remaining']
            print(f"使用 {label}(search 额度剩余 {remaining})", flush=True)
            return t
        except Exception:
            print(f"跳过 {label}:GitHub 拒绝或网络不通", flush=True)
    raise SystemExit('没有可用的 GitHub token')


tok = github_token()

QUERIES = [
    'agent+skill+in:name,description+stars:>200',
    'claude+skill+in:name,description+stars:>200',
    'codex+skill+in:name,description+stars:>200',
    'mcp+server+in:name,description+stars:>300',
    'ppt+skill+in:name,description+stars:>100',
    'powerpoint+skill+in:name,description+stars:>100',
    'slides+skill+in:name,description+stars:>100',
    '"for+AI+agents"+in:description+stars:>300',
    'agent+cli+in:name,description+stars:>300',
    'claude+code+in:name,description+stars:>500',
    'openclaw+in:name,description+stars:>100',
    'skills+in:name+stars:>500',
]

found = {}
for q in QUERIES:
    for page in (1, 2):
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=50&page={page}"
        try:
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
            items = json.load(urllib.request.urlopen(req, timeout=30)).get('items', [])
        except Exception as e:
            print(f"  query failed ({q[:28]}): {type(e).__name__}", flush=True)
            break
        if not items:
            break
        for i in items:
            found[i['full_name']] = i
        time.sleep(2)          # search API: 30 req/min
    print(f"  扫完 {q[:34]:<36} 累计 {len(found)}", flush=True)

conn = psycopg2.connect(os.environ['SUPABASE_DB_URL'], connect_timeout=30)
cur = conn.cursor()
cur.execute("SELECT lower(repo_full_name) FROM skills")
have = {r[0] for r in cur.fetchall()}
# Every status counts as "known", including 'rejected'. Keyword search returns
# false positives — a Linux sysadmin quiz, a conference-deadline tracker — and
# without somewhere to record that decision the weekly alert would re-report
# them forever and stop being read. Marking one rejected in extra_repos is how
# you tell this scan "we looked, it is not a skill".
cur.execute("SELECT lower(full_name) FROM extra_repos")
have |= {r[0] for r in cur.fetchall()}
conn.close()

missing = [v for k, v in found.items() if k.lower() not in have]
missing.sort(key=lambda i: -i['stargazers_count'])
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT_DIR, exist_ok=True)
rows = [{'full_name': i['full_name'], 'stars': i['stargazers_count'],
         'description': i['description']} for i in missing]
json.dump(rows, open(os.path.join(OUT_DIR, 'missing-repos.json'), 'w'),
          ensure_ascii=False, indent=1)

# Machine-readable summary so the workflow can decide whether to raise an issue
# without re-parsing human output.
big = [r for r in rows if r['stars'] >= 5000]
summary = {'scanned': len(found), 'missing': len(missing),
           'missing_over_5k': len(big),
           'top': rows[:20]}
json.dump(summary, open(os.path.join(OUT_DIR, 'missing-repos-summary.json'), 'w'),
          ensure_ascii=False, indent=1)
gh_out = os.environ.get('GITHUB_OUTPUT')
if gh_out:
    with open(gh_out, 'a') as f:
        f.write(f"missing={len(missing)}\nmissing_over_5k={len(big)}\n")

print(f"\nGitHub 命中 {len(found)} 个,未收录 {len(missing)} 个(其中 >=5000★ 的 {len(big)} 个)")
for i in missing[:30]:
    print(f"  {i['stargazers_count']:>7,}★  {i['full_name']:<46} {(i['description'] or '')[:44]}")
