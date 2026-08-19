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
tok = subprocess.run(['gh','auth','token'], capture_output=True, text=True,
                     env={k:v for k,v in os.environ.items()
                          if k not in ('GH_TOKEN','GITHUB_TOKEN')}).stdout.strip()

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
cur.execute("SELECT lower(full_name) FROM extra_repos")
have |= {r[0] for r in cur.fetchall()}
conn.close()

missing = [v for k, v in found.items() if k.lower() not in have]
missing.sort(key=lambda i: -i['stargazers_count'])
json.dump([{'full_name': i['full_name'], 'stars': i['stargazers_count'],
            'description': i['description']} for i in missing],
          open('/tmp/missing_repos.json','w'), ensure_ascii=False, indent=1)
print(f"\nGitHub 命中 {len(found)} 个,未收录 {len(missing)} 个")
for i in missing[:30]:
    print(f"  {i['stargazers_count']:>7,}★  {i['full_name']:<46} {(i['description'] or '')[:44]}")
