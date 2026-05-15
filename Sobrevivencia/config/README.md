# config/

Pasta para **configurações externas** do jogo — editáveis sem alterar código Python.

## Arquivos

| Arquivo | Função |
|---|---|
| `settings.json` | *(planejado)* Resolução, fullscreen, volume de SFX/BGM, idioma, sensibilidade de mira. |
| `balance.json` | *(planejado)* Stats de inimigos, dano, velocidade, taxas de drop — tuning sem IDE. |
| `keybinds.json` | *(planejado)* Mapeamento de teclas, botões de mouse e gamepad (salvo automaticamente ao remapear). |
| `__init__.py` | Marca o diretório como pacote Python. |

## Dependências Internas

- Os arquivos `.json` serão carregados na inicialização pela camada `data/constants.py` ou por um futuro módulo `data/config_loader.py`.
- `main.py` poderá ler `settings.json` antes de criar a janela Pygame.
- Nenhum módulo de produção depende de `config/` atualmente — os valores estão hardcoded em `data/constants.py` até a implementação do loader.
