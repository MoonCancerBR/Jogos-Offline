from dataclasses import dataclass, field

if __package__:
    from .constants import RELIC_DEFINITIONS
else:
    from constants import RELIC_DEFINITIONS


MAX_ITEM_LEVEL = 10
MAX_ACTIVE_ITEMS = 5
RELIC_UPGRADE_COST = 7

ITEM_DEFINITIONS = {
    "storm_core": {
        "name": "Nucleo da Tempestade",
        "short": "Raio automatico",
        "description": "Solta um raio no inimigo mais proximo em ciclos.",
    },
    "guardian_plate": {
        "name": "Placa Guardia",
        "short": "Defesa em perigo",
        "description": "Reduz dano recebido quando a vida esta baixa.",
    },
    "magnet_orb": {
        "name": "Orbe Magnetico",
        "short": "Coleta ampliada",
        "description": "Aumenta o alcance de coleta de XP, moedas e itens.",
    },
    "chrono_boots": {
        "name": "Botas Crono",
        "short": "Movimento e dash",
        "description": "Aumenta velocidade e reduz recarga do dash.",
    },
    "blade_relay": {
        "name": "Rele da Lamina",
        "short": "Espada ampliada",
        "description": "Aumenta alcance da espada e ritmo de combate.",
    },
}

BASE_ITEM_KEYS = tuple(ITEM_DEFINITIONS.keys())


@dataclass
class InventoryItem:
    key: str
    level: int = 1
    hybrid_sources: tuple = field(default_factory=tuple)
    timers: dict = field(default_factory=dict)

    @property
    def rank(self):
        if self.key.startswith("relic:"):
            return 3
        if self.hybrid_sources:
            return 2
        return 1

    @property
    def is_hybrid(self):
        return self.rank == 2

    @property
    def is_relic(self):
        return self.rank == 3

    def effect_keys(self):
        if self.hybrid_sources:
            return self.hybrid_sources
        return (self.key,)


