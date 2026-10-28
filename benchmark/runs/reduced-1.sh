#!/usr/bin/env bash
# Rodada reduzida 1: 14 tarefas x 4 níveis x 1 rep, 7 modelos (ver runs/reduced-1.md).
# Uso (de qualquer lugar):  benchmark/runs/reduced-1.sh
# Roda desacoplado do terminal; acompanhar com o comando `status` que ele imprime no fim.
# Rodar de novo retoma de onde parou (células `done` não são refeitas).
set -euo pipefail
BENCH="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BENCH"
export PF_REPO="${PF_REPO:-$HOME/Projetos/PegaFilaWeb}"
M=claude-sonnet-5-5,claude-haiku-5-5,opencode-go/muse-spark-1.3-contributor,opencode-go/deepseek-v4.1-flash,opencode-go/beam-free,llama/gpt-oss-20b,llama/qwen3.6-35b-a3b

if pgrep -f "python -m orchestrator run" >/dev/null; then
    echo "um 'orchestrator run' já está rodando; nada a fazer"; exit 1
fi
docker info >/dev/null 2>&1 || { echo "docker inacessível (daemon parado ou usuário fora do grupo docker)"; exit 1; }

# servidor dos modelos locais
if ! curl -sf localhost:8089/v1/models >/dev/null; then
    mkdir -p runs/_logs
    setsid nohup orchestrator/llama/serve.sh > runs/_logs/llama-server.log 2>&1 < /dev/null &
    for _ in $(seq 60); do curl -sf localhost:8089/v1/models >/dev/null && break; sleep 1; done
    curl -sf localhost:8089/v1/models >/dev/null || { echo "llama-server não subiu (runs/_logs/llama-server.log)"; exit 1; }
    echo "llama-server no ar"
fi

# células do piloto do Muse feitas sem o preâmbulo: refeitas nesta rodada (só na 1ª vez)
python -m orchestrator retry --stale-prompt --no-run --models "$M" --reps 1

mkdir -p runs/_logs
log="runs/_logs/reduced-1-$(date +%Y%m%d-%H%M%S).log"
setsid nohup python -m orchestrator run --models "$M" --reps 1 > "$log" 2>&1 < /dev/null &
sleep 5
echo "rodando (pid $!), log: benchmark/$log"
echo "status: cd $BENCH && python -m orchestrator status --models $M --reps 1"
