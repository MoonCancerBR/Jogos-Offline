# Game Design Document (GDD): Sobrevivência

**Última atualização:** 15/05/2026 — Modernização de UI/UX, Mercado Negro e Sistemas de Evolução  
**Plataforma:** PC  
**Tecnologia:** Python + Pygame (Modernizado com `freetype`, `pytweening` e `pygame-gui`)  
**Resolução alvo:** 1100 x 720 px, 60 FPS, com opção de tela cheia escalada  
**Gênero:** Top-down action survival / bullet heaven tático  
**Referências:** Vampire Survivors, Brotato, roguelites de arena com troca de armas

---

## 1. Visão Geral

Sobrevivência é um jogo de ação em arena infinita no qual o jogador enfrenta hordas crescentes de inimigos enquanto monta uma build durante a partida. O jogo combina ataques automáticos, mira com mouse, coleta de recursos, escolhas de upgrade, itens passivos, fusões e eventos temporários.

A mudança central de arsenal é que armas de longa distância não são mais infinitas. Elas usam pente, reserva de munição e recarga. Quando o pente esvazia, o personagem alterna automaticamente para a arma corpo a corpo enquanto recarrega em segundo plano. Isso transforma a troca de armas em parte essencial do ritmo da partida.

### Core Loop

1. Mover pelo mapa infinito e evitar contato, hazards e ataques especiais.
2. Usar a arma de longa distância enquanto houver munição no pente.
3. Ao esvaziar o pente, sobreviver com a arma corpo a corpo durante a recarga.
4. Coletar XP, moedas, munição, curas, escudos e caixas de item.
5. Escolher upgrades comuns, passivas específicas e itens passivos.
6. Fundir itens em híbridos e relíquias.
7. Completar missões, derrotar inimigos especiais e ampliar a build.

---

## 2. Pilares de Design

- **Troca tática:** a arma corpo a corpo deixa de ser reserva emergencial e vira parte obrigatória da rotação.
- **Munição como recurso:** disparar é forte, mas depende de pente, reserva e pickups.
- **Builds com identidade:** cada personagem possui aprimoramentos de distância, melee, híbridos e especial.
- **Legibilidade:** ameaças importantes usam avisos visuais claros.
- **Escalada constante:** tempo, nível e Game Director pressionam o jogador progressivamente.
- **Juice & Feedback:** animações suaves e fontes modernas para uma experiência premium.

---

## 3. Arsenal, Munição e Tactical Swap

### 3.1 Pente e Reserva

- Capacidade base do pente: **20 projéteis**.
- Capacidade aumenta com o nível: `20 + (nível - 1) x 2`.
- Reserva inicial: **60 munições**.
- Disparos consomem munição do pente.
- Ao recarregar, munição é movida da reserva para o pente.
- Se a reserva estiver vazia, o jogador permanece com a arma corpo a corpo até coletar munição.

### 3.2 Recarga Inteligente

A recarga do pente inicia automaticamente sempre que o jogador troca para a arma corpo a corpo, independentemente de o pente estar zerado ou não:

1. Se o jogador trocar manualmente para a espada com munição restante no pente, a recarga começa em segundo plano imediatamente.
2. Quando o pente chega a 0, o jogo alterna automaticamente para a arma corpo a corpo e a recarga começa.
3. Duração base da recarga: **2,15 s**.
4. Ao concluir a recarga, o jogo alterna automaticamente de volta para a arma de longa distância.
5. Se não houver reserva, a arma de longa distância fica indisponível até coletar munição.

### 3.3 Consumo de Munição

- Cada ciclo de disparo consome **1 munição do pente**.
- Multishot e flechas laterais consomem apenas **1 munição**, mesmo gerando vários projéteis.
- Isso incentiva upgrades de área e tiros múltiplos sem punir demais builds focadas em projéteis.

### 3.4 Munição no Mundo

Inimigos derrotados podem derrubar munição:

