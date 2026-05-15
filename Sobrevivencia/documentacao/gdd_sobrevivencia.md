# Game Design Document (GDD): Sobrevivência

**Última atualização:** 15/05/2026 — Reestruturação de diretórios + pasta documentacao  
**Plataforma:** PC  
**Tecnologia:** Python + Pygame  
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
- Pontos são usados no inventário para subir o nível dos itens, no Gerenciamento de Skills e na Loja de Status.

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

#### Status possíveis

| Status | Efeito aplicado |
|---|---|
| Vida máxima | Aumenta vida máxima e cura o mesmo valor. |
| Dano | Aumenta multiplicador de dano global. |
| Velocidade | Aumenta velocidade de movimento. |
| Cadência | Aumenta velocidade de tiros e golpes. |
| Alcance corpo a corpo | Aumenta alcance da espada/adagas. |
| Carga de especial | Aumenta carga recebida por abate. |
| Vampirismo | Aumenta cura ao derrotar inimigos. |
| Pente | Aumenta capacidade do pente. |
| Recarga | Reduz duração de recarga, respeitando o limite mínimo atual. |

---

## 7. Inventário, Itens e Construções

O inventário é aberto com I ou TAB por padrão. Ele possui 5 slots ativos e 20 slots de reserva. Apenas itens ativos aplicam efeitos.

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
- A fusão exige confirmação.
- Itens usados são consumidos.
- Dois itens base criam um híbrido.
- Dois híbridos compatíveis criam uma relíquia.
- Relíquias não podem ser fundidas.

### 7.4 Tela de Construções

Acessada pelo pause, mostra catálogo e árvore de crafting:

- Tier 1: itens base.
- Tier 2: híbridos.
- Tier 3: relíquias.
- Navegação por setas, Page Up/Page Down, Home/End e mouse.

---

## 8. Relíquias

Relíquias são itens Tier 3 criados por fusão de híbridos ou obtidos raramente em caixas.

### 8.1 Relíquias Pré-definidas

| Nome | Fontes |
|---|---|
| Relíquia do Caçador Eterno | `blade_relay + chrono_boots + guardian_plate + magnet_orb` |
| Relíquia da Vontade de Ferro | `blade_relay + chrono_boots + guardian_plate + storm_core` |
| Relíquia da Velocidade Caótica | `blade_relay + chrono_boots + magnet_orb + storm_core` |
| Relíquia do Colossus Estático | `blade_relay + guardian_plate + magnet_orb + storm_core` |
| Relíquia do Tempo Absoluto | `chrono_boots + guardian_plate + magnet_orb + storm_core` |

### 8.2 Aura de Fogo

Ao equipar pelo menos uma relíquia ativa:

- Dois círculos de fogo orbitam o personagem.
- Raio: cerca de 82 px.
- Dano: 8 dano/s em inimigos dentro da área.
- Visual: anel roxo translúcido com glóbulos laranja/dourados.

### 8.3 Drop Raro

Caixas de item têm **0,5%** de chance de conceder uma relíquia aleatória.

---

## 9. Mundo

### 9.1 Geração Procedural

- Mundo infinito gerado por chunks determinísticos de 768 px.
- Hash estável preserva regiões já visitadas.
- A área inicial ao redor do jogador é limpa para evitar bloqueios injustos.

### 9.2 Terrenos

| Terreno | Cor | Modificador |
|---|---|---:|
| Grama | `#173B2A` | 100% |
| Pedra | `#293241` | 92% |
| Lama | `#46372B` | 76% |
| Areia | `#786C3A` | 55% |

### 9.3 Objetos

- **Obstáculos:** bloqueiam movimentação.
- **Caixotes:** podem dropar moeda, XP, cura ou escudo.
- **Caches:** têm chance adicional de caixa de item.
- **Caixas especiais:** sempre geram caixa de item e moeda.

### 9.4 Hazards

| Tipo | Comportamento |
|---|---|
| Fogo | 17 dano/s ao jogador e 12,24 dano/s a inimigos. Conta para missão de fogo. |
| Gelo | Aplica multiplicador de velocidade de 1,36 no cálculo de hazard/terreno. |
| Mina | Detona por contato do jogador ou inimigo, com raio de 145 px e 74 de dano. |

