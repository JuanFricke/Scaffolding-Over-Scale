#!/bin/bash
# Compila os diagramas TikZ (standalone) para PDF em ../04-desenvolvimento/.
# Usa pdflatex do PATH; se não houver, usa a imagem Docker texlive/texlive:latest-full.
set -euo pipefail
cd "$(dirname "$0")"
OUT=../04-desenvolvimento
mkdir -p "$OUT"
run_pdflatex() {
    if command -v pdflatex >/dev/null 2>&1; then
        pdflatex -interaction=nonstopmode "$@"
    else
        docker run --rm -v "$PWD":/work -w /work -u "$(id -u):$(id -g)" -e HOME=/tmp \
            texlive/texlive:latest-full pdflatex -interaction=nonstopmode "$@"
    fi
}
for f in desenho-experimental camadas-harness orquestrador; do
    run_pdflatex "$f.tex" > /dev/null
    mv "$f.pdf" "$OUT/fig-$f.pdf"
    rm -f "$f.aux" "$f.log"
    echo "-> $OUT/fig-$f.pdf"
done