| Inimigo | Chance | Quantidade |
|---|---:|---:|
| Errante | 18% | 5 a 12 |
| Corredor | 16% | 5 a 12 |
| Bruto | 42% | 10 a 18 |
| Errático Cromático | 70% | 18 a 30 |
| Atirador Ácido | 26% | 5 a 12 |
| Guardião Blindado | 46% | 14 a 24 |
| Demolidor Instável | 22% | 6 a 14 |
| Servo do Colosso | 8% | 2 a 5 |

Mini-boss derrotado concede **+80 munições na reserva** junto das outras recompensas.

---

## 4. Personagens

Cada personagem possui duas armas, dois especiais e dez passivas específicas. As passivas aparecem em upgrades grandes, a cada 3 níveis, mas também podem ser desbloqueadas e aprimoradas manualmente na janela de Gerenciamento de Skills. Cada passiva chega ao nível 10.

### 4.0 Especiais por Arma

- Cada personagem possui um especial de distância e um especial corpo a corpo.
- O especial ativado pelo atalho padrão E depende da arma atual.
- Abates com projéteis, veneno e itens ofensivos de distância carregam a barra de distância.
- Abates com golpes, sangramento, escudo e efeitos próximos carregam a barra corpo a corpo.
- Segurar o atalho de especial por cerca de 1,15 s com as duas barras cheias consome ambas e ativa o combo ultimate.

### 4.1 A Vanguarda

- **Visual:** corpo circular branco (`#F8FAFC`) com triângulo azul (`#38BDF8`).
- **Arma de distância - Pistola:** tiros diretos e constantes. Boa base para multishot, ricochete, veneno e perfuração.
- **Arma corpo a corpo - Espada:** golpe em arco, com dano alto, knockback e destruição de objetos.
- **Especial de distância - Explosão Radial:** explosão ao redor do jogador, causando dano massivo, knockback e destruição de objetos próximos.
- **Especial corpo a corpo - Carga Titânica:** avanço em linha com dano largo e forte, funcionando como abertura ou fuga agressiva.
- **Combo - Protocolo Cerco:** combina Explosão Radial e Carga Titânica em uma ultimate de alto impacto.

#### Passivas da Vanguarda

| Categoria | Chave | Nome | Efeito |
|---|---|---|---|
| Distância | `ricochet` | Balas Ricocheteantes | Projéteis saltam para inimigos próximos. |
| Distância | `poison` | Munição Venenosa | Projéteis aplicam veneno por 3,4 s. |
| Distância | `multishot` | Rajada Paralela | Adiciona +1 projétil paralelo por nível, consumindo só 1 munição por salva. |
| Distância | `piercing_rounds` | Projéteis Perfurantes | Tiros ganham perfuração a cada 3 níveis e dano leve por nível. |
| Corpo a corpo | `wide_cleave` | Corte Amplo | Espada ganha alcance e arco. |
| Corpo a corpo | `execution_edge` | Fio Executor | Espada causa dano extra em inimigos com vida baixa. |
| Corpo a corpo | `shockwave` | Onda de Impacto | Golpes de espada espalham dano em área ao redor do alvo. |
| Ambas | `combat_drill` | Doutrina de Combate | Aumenta dano, cadência e reduz levemente a recarga. |
| Ambas | `field_salvage` | Saque de Campo | Abates podem recuperar munição extra. |
| Especial | `reactor_blast` | Reator Crítico | Especial ganha dano, raio e restaura parte do pente. |

### 4.2 A Caçadora

- **Visual:** corpo circular verde-escuro (`#166534`) com núcleo laranja (`#F97316`).
- **Arma de distância - Arco Longo:** flechas rápidas, fortes e com perfuração base.
- **Arma corpo a corpo - Adagas:** golpes curtos, rápidos e com alto potencial de status.
- **Especial de distância - Chuva de Flechas:** área marcada no cursor que causa dano contínuo por alguns segundos.
- **Especial corpo a corpo - Dança das Adagas:** ataque circular ao redor da Caçadora, aplicando sangramento, knockback e invulnerabilidade curta.
- **Combo - Tempestade Predatória:** combina Chuva de Flechas e Dança das Adagas, criando controle de área e explosão de dano.

