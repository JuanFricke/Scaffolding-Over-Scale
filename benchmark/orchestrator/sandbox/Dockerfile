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

# laravel-lsp (opencode.json at `full`): the official Laravel language server, same version the
# harness was tested with (laravel/lsp v0.0.31, commit c8dd1b7 of the subject repo). The original
# wrapper ran the PHAR in php:8.4-cli; here PHP 8.4 is local. Extracted like nixpkgs does, because
# as a PHAR it insists on writing logs next to itself.
ADD --checksum=sha256:cd936b7877e9c33804cce5631ce38f33e616e7e84c34fec690d69ba5578d8a66 \
    https://raw.githubusercontent.com/laravel/lsp/v0.0.31/builds/laravel-lsp /tmp/laravel-lsp.phar
RUN mkdir -p /opt/laravel-lsp \
 && php -d phar.readonly=0 -r '(new Phar($argv[1]))->extractTo($argv[2], null, true);' /tmp/laravel-lsp.phar /opt/laravel-lsp \
 && rm /tmp/laravel-lsp.phar \
 && printf '%s\n' '#!/bin/sh' \
      'export LARAVEL_STORAGE_PATH="${XDG_CACHE_HOME:-$HOME/.cache}/laravel-lsp"' \
      'mkdir -p "$LARAVEL_STORAGE_PATH"/framework/cache/data "$LARAVEL_STORAGE_PATH"/framework/views "$LARAVEL_STORAGE_PATH"/framework/sessions "$LARAVEL_STORAGE_PATH"/app/public "$LARAVEL_STORAGE_PATH"/logs' \
      'exec php /opt/laravel-lsp/server "$@"' > /usr/local/bin/laravel-lsp \
 && chmod 755 /usr/local/bin/laravel-lsp

COPY docker-shim.sh /opt/bench-shim/docker
RUN chmod 755 /opt/bench-shim/docker
ENV PATH=/opt/bench-shim:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    COMPOSER_HOME=/home/agent/.composer
WORKDIR /workspace
