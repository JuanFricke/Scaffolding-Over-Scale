#!/bin/sh
# `docker` inside the benchmark sandbox. The tree's bin/pf runs
# `docker compose -f docker/compose.dev.yml exec app <cmd>`; here that just runs <cmd>,
# because the sandbox already is the app container (same PHP image). Nothing else works.
if [ "$1" = "compose" ]; then
  shift
  while [ $# -gt 0 ]; do
    case "$1" in
      -f|--file|-p|--project-name|--env-file|--profile) shift 2 ;;
      -*) shift ;;
      *) break ;;
    esac
  done
  sub="$1"; [ $# -gt 0 ] && shift
  case "$sub" in
    version) echo "Docker Compose version v2 (benchmark sandbox shim)"; exit 0 ;;
    exec|run)
      while [ $# -gt 0 ]; do
        case "$1" in
          -u|--user|-w|--workdir|-e|--env) shift 2 ;;
          -*) shift ;;
          *) break ;;
        esac
      done
      [ $# -gt 0 ] && shift            # service name (app)
      [ $# -gt 0 ] || set -- bash
      exec "$@" ;;
    up)
      [ -f .env ] || cp .env.example .env
      [ -d vendor ] || composer install --no-interaction --no-progress
      php artisan key:generate --force -q 2>/dev/null
      echo "sandbox: no containers here; 'bin/pf shell <cmd>' runs <cmd> directly"; exit 0 ;;
    down|logs|ps|build|stop) echo "sandbox: 'docker compose $sub' is a no-op"; exit 0 ;;
  esac
fi
echo "docker is not available in the benchmark sandbox; run php/composer/npm directly or via 'bin/pf shell <cmd>'" >&2
exit 1