#### Passivas da Caçadora

| Categoria | Chave | Nome | Efeito |
|---|---|---|---|
| Distância | `explosive` | Flechas Explosivas | Flechas explodem ao expirar ou bater em parede/objeto. |
| Distância | `homing` | Flecha Teleguiada | Flechas corrigem trajetória rumo ao inimigo mais próximo. |
| Distância | `splinter_arrows` | Flechas Estilhaço | Disparos lançam flechas laterais menores, consumindo só 1 munição. |
| Corpo a corpo | `prey_mark` | Marca da Presa | Adagas reduzem velocidade do alvo e aumentam o dano recebido pelo golpe. |
| Corpo a corpo | `bleeding_blades` | Lâminas Sangrentas | Adagas aplicam sangramento por tempo. |
| Corpo a corpo | `fan_blades` | Leque de Adagas | Adagas ganham arco, alcance e dano. |
| Corpo a corpo | `shadow_lunge` | Investida Sombria | Acertos de adaga reduzem a recarga do dash e dão invulnerabilidade curtíssima. |
| Ambas | `predator_focus` | Foco Predador | Aumenta dano, ritmo das duas armas e reduz levemente a recarga. |
| Ambas | `ammo_siphon` | Saque Preciso | Abates podem recuperar munição e carga de especial. |
| Especial | `storm_eye` | Olho da Tempestade | Chuva de Flechas dura mais, cobre área maior e causa mais dano. |

---

## 5. Mecânicas Principais

### 5.1 Movimento

- Movimento livre em 8 direções com WASD ou setas por padrão.
- Os atalhos de jogabilidade podem ser remapeados durante a sessão pela tela de Configurações, incluindo teclado, mouse e joystick/controle.
- Velocidade base: 235 px/s.
- Terrenos, buffs, escudo, itens e upgrades modificam a velocidade final.

### 5.2 Dash

- Ativado com Espaço por padrão.
- Velocidade: 790 px/s.
- Duração: 0,17 s.
- Invulnerabilidade curta: duração do dash + 0,08 s.
- Cooldown base: 1,25 s.
- Botas Crono, híbridos e Investida Sombria podem reduzir a recarga efetiva.

### 5.3 Dano e Status

- **Dano de contato:** inimigos causam dano contínuo ao encostar.
- **Knockback:** espada, adagas, escudo, explosões, minas e especiais empurram inimigos.
- **Congelamento:** projéteis com buff reduzem inimigos para 28% da velocidade por 2,4 s.
- **Veneno:** dano contínuo aplicado por Munição Venenosa.
- **Sangramento:** dano contínuo aplicado por Lâminas Sangrentas.
- **Escudo:** concede invulnerabilidade por 7 s, +25% velocidade, repulsão e dano próximo.
- **Dano Flutuante:** números de dano agora usam animações de suavização (`pytweening`) para melhor feedback visual.

---

## 6. Progressão

### 6.1 Level Up — Singleplayer

- Fórmula de XP: `40 + 25 x nível_atual`.
- Ao subir de nível, o jogador escolhe 1 entre 3 cartas.
- Níveis comuns oferecem upgrades gerais.
- A cada 3 níveis, o upgrade é grande e oferece passivas específicas do personagem.
- Quando todas as passivas específicas chegarem ao nível 10, upgrades grandes passam a oferecer Omni Upgrades.

### 6.1.1 Level Up — Multiplayer (Draft por Revezamento)

No modo cooperativo, o nível é **global para a dupla**. O XP coletado por qualquer jogador alimenta uma barra de nível compartilhada. Ao subir de nível, ambos os jogadores ganham a oportunidade de escolher um upgrade de status por meio de um sistema de draft:

- **Pool de escolhas:** o jogo gera uma lista única com **3 opções** de status aleatórias (+vida, +velocidade, +dano etc.).
- **Fluxo de seleção (draft):**
  1. O Jogador A (quem tem prioridade neste nível) escolhe **1 das 3** opções disponíveis.
  2. O Jogador B escolhe **1 das 2** opções restantes.
  3. A opção que sobrar é **descartada**.
