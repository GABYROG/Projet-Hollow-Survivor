from blue_slime import BlueSlime
import random
import pygame
from entities import FastEnemy, TankEnemy, RangedEnemy
from bosses   import BOSS_SEQUENCE
# Paliers de temps (secondes) -> (types, ennemis_par_seconde)
PALIERS = [
    (  0, [BlueSlime],                                        1.0),
    ( 10, [BlueSlime, FastEnemy],                             1.0),
    ( 30, [BlueSlime, FastEnemy, TankEnemy],                  1.5),
    ( 60, [BlueSlime, FastEnemy, TankEnemy, RangedEnemy],     2.0),
    (120, [BlueSlime, FastEnemy, TankEnemy, RangedEnemy],     2.5),
    (240, [BlueSlime, FastEnemy, TankEnemy, RangedEnemy],     3.0),
]
BOSS_TIMES   = [120, 240, 360, 480, 600]
VICTORY_TIME = 1200
MAX_ENEMIES  = 12
class WaveManager:
    def __init__(self):
        self.start_ticks      = 0
        self.elapsed          = 0.0
        self._spawn_accum     = 0.0
        self._last_tick       = 0
        self._boss_index      = 0
        self.boss_killed      = 0
        self.game_won         = False
        self._lava_map_active = False
    def start(self):
        self.start_ticks = pygame.time.get_ticks()
        self._last_tick  = self.start_ticks
    def update(self, gs, now, speed_f=1.0):
        if self.game_won:
            return
        dt_ms = now - self._last_tick
        self._last_tick = now
        self.elapsed = (now - self.start_ticks) / 1000.0
        # Transition map lave à 10 min
        if self.elapsed >= 600 and not self._lava_map_active:
            self._lava_map_active = True
            gs.map_data = gs.lava_map
        if self.elapsed >= VICTORY_TIME:
            self.game_won = True
            return
        rate, types = self._current_rate_and_types()
        if len(gs.enemies) < MAX_ENEMIES:
            self._spawn_accum += rate * (dt_ms / 1000.0) * speed_f
            while self._spawn_accum >= 1.0 and len(gs.enemies) < MAX_ENEMIES:
                self._spawn_accum -= 1.0
                self._spawn_enemy(gs, types)
        self._check_boss_spawn(gs, now)
    def _current_rate_and_types(self):
        rate, types = 1.0, [BlueSlime]
        for (t, t_list, r) in PALIERS:
            if self.elapsed >= t:
                rate, types = r, t_list
        return rate, types
    def _spawn_enemy(self, gs, types):
        cls = random.choice(types)
        e   = cls.spawn_at_border(gs.player.x, gs.player.y)
        if e:
            gs.enemies.append(e)
    def _check_boss_spawn(self, gs, now):
        if self._boss_index >= len(BOSS_SEQUENCE):
            return
        if gs.boss is not None:
            return
        if self.elapsed >= BOSS_TIMES[self._boss_index]:
            cls = BOSS_SEQUENCE[self._boss_index]
            gs.boss = cls(gs.player.x, gs.player.y)
            self._boss_index += 1
            gs.boss_announcement = (now, cls.NAME)
    def on_boss_killed(self):
        self.boss_killed += 1
    def time_str(self):
        t = int(self.elapsed)
        return f"{t//60:02d}:{t%60:02d}"
    def next_boss_in(self):
        if self._boss_index >= len(BOSS_TIMES):
            return -1
        return max(0.0, BOSS_TIMES[self._boss_index] - self.elapsed)
