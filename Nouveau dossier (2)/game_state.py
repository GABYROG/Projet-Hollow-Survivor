"""game_state.py — Etat central de la session."""
import pygame
from settings      import GOLD_GAIN_BASE, WIDTH, HEIGHT, MAP_W, MAP_H
from entities      import Player, Basket
from world         import MapData
from world         import LavaMapData
from wave_manager  import WaveManager
from experience    import XPSystem
from items         import ItemSystem
class GameState:
    SCREENS = ("menu","weapon_select","playing","level_up","game_over","victory")
    def __init__(self, map_data: MapData):
        self.map_data     = map_data
        self.screen_state = "menu"
        # Persistant
        self.high_score  = 0
        self.gold        = 0
        self.gold_gain   = GOLD_GAIN_BASE
        # Runtime
        self.player       = None
        self.enemies      = []
        self.projectiles  = []
        self.particles    = []
        self.damage_nums  = []
        self.baskets      = []
        self.boss         = None
        self.score        = 0
        self.wave_manager  = None
        self.xp_system     = None
        self.item_system   = None
        self.camera_shake  = 0
        self.boss_announcement  = None
        self.weapon_select_layout = None
        self.lava_map = LavaMapData()
    # ── Nouvelle partie ──
    def start_new_game(self, weapon: str):
        self.score      = 0
        self.enemies    = []
        self.projectiles= []
        self.particles  = []
        self.damage_nums= []
        self.boss       = None
        self.boss_announcement = None
        self.camera_shake = 0
        self.player          = Player()
        self.player.weapons  = [weapon]
        self.player.unlocked_weapons = {weapon}
        self.baskets = [Basket(x, y) for x, y in self.map_data.basket_positions]
        self.wave_manager = WaveManager()
        self.wave_manager.start()
        self.xp_system   = XPSystem()
        self.item_system  = ItemSystem()
        # Lien pour que XPSystem puisse lire les items equipes
        self.player._item_sys = self.item_system
        self.screen_state = "playing"
    # ── Score & Or ──
    def on_kill(self, xp=1):
        self.score += xp
        self.gold  += self.gold_gain * xp
        if self.score > self.high_score:
            self.high_score = self.score
    def on_boss_killed(self):
        self.on_kill(25)
        self.boss = None
        self.wave_manager.on_boss_killed()
    # ── Camera ──
    def get_camera(self):
        import random
        sk = self.camera_shake
        sx = random.randint(-sk, sk) if sk else 0
        sy = random.randint(-sk, sk) if sk else 0
        cx = max(0, min(int(self.player.x) - WIDTH//2,  MAP_W-WIDTH))
        cy = max(0, min(int(self.player.y) - HEIGHT//2, MAP_H-HEIGHT))
        return cx+sx, cy+sy