- **Alternância de prioridade (anti-fixa):** o jogo rastreia quem iniciou a escolha no nível anterior. A cada novo level up, a ordem inverte automaticamente. No primeiro nível, a prioridade é definida por **sorteio** e alternada nos subsequentes.
- **Bloqueio ativo de input:**
  - Enquanto o Jogador A estiver selecionando, o input do Jogador B é **completamente ignorado**.
  - Após a escolha do Jogador A, o sistema libera o input do Jogador B e bloqueia o do Jogador A automaticamente.
  - A UI destaca com **brilho ou cursor colorido** (P1/P2) de quem é a vez em tempo real.
- **Passivas exclusivas:** passivas específicas de personagem permanecem individuais e separadas da escolha comum de draft.
- A cada 3 níveis, o upgrade grande continua oferecendo passivas específicas, aplicadas individualmente a cada jogador.

### 6.2 Upgrades Comuns

| Chave | Nome | Efeito |
|---|---|---|
| `speed` | Passos Leves | +8% velocidade permanente. |
| `damage` | Lâmina e Cano | +13% dano em todos os ataques. |
| `max_health` | Pulso Vital | +22 vida máxima e cura parcial. |
| `fire_rate` | Ritmo de Combate | +11% cadência de tiros e golpes. |
| `sword_range` | Alcance da Espada | +10% alcance do corte. |
| `special_gain` | Núcleo Instável | +16% carga de especial por abate. |
| `vampirism` | Vampirismo | Recupera +2,5 de vida por inimigo derrotado. |

### 6.3 Omni Upgrades

| Chave | Nome | Efeito |
|---|---|---|
| `omni_power` | Poder Absoluto | +25% dano, cadência e alcance de espada. |
| `omni_survival` | Resiliência Máxima | +45 vida máxima, +45% velocidade e +5 vampirismo. |
| `omni_special` | Mestre Supremo | +100% carga de especial, +35% alcance de espada e +15% cadência. |

### 6.4 Pontos de Item

- Cada nível concede +1 ponto de item.
- Upgrades grandes concedem +2 pontos extras.
- Derrotar mini-boss concede +3 pontos.
- Pontos são usados no inventário para subir o nível dos itens, no Gerenciamento de Skills, na Loja de Status e no **Mercado Negro**.

### 6.5 Gerenciamento de Skills

A janela **Gerenciamento de Skills** lista todas as passivas específicas do personagem:

- Skills com nível 0 aparecem como bloqueadas.
- Skills com nível 1 ou mais aparecem como ativas.
- O jogador pode gastar pontos de item para desbloquear ou upar uma skill.
- Skills comuns custam **3 pontos** por nível.
- Skills da categoria **Especial** custam **6 pontos** por nível.
- O nível máximo continua sendo 10.
- A janela pode ser acessada pelo pause ou pela tecla K por padrão durante a partida.
- A lista usa cards escuros de alto contraste; a cor da categoria aparece como borda/etiqueta para preservar leitura.

### 6.6 Loja de Status

A **Loja de Status** é uma mecânica de progressão permanente dentro da sessão:

- Desbloqueio inicial de teste: **nível 20**.
- Acessada pelo pause pela opção **Loja de Status**.
- Usa os mesmos pontos ganhos por nível, criando disputa com itens e skills.
- Ao abrir a loja desbloqueada, o jogador pode usar **Roletar** para gastar 1 ponto e gerar 3 ofertas.
- Cada oferta mostra atributos aleatórios, força da melhoria e custo de compra.
- Abaixo de cada oferta existe o botão **Jogar novamente**, que custa 1 ponto e rerrola apenas aquela oferta.
- Rerrolar uma oferta pode aumentar sua força, chegando até melhorias lendárias.
- O custo de compra é calculado de acordo com a quantidade e intensidade dos status oferecidos.
- Ao comprar uma oferta, seus status são aplicados permanentemente na run e a loja volta ao estado sem ofertas.

---

## 7. Inventário, Itens e Construções