class Inventory:
    def __init__(self):
        self.items = {}
        self.active_slots = []
        self.points = 0
        self.fusion_marks = []

    def item_list(self):
        return list(self.items.values())

    def active_items(self):
        return [self.items[key] for key in self.active_slots if key in self.items]

    def get(self, key):
        return self.items.get(key)

    def is_active(self, key):
        return key in self.active_slots

    def add_random_item(self, rng):
        eligible_hybrids = [item for item in self.items.values() if item.is_hybrid and item.level < MAX_ITEM_LEVEL]

        if eligible_hybrids and rng.random() < 0.10:
            return self.add_item(rng.choice(eligible_hybrids).key)

        eligible_base = []
        for key in BASE_ITEM_KEYS:
            if key in self.items and self.items[key].level >= MAX_ITEM_LEVEL:
                continue

            is_fused = False
            for item in self.items.values():
                if item.hybrid_sources and key in item.hybrid_sources:
                    is_fused = True
                    break

            if not is_fused:
                eligible_base.append(key)

        if not eligible_base:
            if eligible_hybrids:
                return self.add_item(rng.choice(eligible_hybrids).key)
            return "duplicate_max", None

        return self.add_item(rng.choice(eligible_base))

    def add_item(self, key):
        if key in self.items:
            item = self.items[key]
            if item.level < MAX_ITEM_LEVEL:
                item.level += 1
                return "level_up", item
            return "duplicate_max", item

        item = InventoryItem(key=key)
        self.items[key] = item
        if len(self.active_slots) < MAX_ACTIVE_ITEMS:
            self.active_slots.append(key)
        return "new", item

    def add_relic(self, relic_source_key):
        """Add a pre-defined relic by its source key (sorted base keys joined by +)."""
        if relic_source_key not in RELIC_DEFINITIONS:
            return "invalid", None
        relic_key = "relic:" + relic_source_key
        sources = tuple(relic_source_key.split("+"))
        if relic_key in self.items:
            item = self.items[relic_key]
            if item.level < MAX_ITEM_LEVEL:
                item.level += 1
                return "level_up", item
            return "duplicate_max", item
        item = InventoryItem(key=relic_key, level=1, hybrid_sources=sources)
        self.items[relic_key] = item
        if len(self.active_slots) < MAX_ACTIVE_ITEMS:
            self.active_slots.append(relic_key)
        return "new", item

    def toggle_active(self, key):
        if key not in self.items:
            return False, "Item nao encontrado."
        if key in self.active_slots:
            self.active_slots.remove(key)
            return True, "Item removido dos ativos."
        if len(self.active_slots) >= MAX_ACTIVE_ITEMS:
            return False, "Slots ativos cheios."
        self.active_slots.append(key)
        return True, "Item equipado."

    def upgrade_with_point(self, key):
        item = self.items.get(key)
        if item is None:
            return False, "Item nao encontrado."

        if item.is_relic:
            cost = RELIC_UPGRADE_COST
        elif item.is_hybrid:
            cost = 3
        else:
            cost = 1

        if self.points < cost:
            return False, f"Sem pontos suficientes (Custa {cost})."

        if item.level >= MAX_ITEM_LEVEL:
            return False, "Item ja esta no nivel maximo."

        self.points -= cost
        item.level += 1
        return True, "Item aprimorado."

    def mark_for_fusion(self, key):
        item = self.items.get(key)
        if item is None:
            return False, "Item nao encontrado."
        if item.level < MAX_ITEM_LEVEL:
            return False, "Fusao exige item nivel 10."
        if item.is_relic:
            return False, "Reliquia nao pode ser fundida."

        # Enforce same-rank rule
        if self.fusion_marks:
            other = self.items.get(self.fusion_marks[0])
            if other and other.rank != item.rank:
                return False, f"So e possivel fundir itens do mesmo ranking (Rank {other.rank})."

        if key in self.fusion_marks:
            self.fusion_marks.remove(key)
            return True, "Marcacao removida."
        if len(self.fusion_marks) >= 2:
            self.fusion_marks = []
        self.fusion_marks.append(key)
        if len(self.fusion_marks) == 2:
            success, preview, message = self.preview_marked_fusion()
            if not success:
                self.fusion_marks = []
                return False, message
            return True, f"Confirme a fusao: {item_display_name(preview)}."
        return True, "Item marcado para fusao."

    def clear_fusion_marks(self):
        self.fusion_marks = []

    def preview_marked_fusion(self):
        return self.preview_fusion(self.fusion_marks)

    def preview_fusion(self, keys):
        if len(keys) != 2:
            return False, None, "Marque dois itens nivel 10 do mesmo ranking."

        first_key, second_key = keys
        first = self.items.get(first_key)
        second = self.items.get(second_key)

        if first is None or second is None or first.key == second.key:
            return False, None, "Fusao invalida."
        if first.level < MAX_ITEM_LEVEL or second.level < MAX_ITEM_LEVEL:
            return False, None, "Fusao exige dois itens nivel 10."
        if first.rank != second.rank:
            return False, None, "So e possivel fundir itens do mesmo ranking."

        combined_sources = tuple(sorted(set(first.effect_keys() + second.effect_keys())))

        if first.rank == 1:
            hybrid_key = "hybrid:" + "+".join(combined_sources)
            hybrid = InventoryItem(key=hybrid_key, level=1, hybrid_sources=combined_sources)
            return True, hybrid, "Item hibrido sera criado."

        if first.rank == 2:
            if len(combined_sources) != 4:
                return False, None, "Fontes da Reliquia se sobrepoem. Escolha hibridos diferentes."
            relic_source_key = "+".join(combined_sources)
            if relic_source_key not in RELIC_DEFINITIONS:
                return False, None, "Combinacao de Reliquia invalida."
            relic_key = "relic:" + relic_source_key
            relic = InventoryItem(key=relic_key, level=1, hybrid_sources=combined_sources)
            return True, relic, "Reliquia sera forjada."

        return False, None, "Fusao nao suportada para este ranking."

    def fuse_marked_items(self):
        success, result_item, message = self.preview_marked_fusion()
        if not success:
            self.fusion_marks = []
            return False, message
        first_key, second_key = self.fusion_marks
        self.fusion_marks = []

        for key in (first_key, second_key):
            self.items.pop(key, None)
            if key in self.active_slots:
                self.active_slots.remove(key)
        self.items[result_item.key] = result_item
        if len(self.active_slots) < MAX_ACTIVE_ITEMS:
            self.active_slots.append(result_item.key)

        if result_item.is_relic:
            return True, "Reliquia forjada!"
        return True, "Item hibrido criado."

    def active_effect_level(self, effect_key):
        total = 0
        for item in self.active_items():
            if effect_key in item.effect_keys():
                total += item.level
        return total

    def active_hybrid_level(self):
        return sum(item.level for item in self.active_items() if item.is_hybrid)

    def active_relic_level(self):
        return sum(item.level for item in self.active_items() if item.is_relic)


def item_display_name(item):
    if item.is_relic:
        relic_key = item.key[len("relic:"):]
        return RELIC_DEFINITIONS.get(relic_key, {}).get("name", "Reliquia Desconhecida")
    if item.is_hybrid:
        names = [ITEM_DEFINITIONS[key]["name"] for key in item.hybrid_sources]
        return "Hibrido: " + " + ".join(names)
    return ITEM_DEFINITIONS[item.key]["name"]


def item_short_description(item):
    if item.is_relic:
        relic_key = item.key[len("relic:"):]
        return RELIC_DEFINITIONS.get(relic_key, {}).get("description", "Aura de fogo giratoria.")
    if item.is_hybrid:
        names = [ITEM_DEFINITIONS[key]["short"] for key in item.hybrid_sources]
        return " + ".join(names) + " | extra: area e recarga"
    return ITEM_DEFINITIONS[item.key]["description"]
