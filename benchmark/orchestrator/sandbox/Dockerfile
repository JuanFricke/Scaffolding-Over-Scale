# Agent sandbox: the grading image (same PHP/extensions) plus Node, intelephense and a
# `docker` shim, so the agent can run tests in-place but cannot see anything but its tree.
# The agent CLIs themselves are bind-mounted from the host at run time (same version as
# recorded by `python -m orchestrator env`).
ARG BASE=pf-bench:tcc-baseline-v1
FROM node:22.23.4-bookworm-slim AS node
FROM ${BASE}

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && apt-get update && apt-get install -y --no-install-recommends ripgrep procps less \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g --no-audit --no-fund intelephense@1.18.5 \
 && git config --system safe.directory '*' \
 && git config --system user.name agent \
 && git config --system user.email agent@bench.local \
 && mkdir -p /home/agent && chmod 1777 /home/agent

COPY docker-shim.sh /opt/bench-shim/docker
RUN chmod 755 /opt/bench-shim/docker
ENV PATH=/opt/bench-shim:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    COMPOSER_HOME=/home/agent/.composer
WORKDIR /workspace