O inventário é aberto com I ou TAB por padrão. Ele possui 5 slots ativos e 20 slots de reserva. Apenas itens ativos aplicam efeitos. A interface agora utiliza **pygame-gui** para uma navegação mais moderna e fluida.

### 7.1 Itens Base

| Chave | Nome | Efeito |
|---|---|---|
| `storm_core` | Núcleo da Tempestade | Solta raio automático no inimigo mais próximo. |
| `guardian_plate` | Placa Guardiã | Reduz dano recebido quando a vida está abaixo de 42%. |
| `magnet_orb` | Orbe Magnético | Aumenta raio de coleta de XP, moedas e caixas. |
| `chrono_boots` | Botas Crono | Aumenta velocidade e reduz cooldown do dash. |
| `blade_relay` | Relé da Lâmina | Aumenta cadência, dano e alcance da espada. |

### 7.2 Upgrade de Itens

| Rank | Tipo | Custo por nível | Nível máximo |
|---|---|---:|---:|
| 1 | Item base | 1 ponto | 10 |
| 2 | Híbrido | 3 pontos | 10 |
| 3 | Relíquia | 7 pontos | 10 |

### 7.3 Fusão

- Dois itens de mesmo rank e nível 10 podem ser marcados com F.
- A fusão exige confirmação em uma tela dedicada com árvore de visualização.
- Itens usados são consumidos.
- Dois itens base criam um híbrido.
- Dois híbridos compatíveis criam uma relíquia.
- Relíquias não podem ser fundidas.

### 7.4 Venda de Itens

O jogador pode vender itens para recuperar pontos de item:
- **Restrição:** Só é possível vender itens que estão na **reserva** (não equipados).
- **Valores de venda:**
  - Rank 1 (Básico): `1 + (nível - 1) // 2` pontos.
  - Rank 2 (Híbrido): `5 + (nível - 1) * 2` pontos.
  - Rank 3 (Relíquia): `15 + (nível - 1) * 5` pontos.

---

## 8. Mercado Negro e Evolução

O **Mercado Negro** é uma aba especial no Inventário desbloqueada permanentemente na sessão ao atingir o **nível 10 com qualquer Relíquia**.

### 8.1 Loja do Mercado Negro
Permite a compra direta de itens base para acelerar builds:
- **Custo:** 15 pontos por item base (nível 1).
- Comprar um item que o jogador já possui aumenta o nível do mesmo.

### 8.2 Transformação de Itens
Mecânica de alto risco para forçar a criação de híbridos:
- **Custo:** 15 pontos.
- **Alvo:** Item base (Rank 1) no nível 10.
- **Resultados:**
  - **Sucesso (50%):** O item evolui instantaneamente para um Híbrido aleatório compatível.
  - **Falha Segura (25%):** Nada acontece, mas os pontos são consumidos.
  - **Falha Crítica (25%):** O item sofre degradação e se transforma em outro item base aleatório.

---

## 9. Relíquias

Relíquias são itens Tier 3 criados por fusão de híbridos ou obtidos raramente em caixas.

### 9.1 Relíquias Pré-definidas

| Nome | Fontes |
|---|---|
| Relíquia do Caçador Eterno | `blade_relay + chrono_boots + guardian_plate + magnet_orb` |
| Relíquia da Vontade de Ferro | `blade_relay + chrono_boots + guardian_plate + storm_core` |
| Relíquia da Velocidade Caótica | `blade_relay + chrono_boots + magnet_orb + storm_core` |
| Relíquia do Colossus Estático | `blade_relay + guardian_plate + magnet_orb + storm_core` |
| Relíquia do Tempo Absoluto | `chrono_boots + guardian_plate + magnet_orb + storm_core` |

### 9.2 Aura de Fogo

Ao equipar pelo menos uma relíquia ativa:

- Dois círculos de fogo orbitam o personagem.
- Raio: cerca de 82 px.
- Dano: 8 dano/s em inimigos dentro da área.
- Visual: anel roxo translúcido com glóbulos laranja/dourados.

---