---

## 10. Inimigos

A dificuldade base escala com:

`1.0 + tempo_de_partida / 85 + (nível_do_jogador - 1) x 0,09`

| Tipo | Nome | Raio | Vida | Velocidade | Dano/s | XP | Moeda |
|---|---|---:|---:|---:|---:|---:|---:|
| `basic` | Errante | 17 | 36 | 122 | 14 | 11 | 12% |
| `runner` | Corredor | 13 | 24 | 178 | 11 | 9 | 10% |
| `brute` | Bruto | 24 | 95 | 82 | 25 | 25 | 28% |
| `chromatic` | Errático Cromático | 20 | 62 | 255 | 6 | 36 | 75% |
| `spitter` | Atirador Ácido | 16 | 58 | 108 | 13 | 18 | 18% |
| `bulwark` | Guardião Blindado | 29 | 175 | 66 | 30 | 38 | 34% |
| `sapper` | Demolidor Instável | 15 | 32 | 168 | 8 | 16 | 16% |
| `miniboss` | Colosso Errante | 46 | 720 | 58 | 22 | 180 | 100% |
| `minion` | Servo do Colosso | 11 | 18 | 200 | 8 | 4 | 0% |

### 10.1 Spawns

- Intervalo inicial: 1,15 s.
- Intervalo mínimo: 0,23 s.
- Spawns comuns surgem entre 560 e 760 px do jogador.
- Após 25 s, corredores entram na rotação.
- Após 75 s, brutos entram na rotação.
- Após 95 s, Atiradores Ácidos entram na rotação.
- Após 150 s, Guardiões Blindados entram na rotação.
- Após 190 s, Demolidores Instáveis entram na rotação.
- Após 80 s, pode surgir +1 inimigo por ciclo.
- Após 170 s, pode surgir +1 inimigo adicional.

### 10.2 Errático Cromático

- Surge a cada 18 a 32 s.
- Vive por 12 s e escapa se não for morto.
- Movimento especial: foge quando perto, orbita em média distância e aproxima quando longe.
- Ao morrer, concede recompensa aleatória.

### 10.3 Mini-boss: Colosso Errante

- Pode surgir após 45 s, respeitando timer de 86 a 132 s.
- Só um mini-boss ativo por vez.
- Ao morrer: vida cheia, +80 munição, pontos, +3 pontos de item, +3 níveis, moedas e recompensa forte.

| Ação | Aviso | Efeito |
|---|---|---|
| Salto | Círculo vermelho por 0,95 s | Causa 48 dano em raio de 128 px. |
| Laser | Faixa vermelha por 0,85 s | Laser de 760 px, largura 54 px, 38 dano. |
| Invocação | Aura roxa por 2 s | Invoca 3 a 5 Servos do Colosso. |
| Pulso Sísmico | Círculo vermelho por 0,78 s | Causa 36 dano em raio de 220 px. |

Quando a vida do Colosso cai abaixo de 45%, ele entra em fúria uma vez, ganhando velocidade e dano.

### 10.4 Novos Comportamentos

- **Atirador Ácido:** mantém distância e dispara uma linha de ácido com aviso prévio. A frequência do laser é moderada e o disparo é precedido por uma **linha de mira visual** (aviso de 0,6 s) antes do projétil real, dando ao jogador tempo de reagir. A lógica de fuga possui **distância máxima** para que o inimigo não se afaste infinitamente do jogador; ao atingir o limite, ele recua lentamente ou para de fugir.
- **Guardião Blindado:** protege inimigos próximos, reduzindo dano recebido por eles.
- **Demolidor Instável:** corre até o jogador e explode ao se aproximar.

---

## 11. Pickups e Recompensas

| Pickup | Efeito |
|---|---|
| XP | Soma experiência e pontuação. TTL de 18 s. |
| Munição | Adiciona munição à reserva. Pode iniciar recarga se o pente estiver vazio. |
| Moeda | +25 pontos. A cada 5 moedas, ativa buff aleatório por 8 s. |
| Cura | Restaura vida imediatamente. |
| Escudo | 7 s de invulnerabilidade, +25% velocidade, repulsão e dano próximo. |
| Caixa de Item | Adiciona item novo, sobe item existente ou concede ponto se não houver item disponível. |

