# Sandbox for running one third-party PPT skill end to end (ops/ppt-runs/README.md).
# Throwaway: one container per skill, removed after the run.
FROM node:22-bookworm
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv git sudo curl ca-certificates jq poppler-utils \
      libreoffice-impress libreoffice-calc fonts-noto-cjk fonts-noto-color-emoji chromium \
      fonts-liberation2 fonts-crosextra-carlito fonts-crosextra-caladea fonts-inconsolata unzip \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages python-pptx pillow playwright
# Metric-compatible stand-ins for Office fonts, so a deck laid out for Segoe UI / Calibri /
# Arial renders at the same widths (otherwise wider substitutes push titles off the slide).
RUN mkdir -p /usr/share/fonts/truetype/selawik && cd /usr/share/fonts/truetype/selawik \
    && curl -fsSL -o s.zip https://github.com/microsoft/Selawik/releases/download/1.01/Selawik_Release.zip \
    && unzip -qj s.zip '*.ttf' && rm s.zip \
    && printf '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><alias><family>Segoe UI</family><prefer><family>Selawik</family></prefer></alias><alias><family>Microsoft YaHei</family><prefer><family>Noto Sans CJK SC</family></prefer></alias><alias><family>Consolas</family><prefer><family>Inconsolata</family></prefer></alias></fontconfig>' > /etc/fonts/local.conf \
    && fc-cache -f
RUN npm install -g @anthropic-ai/claude-code
# Skills may `sudo apt install`; inside the throwaway container that is allowed.
RUN useradd -m -s /bin/bash runner && echo 'runner ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/runner
USER runner
WORKDIR /home/runner/work
COPY --chown=runner run_one.sh render.py /home/runner/bin/
ENTRYPOINT ["bash", "/home/runner/bin/run_one.sh"]
