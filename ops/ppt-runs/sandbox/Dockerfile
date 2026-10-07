# Sandbox for running one third-party PPT skill end to end (ops/ppt-runs/README.md).
# Throwaway: one container per skill, removed after the run.
FROM node:22-bookworm
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv git sudo curl ca-certificates jq poppler-utils \
      libreoffice-impress libreoffice-calc fonts-noto-cjk fonts-noto-color-emoji chromium \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages python-pptx pillow
RUN npm install -g @anthropic-ai/claude-code
# Skills may `sudo apt install`; inside the throwaway container that is allowed.
RUN useradd -m -s /bin/bash runner && echo 'runner ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/runner
USER runner
WORKDIR /home/runner/work
COPY --chown=runner run_one.sh render.py /home/runner/bin/
ENTRYPOINT ["bash", "/home/runner/bin/run_one.sh"]
