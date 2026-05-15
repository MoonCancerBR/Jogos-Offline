# Sobrevivência

Jogo de ação top-down survival / bullet heaven tático, desenvolvido em **Python + Pygame**.

## Arquivos na Raiz

| Arquivo | Função |
|---|---|
| `main.py` | Loop principal, captura de input (teclado/mouse/joystick) e state machine (menu → seleção → gameplay → pause → game over). |
| `__init__.py` | Marca o diretório como pacote Python importável. |

## Estrutura de Diretórios

| Pasta | Responsabilidade |
|---|---|
| `core/` | Motor do jogo — lógica pura de gameplay, entidades e mundo. |
| `data/` | Dados estáticos — constantes numéricas, definições de itens e fusões. |
| `presentation/` | Renderização — HUD, menus e telas (depende de Pygame). |
| `assets/` | Recursos visuais e sonoros (imagens, sons, fontes). |
| `config/` | Configurações externas em JSON (resolução, balance, keybinds). |
| `tools/` | Scripts de desenvolvimento (profiling, editor de balance). |
| `documentacao/` | Documentação técnica: GDD canônico, diagrama Mermaid, resumo do projeto. |

## Como Executar

```bash
python -m Sobrevivencia.main
```
