#!/bin/bash
# The SEO test's sandbox entry (ops/seo-runs): serve the test site at http://lumentea.test/, then the usual run.
# The site is copied to a root-only folder so the agent audits it over HTTP, not by reading the files.
sudo mkdir -p /srv/seo && sudo cp -r /in/site /in/server.py /srv/seo/ && sudo chmod -R go-rwx /srv/seo
echo "127.0.0.1 lumentea.test" | sudo tee -a /etc/hosts > /dev/null
sudo sh -c 'nohup python3 /srv/seo/server.py 80 > /srv/seo/access.log 2>&1 &'
for _ in $(seq 1 20); do curl -s -o /dev/null http://lumentea.test/ && break; sleep 0.5; done
mkdir -p /out; trap 'sudo cp /srv/seo/access.log /out/access.log 2>/dev/null; sudo chown runner /out/access.log 2>/dev/null' EXIT
bash /home/runner/bin/run_one.sh "$@"
