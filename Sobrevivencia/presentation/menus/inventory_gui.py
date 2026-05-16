import pygame

try:
    import pygame_gui
    from pygame_gui.elements import UIWindow, UIButton, UILabel, UIPanel, UIScrollingContainer, UIImage
    from pygame_gui.core import ObjectID
except ImportError:
    pygame_gui = None
    UIWindow = UIButton = UILabel = UIPanel = UIScrollingContainer = UIImage = None

    class ObjectID:
        def __init__(self, class_id=None, object_id=None):
            self.class_id = class_id
            self.object_id = object_id

if __package__:
    from ...data.constants import *
    from ...data.items import ITEM_DEFINITIONS, item_display_name, item_short_description
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import ITEM_DEFINITIONS, item_display_name, item_short_description
    from Sobrevivencia.presentation.ui_utils import hex_color

class InventoryGUI:
    def init_inventory_gui(self):
        self.inv_window = None
        self.item_buttons = {} 
        
    def render_inventory_gui(self, game):
        if pygame_gui is None:
            return []
        # Instead of manual drawing, we check if the window exists
        if not self.inv_window or not self.inv_window.alive():
            self._create_inventory_window(game)
        
        # We don't need to return button_rects anymore, pygame-gui handles events
        return []

    def _create_inventory_window(self, game):
        inv = game.get_inventory(game.menu_player_index)
        
        self.inv_window = UIWindow(
            rect=pygame.Rect((100, 80), (900, 580)),
            manager=self.gui_manager,
            window_display_title=f"INVENTARIO - JOGADOR {game.menu_player_index + 1}" if game.multiplayer else "INVENTARIO",
            object_id="#inventory_window"
        )
        
        # Grid de itens em um painel rolável
        self.scroll_container = UIScrollingContainer(
            relative_rect=pygame.Rect((20, 20), (600, 500)),
            manager=self.gui_manager,
            container=self.inv_window
        )
        
        items = inv.item_list()
        self.item_buttons = {}
        
        slot_size = 64
        spacing = 10
        cols = 7
        
        for i, item in enumerate(items):
            col = i % cols
            row = i // cols
            btn = UIButton(
                relative_rect=pygame.Rect((col * (slot_size + spacing), row * (slot_size + spacing)), (slot_size, slot_size)),
                text="",
                manager=self.gui_manager,
                container=self.scroll_container,
                tool_tip_text=f"{item_display_name(item)} (Nivel {item.level})",
                object_id=ObjectID(class_id="@inventory_item", object_id=f"#{item.slot_key}")
            )
            self.item_buttons[btn] = item
            
        # Painel de detalhes
        self.details_panel = UIPanel(
            relative_rect=pygame.Rect((630, 20), (240, 500)),
            manager=self.gui_manager,
            container=self.inv_window
        )
        
        self.details_title = UILabel(
            relative_rect=pygame.Rect((10, 10), (220, 30)),
            text="Selecione um item",
            manager=self.gui_manager,
            container=self.details_panel
        )
        
        self.details_desc = UILabel(
            relative_rect=pygame.Rect((10, 50), (220, 100)),
            text="",
            manager=self.gui_manager,
            container=self.details_panel
        )

    def handle_inventory_event(self, event):
        if pygame_gui is None:
            return
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in self.item_buttons:
                item = self.item_buttons[event.ui_element]
                self._update_details(item)

    def _update_details(self, item):
        self.details_title.set_text(item_display_name(item))
        self.details_desc.set_text(item_short_description(item))
