import pygame
import math
import random
from settings import MAP_W, MAP_H
from entities import BaseEnemy

frames_attack = []
frames_dead  = []
frames_hurt   = []
frames_run    = []

def load_assets():
    global frames_attack, frames_death, frames_hurt, frames_run
    for i in range(1, 11):
        frames_attack.append(pygame.image.load(f"attack({i}).png").convert_alpha())
    for i in range(1, 4):
        frames_dead.append(pygame.image.load(f"dead({i}).png").convert_alpha())
    for i in range(1, 7):
        frames_hurt.append(pygame.image.load(f"hurt({i}).png").convert_alpha())
    for i in range(1, 9):
        frames_run.append(pygame.image.load(f"run({i}).png").convert_alpha())
frame_width  = 128
frame_height = 128


class BlueSlime(BaseEnemy):
    HP        = 10
    SPEED     = 2.8
    DMG       = 8
    ATK_CD    = 900
    XP        = 1
    SIZE      = 64
    COLOR     = (60, 150, 255)
    OUTLINE   = (30, 80, 200)
    KB_RESIST = 1.0

    def __init__(self, x, y):
        super().__init__(x, y)
        self.frame_index     = 0.0
        self.animation_speed = 0.15
        self.anim_state      = "run" 

    def update(self, pcx, pcy, now, gs, spd_f=1.0):
        if self.flash > 0: self.flash -= 1
        self.tick_dots(now, gs)

        if self.anim_state == "death":
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_death):
                self.frame_index = len(frames_death) - 1
            return

        if self.anim_state == "hurt":
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_hurt):
                self.anim_state  = "run"
                self.frame_index = 0.0

        ecx, ecy = self.center()
        dist = math.hypot(pcx - ecx, pcy - ecy)

        if dist <= self.SIZE + 20:
            if self.anim_state != "attack":
                self.anim_state  = "attack"
                self.frame_index = 0.0
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_attack):
                self.frame_index = 0.0
        else:
            if self.anim_state not in ("hurt", "death"):
                self.anim_state = "run"
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_run):
                self.frame_index = 0.0
            self.move_toward(pcx, pcy, spd_f)

    def take_hit(self, dmg, angle=0, force=0):
        super().take_hit(dmg, angle, force)
        if self.hp <= 0:
            self.anim_state  = "death"
            self.frame_index = 0.0
        else:
            self.anim_state  = "hurt"
            self.frame_index = 0.0

    def current_frame(self):
        if self.anim_state == "attack":
            frames = frames_attack
        elif self.anim_state == "death":
            frames = frames_death
        elif self.anim_state == "hurt":
            frames = frames_hurt
        else:
            frames = frames_run
        idx = min(int(self.frame_index), len(frames) - 1)
        return frames[idx]

    @classmethod
    def spawn_at_border(cls, px, py):
        for _ in range(200):
            angle = random.uniform(0, math.pi * 2)
            dist  = random.uniform(480, 700)
            x = px + math.cos(angle) * dist
            y = py + math.sin(angle) * dist
            if 0 <= x <= MAP_W - cls.SIZE and 0 <= y <= MAP_H - cls.SIZE:
                return cls(float(x), float(y))
        return None