### Buffs de Moeda

- **Tiro Congelante:** projéteis aplicam congelamento.
- **Aumento de Velocidade:** +45% velocidade.
- **Dano Energizado:** +25% dano.

---

## 12. Missões Temporárias

### Fluxo

- Primeira missão surge entre 60 e 90 s.
- Após concluir ou falhar, a próxima surge entre 90 e 150 s.
- Só há uma missão ativa por vez.
- Recompensa: +3 níveis e screen shake.

| ID | Objetivo | Meta | Tempo |
|---|---|---:|---:|
| `kill_fast` | Mate 50 inimigos em 30 s | 50 abates | 30 s |
| `melee_only` | Sobreviva só com arma corpo a corpo | 60 s | 60 s |
| `stand_fire` | Fique dentro de área de fogo | 15 s acumulados | 90 s |
| `kill_brutes` | Abata Brutos | 5 Brutos | 90 s |
| `survive_no_dash` | Sobreviva sem usar dash | 45 s | 45 s |

---

## 13. Game Director

A cada 60 s, o Game Director aumenta a pressão da partida.

| Atributo | Incremento por minuto | Limite |
|---|---:|---:|
| Vida dos inimigos | +5% | +100% |
| Dano dos inimigos | +2% | +40% |
| Velocidade dos inimigos | +2% | +30% |
| Cap de inimigos | +5 por minuto | 140 |

Mensagem exibida: `Minuto N: inimigos mais fortes!`

---

## 14. Interface

### HUD

- Vida, XP e duas barras de especial.
- Arma ativa.
- Pente/recarga.
- Cooldown do dash.
- Abates, moedas e pontos.
- Mensagem de sistema.
- Buffs ativos.
- Slots de itens ativos.
- Slots das passivas do personagem.
- Painel de status com dano, alcance, cadência, pente, reserva e recarga.
- Painel de missão.

### Telas

| Tela | Função |
|---|---|
| Menu Principal | Iniciar jogo, comandos, configurações ou voltar ao menu arcade. |
| Seleção de Personagem | Exibe armas, especial e passivas em duas colunas. |
| Pause | Continuar, comandos, configurações, skills, construções, trocar personagem, reiniciar, voltar ao menu ou fechar. |
| Comandos | Consulta rápida dos controles atuais e da mecânica de munição. |
| Configurações | Alternar tela cheia, restaurar controles padrão e remapear atalhos de jogabilidade por sessão, incluindo joystick/controle. |
| Level Up | Escolher carta de upgrade; cartas não selecionadas usam fundo escuro de alto contraste. No multiplayer, a UI sinaliza visualmente (brilho ou cursor colorido P1/P2) de quem é a vez de escolher. |
| Inventário | Equipar, remover, upar, marcar fusão e ver reserva. |
| Gerenciamento de Skills | Ver skills ativas/bloqueadas e gastar pontos para desbloquear ou upar passivas. |
| Loja de Status | Rerrolar e comprar melhorias permanentes de status a partir do nível 20. |
| Confirmação de Fusão | Confirmar ou cancelar consumo de itens nível 10. |
| Construções | Catálogo de itens, híbridos, relíquias e árvores de fusão. |
| Game Over | Tempo, abates, pontuação, reinício, troca de personagem e opções finais. |

### 14.1 Adaptação de Tela (Fullscreen)

- O modo tela cheia utiliza a **resolução nativa do monitor** via escala de DPI, em vez de forçar mudança de resolução.
- A superfície do jogo é renderizada na resolução lógica (1100 × 720) e escalada para a resolução nativa via `pygame.transform.smoothscale`, evitando borrões e flickering.
- Se o modo fullscreen escalado falhar no driver/renderer local, o jogo tenta fullscreen simples e volta para janela se necessário, sem encerrar a partida.

### 14.2 Fila de Ações na UI (Level Up — Multiplayer)

