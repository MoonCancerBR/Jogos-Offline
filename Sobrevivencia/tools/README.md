# tools/

Scripts de **desenvolvimento e performance** — não são importados pelo jogo em produção.

## Arquivos

| Arquivo | Função |
|---|---|
| `profiler.py` | *(planejado)* Análise de performance com `cProfile`: mede FPS, tempo de update/render e identifica gargalos de spawn e colisão. |
| `balance_editor.py` | *(planejado)* Editor CLI/GUI para ajustar `config/balance.json` com preview de curvas de dificuldade, sem necessidade de IDE. |
| `__init__.py` | Marca o diretório como pacote Python. |

## Dependências Internas

- Ferramentas são **stand-alone**: não são importadas por nenhum módulo do jogo.
- `balance_editor.py` lê e escreve em `config/balance.json` e pode gerar snapshots em `data/constants_backup.py`.
- `profiler.py` executa o módulo alvo e salva relatório de performance.

## Como Executar

```bash
python -m Sobrevivencia.tools.profiler
python -m Sobrevivencia.tools.balance_editor
```
