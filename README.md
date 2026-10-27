# Scaffolding Over Scale: Evaluating Repository-Level Harnesses to Maximize Output Quality in Constrained LLMs

TCC — Juan Paulo Fricke

## Estrutura

O repositório tem duas partes:

- `tcc-artigo-template-latex/` — cópia do template LaTeX de artigo TCC da UNIJUÍ (origem: https://github.com/dornelles/tcc-artigo-template-latex, Prof. Eldair F. Dornelles). É onde o artigo será escrito (`main.tex`, `capitulos/`, `referencias.bib`).
- `benchmark/` — o benchmark de ablação de *harness* usado no experimento: tarefas (`tasks/`), scripts de preparação e avaliação (`bin/`), um snapshot redigido do harness estudado (`harness/v1/`) e os resultados (`runs/results.jsonl`). Veja [`benchmark/README.md`](benchmark/README.md) para o protocolo e [`benchmark/REDACTIONS.md`](benchmark/REDACTIONS.md) para o que foi removido da cópia pública.

## Executar o benchmark

As tarefas reproduzem pull requests do repositório-sujeito `PegaFila/PegaFilaWeb`, que é **privado**. Os enunciados, scripts e o snapshot do harness são públicos aqui, mas os commits das tarefas não. Portanto, **executar o benchmark exige acesso de leitura ao repositório privado**: clone-o ao lado deste (`../PegaFilaWeb`), rode `git fetch --all` nele (inclusive as branches `feat/42-*` e `feat/46-*`) ou aponte a variável `PF_REPO` para o clone. Também são necessários bash, git, tar, awk e docker. Sem esse acesso, o artigo, os enunciados e o harness continuam legíveis, mas a avaliação não pode ser reproduzida.

## Template original

Para atualizar a partir do template original:

```bash
git clone https://github.com/dornelles/tcc-artigo-template-latex.git /tmp/tcc-template
cp -r /tmp/tcc-template/* tcc-artigo-template-latex/
```