- A interface sinaliza visualmente de quem é a vez de escolher com **brilho ou cursor colorido** (P1 azul / P2 vermelho).
- Enquanto o Jogador A escolhe, os inputs do Jogador B para a UI são **completamente ignorados**, prevenindo seleções acidentais.
- Após a escolha do Jogador A, o sistema libera o input do Jogador B e bloqueia o do Jogador A automaticamente.

### 14.3 Trava de Dispositivo — Singleplayer

No modo singleplayer, o jogo implementa detecção do dispositivo ativo para evitar conflito de inputs simultâneos entre mouse/teclado e joystick:

- Quando o jogador usa o **joystick**, os eventos de mouse e teclado são ignorados pelo sistema de jogabilidade.
- Quando o jogador usa **mouse/teclado**, os inputs do joystick são desconsiderados.
- A troca de dispositivo ativo ocorre **automaticamente** ao detectar o primeiro input do novo dispositivo, sem necessidade de configuração manual.
- A detecção não afeta navegação de menus, apenas inputs de jogabilidade.

### Configurações de Jogabilidade

- A tela pode ser aberta pelo menu principal, pelo pause ou pelo atalho padrão O durante a partida.
- O jogador pode remapear ações de jogabilidade para teclado, botões do mouse ou entradas de joystick/controle.
- Joysticks conectados são detectados via Pygame; o remapeador captura botões, eixos analógicos direcionais e D-pad/hat.
- Cada ação possui três slots de atalho: primário, alternativo e controle.
- Ao detectar joystick, o jogo aplica um padrão inicial estilo Xbox 360: analógico esquerdo para movimento, analógico direito para mira, A para confirmar/dash, B para voltar, X para especial, Y para alternar arma, LB para Loja de Status, Back para inventário, RB para skills e Start para pausar.
- Quando o analógico direito é usado, a mira passa para modo joystick e mostra um ponteiro na direção apontada; mover/clicar o mouse devolve a mira para o mouse.
- O menu inicial, a seleção de personagem, a tela de comandos, a tela de configurações e o pause aceitam navegação básica por joystick.
- As alterações valem apenas para a sessão atual da partida.
- A tela possui botão para restaurar os atalhos padrão.
- A tela cheia pode ser alternada pela janela de Configurações ou pelo atalho padrão F11.
- Se o joystick for desconectado durante a sessão, o jogo reinicializa o estado de entrada e continua em execução.
- A tela Comandos reflete os atalhos atualmente configurados.

---

## 15. Controles

As entradas abaixo são os padrões iniciais. As ações de jogabilidade podem ser remapeadas na tela de Configurações durante a sessão para teclado, mouse ou joystick; controles de navegação de menus permanecem fixos.

| Ação | Entrada padrão |
|---|---|
| Mover | WASD ou setas |
| Mover com controle | Analógico esquerdo |
| Mirar | Mouse |
| Mirar com controle | Analógico direito |
| Alternar arma | Q ou Shift |
| Alternar arma com controle | Y |
| Dash | Espaço |
| Dash com controle | A |
| Especial da arma atual | E |
| Especial com controle | X |
| Combo ultimate | Segurar atalho de especial com as duas barras cheias |
| Inventário | I ou TAB |
| Inventário com controle | Back |
| Gerenciamento de Skills | K ou opção no pause |
| Gerenciamento de Skills com controle | RB |
| Loja de Status | L ou opção no pause a partir do nível 20 |
| Loja de Status com controle | LB |
| Pausar | Esc |
| Pausar com controle | Start |
| Configurações | O ou opção no menu/pause |
| Tela cheia | F11 ou botão em Configurações |
| Confirmar | Enter, Enter numérico ou Espaço |
| Equipar/remover item | Enter ou E no inventário |
| Upar item | U no inventário |
| Marcar fusão | F no inventário |
| Confirmar fusão | Y ou botão Confirmar |
| Cancelar fusão | N, Esc ou Backspace |
| Construções | Acessar pelo pause |
| Navegar construções | Setas, Page Up/Page Down, Home/End |
| Roletar Loja de Status | Botão Roletar ou R quando não houver ofertas |
| Comprar oferta da Loja de Status | Botões Comprar ou teclas 1, 2 e 3 |
| Rerrolar oferta da Loja de Status | Botão Jogar novamente abaixo da oferta |
| Reiniciar no Game Over | R |
| Trocar personagem no Game Over | C ou T |