## 10. Mundo e Inimigos

(Mantido conforme versão anterior, com ajustes de balanceamento dinâmico).

---

## 11. Interface Modernizada

A interface do jogo passou por uma reformulação técnica completa para melhorar a legibilidade e o "game feel".

### 11.1 Tecnologias de UI
- **Pygame-GUI:** Utilizado em um "Design System Modular" para as telas de Inventário, Mercado Negro, Upgrades, Seleção de Personagem, Modos e Configurações. As janelas modais nativas agora gerenciam pop-ups de confirmação, barras de rolagem nativas e imagens sobrepostas vetoriais, substituindo os antigos canvas absolutos.
- **Pygame Freetype:** Substituiu o sistema de fontes legado, permitindo renderização de texto em alta qualidade, rotação e efeitos de contorno sem perda de performance.
- **Animation Manager (Tweening):** Sistema centralizado baseado em `pytweening` que gerencia transições suaves, números flutuantes de dano e efeitos de "pop" em elementos da interface.

### 11.2 Regras de Navegação
- **Voltar ao Menu:** Redireciona o jogador para a tela inicial do modo `Sobrevivência`, mantendo o jogo ativo na memória para recomeços rápidos, sem fechar a aplicação principal.
- **Fechar (Quit / X):** Encerra a sessão da aplicação ativa devolvendo o fluxo para o Arcade de Jogos raiz.

### 11.3 HUD e Telas
- **Feedback de Munição:** Mensagens flutuantes "RECARREGANDO" ou "SEM MUNIÇÃO" com efeito de pulso sobre o jogador.
- **Dano Flutuante:** Números que sobem e desaparecem com curvas de suavização (Ease Out).
- **Miras Coloridas:** Mira azul para P1 e vermelha para P2, com ponteiros específicos para joystick.

---

## 12. Arquitetura Técnica (v2.0)

### 12.1 Dependências
- `pygame` (Core)
- `pygame-ce` (Opcional, recomendado para performance)
- `pygame_gui` (Sistemas de menu modulares)
- `pytweening` (Animações)

### 12.2 Organização de Código
- `presentation/animation_manager.py`: Orquestra todas as interpolações temporais.
- `presentation/menus/`: Contém os componentes de UI modulares (como `ui_components.py`, que atua como Factory para botões, painéis, caixas de texto e superfícies).
- `core/game_logic.py`: Mantém a separação entre lógica pura e visual, comunicando-se com a UI via eventos.
- `core/managers/buff_applicator.py`: O novo coração do sistema matemático de itens.

### 12.3 Status Injetados e Buff Applicator
O `buff_applicator.py` centraliza a matemática de escala dos itens. Em vez de o jogo consultar o inventário a cada frame (o que antes causava quedas bruscas de performance), as funções embutem valores pré-calculados nas seguintes variáveis diretamente no objeto `Player` após o equip/desequip/upgrade:
- `item_speed_bonus`: Multiplicador de velocidade acumulativo de itens.
- `item_damage_bonus`: Bônus direto em ataques e armas.
- `item_attack_rate_bonus`: Aceleração da cadência base.
- `item_sword_range_bonus`: Extensão do hitbox e arco da espada.
- `item_guardian_reduction`: Fração redutora de dano pré-calculada do item `guardian_plate`.

Esses bônus de itens somam-se separadamente aos bônus permanentes ganhos pelo ganho de nível.

---

## 13. Roadmap de UIX e Performance

### Curto Prazo
- Implementar **Pygame-CE** como motor padrão para ganho de performance imediato (até 20% em loops de renderização).
- Migrar o restante dos menus manuais para o `pygame_gui`.

### Médio Prazo
- Avaliar **Numba/Cython** para as rotinas de colisão de hordas (>200 inimigos).
- Adicionar suporte a **Shaders (GLSL)** via `ModernGL` para efeitos de aura e distorção sem sobrecarregar a CPU.

### Longo Prazo
- Sistema de partículas acelerado por GPU.
- UI Dinâmica que reage ao ritmo da música e intensidade do combate.