---

## 16. Multiplayer Local (Coop)

O jogo possui modo cooperativo local para dois jogadores quando um joystick/controle é detectado.

### 16.1 Inicialização

- Ao escolher iniciar uma partida com joystick conectado, o jogo exibe seleção entre **Single-Player** e **Multiplayer**.
- No modo Multiplayer, a seleção de personagens ocorre em turnos: primeiro Jogador 1, depois Jogador 2.
- Os dois jogadores podem escolher o mesmo personagem.
- Jogador 1 usa **teclado + mouse**.
- Jogador 2 usa **joystick/controle**.

### 16.2 Câmera Dinâmica (Ponto Médio)

- A câmera segue o **centro geométrico** entre os dois jogadores: `CamPos = (P1 + P2) / 2`.
- Existe um **limite de distância máxima** entre os jogadores. Quando os jogadores se afastam além desse limite, a câmera aplica um **zoom-out leve** para manter ambos visíveis.
- Se a distância máxima de zoom for atingida, o tether impede que os jogadores se afastem mais (ver seção 16.2.1).
- Se o Jogador 1 cair, a câmera passa automaticamente a seguir o Jogador 2 enquanto ele estiver vivo, e vice-versa.
- As miras possuem cores distintas: Jogador 1 azul e Jogador 2 vermelho.

#### 16.2.1 Tether

- Os jogadores não podem se afastar além do limite máximo de tether.
- Ao ultrapassar a distância limite, o jogador mais distante do centro é teletransportado para uma posição segura próxima ao foco da câmera.

### 16.3 Interface

- O HUD cooperativo exibe vida, especiais, munição e dash dos dois jogadores em lados opostos da tela.
- O modo cooperativo também exibe dois painéis de status individuais, um para cada jogador, mostrando velocidade, velocidade no terreno atual, dano à distância, dano corpo a corpo, alcance, cadência de tiro, munição, reserva e pontos do inventário correspondente.
- Moedas aparecem como recurso compartilhado.
- Mensagens de level up e menus congelam a partida e destacam o turno do jogador que está realizando a ação, por exemplo: `Turno do Jogador 2`.
- Telas de gerenciamento individual, como Inventário e Gerenciamento de Skills, usam uma janela única com indicador do jogador ativo e botão **Ver Jogador 1/2** para alternar entre os dados de cada jogador.
- **Input lock — multiplayer:** enquanto P1 escolhe na UI, os inputs de P2 são ignorados (e vice-versa), prevenindo seleções acidentais.

### 16.4 Progressão e Economia

- **XP compartilhado:** o nível é **global para a dupla**. XP coletado por qualquer jogador alimenta uma barra de nível compartilhada.
- Ao subir de nível, ambos os jogadores ganham a oportunidade de escolher um upgrade de status via sistema de **draft por revezamento** (ver seção 6.1.1).
- Cada jogador escolhe individualmente 1 opção de upgrade, aplicada ao seu personagem.
- Passivas exclusivas de personagem permanecem individuais e separadas da escolha comum.
- Cada jogador possui individualmente: vida, status, inventário, itens passivos, passivas, munição, especiais, abates e pontuação.
- Moedas são coletivas e entram em uma carteira compartilhada no modo coop.
- A Loja de Status continua sendo uma loja de equipe: ofertas compradas aplicam os status aos jogadores da partida.

### 16.5 Queda, Revive e Derrota

- Ao zerar a vida, o jogador entra em estado de queda em vez de encerrar imediatamente a partida.
- Um sinal de resgate aparece sobre o corpo caído.
- O jogador vivo precisa permanecer dentro da área do sinal por **4,0 s** para reviver o aliado.
- O jogador revivido retorna com **50% da vida máxima** e invulnerabilidade curta.
- O Game Over só ocorre quando os dois jogadores estão caídos simultaneamente.

---

## 17. Balanceamento Atual

- Arma de distância é a opção mais segura, mas depende de munição.
- Corpo a corpo é obrigatório durante recarga e ganha várias passivas próprias.
- Multishot e Flechas Estilhaço são eficientes porque consomem só 1 munição por salva.
- Munição cai de inimigos, então o jogador precisa continuar lutando e se posicionando.
- Builds fortes devem alternar entre dano à distância, controle melee e gestão de recursos.
- Relíquias continuam sendo objetivos de longo prazo.

---

## 18. Roadmap

Os itens desta seção são pendências planejadas e ainda não fazem parte da implementação atual.

### Curto Prazo

- Adicionar efeitos sonoros para pente vazio, recarga completa, pickup de munição e fusão.
- Criar feedback visual mais forte para "sem munição".
- Mostrar build final no Game Over.
- Balancear chances de drop de munição após testes de duração real.

### Médio Prazo

- Adicionar personagens com outras regras de munição.
- Criar inimigos que pressionem especificamente durante a recarga.
- Adicionar upgrades comuns ligados a reserva e velocidade de recarga.
- Criar variações de bioma com hazards exclusivos.

### Longo Prazo

- Sistema de conquistas.
- Ranking local por personagem.
- Meta-progressão entre partidas.
- Novos mini-bosses com padrões próprios.

---

## 19. Arquitetura Técnica

### 19.1 Estrutura de Diretórios

O projeto segue uma arquitetura modular inspirada em MVC/ECS simplificado, separando responsabilidades em camadas. A estrutura foi reorganizada em 15/05/2026 para facilitar escalabilidade.

> **Diagrama interativo:** consulte `documentacao/estrutura_projeto.mmd` para o diagrama Mermaid completo com responsabilidades detalhadas de cada pasta.

```
Sobrevivencia/
│
├── main.py                        ← Loop principal, input e state machine
├── gdd_sobrevivencia.md           ← Este documento
├── __init__.py                    ← Entry point do pacote Python
│
├── core/                          ← Motor do jogo (lógica pura)
│   ├── game_logic.py              ← Toda a lógica de gameplay (GameLogic)
│   ├── entities.py                ← Dataclasses: Player, Enemy, Projectile, etc.
│   └── world.py                   ← Geração de chunks, colisão, terreno
│
├── data/                          ← Dados e configurações do jogo
│   ├── constants.py               ← Todas as constantes numéricas e dicionários
│   └── items.py                   ← Definições de itens, Inventory, fusões
│
├── presentation/                  ← Renderização e interface (UI)
│   └── ui.py                      ← Toda renderização Pygame (HUD, menus, telas)
│
├── assets/                        ← Recursos visuais e sonoros
│   ├── items/                     ← Ícones de itens (PNG 32x32)
│   ├── sprites/                   ← (futuro) Sprite sheets de personagens/inimigos
│   ├── sfx/                       ← (futuro) Efeitos sonoros (.ogg/.wav)
│   ├── bgm/                       ← (futuro) Trilhas de fundo (.ogg)
│   └── fonts/                     ← (futuro) Fontes customizadas (.ttf)
│
├── config/                        ← Configurações externas sem código
│   ├── settings.json              ← (futuro) Resolução, volume, idioma
│   ├── balance.json               ← (futuro) Stats editáveis sem IDE
│   └── keybinds.json              ← (futuro) Mapeamento de teclas/gamepad
│
├── tools/                         ← Scripts de desenvolvimento
│   ├── profiler.py                ← (futuro) Análise de performance
│   └── balance_editor.py          ← (futuro) Editor de balance.json
│
└── documentacao/                  ← Documentação técnica e de design
    ├── estrutura_projeto.mmd      ← Diagrama Mermaid da árvore de diretórios
    └── gdd_sobrevivencia.md       ← Cópia canônica deste GDD
```

### 19.2 Responsabilidade de Cada Camada

| Camada | Arquivo(s) | Responsabilidade |
|---|---|---|
| **Core / Logic** | `core/game_logic.py` | Toda a lógica de gameplay: movimento, combate, spawns, drops, progressão, multiplayer. Não importa Pygame diretamente. |
| **Core / Entities** | `core/entities.py` | Dataclasses puras: `Player`, `Enemy`, `Projectile`, `Slash`, `Drop`, `Hazard`, `Destructible`. Sem lógica de gameplay. |
| **Core / World** | `core/world.py` | Geração procedural de chunks, colisão círculo-retângulo, terreno e hazards do mapa. |
| **Data / Constants** | `data/constants.py` | Todas as constantes numéricas, dicionários de terreno, inimigos, personagens e cores. É a única fonte de verdade para balanço. |
| **Data / Backup** | `data/constants_backup.py` | Snapshot de segurança gerado antes de grandes refatorações. Não é importado em produção. |
| **Data / Items** | `data/items.py` | Definições de itens, sistema de Inventory, lógica de fusão Híbrido/Relíquia. |
| **Presentation** | `presentation/ui.py` | Toda a renderização Pygame: HUD, menus, telas de personagem, pause, game over. Não executa lógica de gameplay. |
| **Entry Point** | `main.py` | Loop principal, input de teclado/joystick, state machine (menu → jogo → pause → game over). |
| **Documentação** | `documentacao/` | GDD canônico e diagrama Mermaid da arquitetura do projeto. |

### 19.3 Fluxo de Importação

```
main.py
  ├── data.constants (FPS, tamanho de tela, personagens)
  ├── core.game_logic (GameLogic)
  │     ├── data.constants (todas as constantes)
  │     ├── core.entities (dataclasses)
  │     ├── data.items (Inventory)
  │     └── core.world (World)
  └── presentation.ui (UI)
        ├── data.constants
        └── data.items (nomes e descrições)

Nota: data.constants_backup NÃO é importado em nenhum módulo de produção.
```

### 19.4 Como Adicionar Conteúdo

**Novo personagem jogável:**
1. Adicionar entrada em `CHARACTERS` em `data/constants.py` com `weapon_1`, `weapon_2`, `passives`, `specials`, `color`, etc.
2. Implementar lógica exclusiva de especial em `core/game_logic.py` nos métodos `_cast_weapon_special` e `_cast_combo_special`.
3. Adicionar sprite/ícone em `assets/sprites/`.

**Novo inimigo/boss:**
1. Adicionar entrada em `ENEMY_TYPES` em `data/constants.py`.
2. Implementar comportamento de IA em `core/game_logic.py` (métodos `_<tipo>_velocity` e `_update_enemies`).
3. Adicionar lógica de spawn em `_spawn_special_enemy` se for inimigo especial.

**Novo item passivo:**
1. Adicionar em `ITEM_DEFINITIONS` em `data/items.py`.
2. Adicionar lógica de efeito em `core/game_logic.py`.
3. Adicionar ícone PNG em `assets/items/`.

**Nova fusão:**
1. Adicionar em `RELIC_DEFINITIONS` em `data/constants.py` (chave = fontes ordenadas por `+`).
2. A lógica de `preview_fusion` em `data/items.py` reconhece automaticamente relíquias registradas.

**Novo obstáculo no mundo:**
1. Adicionar tipo em `core/world.py` com lógica de colisão/geração.
2. Registrar parâmetros visuais em `data/constants.py`.
3. Adicionar sprite em `assets/sprites/` (quando implementado).

**Novo hazard:**
1. Adicionar entrada em `HAZARD_TYPES` em `data/constants.py`.
2. Implementar geração e efeito em `core/world.py` e `core/game_logic.py`.

**Novo bioma:**
1. Definir paleta, terrenos e hazards em `data/constants.py`.
2. Implementar regras de geração em `core/world.py`.
3. Adicionar trilha em `assets/bgm/` e registrar no carregador de assets.

---

## 20. Histórico de Mudanças Estruturais

| Data | Mudança | Responsável |
|---|---|---|
| 15/05/2026 | Reestruturação do projeto de arquivo único (`main.py`) para arquitetura modular MVC/ECS. Criação de `core/`, `data/`, `presentation/`, `assets/`, `config/`, `tools/`. | Antigravity AI |
| 15/05/2026 | Criação de `data/constants_backup.py` como snapshot de segurança antes da refatoração de constantes. | Antigravity AI |
| 15/05/2026 | Criação da pasta `documentacao/` com `estrutura_projeto.mmd` (diagrama Mermaid) e cópia canônica do GDD. Correção de numeração duplicada da seção 11. | Antigravity AI |
