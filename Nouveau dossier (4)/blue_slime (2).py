import pygame
import math
import random
from settings import MAP_W, MAP_H
from entities import BaseEnemy

# Listes globales qui contiennet les images de chaque animation du slime

frames_attack = []
frames_dead   = []
frames_hurt   = []
frames_run    = []

def load_assets():
    
    global frames_attack, frames_dead, frames_hurt, frames_run
    #Chargement des images d'animation 
    # convert_alpha()  apour but de conserver la transparence des sprites
    for i in range(1, 11):
        frames_attack.append(pygame.image.load(f"attack({i}).png").convert_alpha())
    for i in range(1, 4):
        frames_dead.append(pygame.image.load(f"dead({i}).png").convert_alpha())
    for i in range(1, 7):
        frames_hurt.append(pygame.image.load(f"hurt({i}).png").convert_alpha())
    for i in range(1, 9):
        frames_run.append(pygame.image.load(f"run({i}).png").convert_alpha())

# Dimensions d'un sprite en pixels
frame_width  = 128
frame_height = 128

class BlueSlime(BaseEnemy):
    # Statistiques de base du slime bleu
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
        # Appel de BaseEnemy.__init__ qui initialise la position et les HP 
        super().__init__(x, y)
        self.frame_index     = 0.0   
        self.animation_speed = 0.15  
        self.anim_state      = "run" 

    def update(self, pcx, pcy, now, gs, spd_f=1.0):
        # Décrémente le timer du flash 
        if self.flash > 0: self.flash -= 1
        
        # Applique les effets de dégâts sur la durée 
        self.tick_dots(now, gs)

        # Si le slime est en train de mourir, on joue l'animation jusqu'à la fin sans interruption
        if self.anim_state == "death":
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_dead):
                self.frame_index = len(frames_dead) - 1  # On bloque sur la dernière image
            return  # On sort immédiatement, aucun autre comportement possible

        # Si le slime vient de recevoir un coup, on joue l'animation hurt
        # Une fois terminée, on repasse automatiquement en état "run"
        if self.anim_state == "hurt":
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_hurt):
                self.anim_state  = "run"
                self.frame_index = 0.0

        # Calcul de la position centrale du slime
        ecx, ecy = self.center()
        
        # math.hypot calcule la distance entre entre le slime et le joueur pour déclencher l'attaque
        dist = math.hypot(pcx - ecx, pcy - ecy)

        if dist <= self.SIZE + 20:
            # Ici , le joueur est à portée d'attaque alorson passe en état "attack"
            if self.anim_state != "attack":
                self.anim_state  = "attack"
                self.frame_index = 0.0  # On repart du début de l'animation
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_attack):
                self.frame_index = 0.0  # Animation en boucle
        else:
            # Le joueur est loin alors le slime se déplace vers lui
            if self.anim_state not in ("hurt", "dead"):
                self.anim_state = "run"
            self.frame_index += self.animation_speed
            if self.frame_index >= len(frames_run):
                self.frame_index = 0.0  #Animation en boucle 
            self.move_toward(pcx, pcy, spd_f)  # On déplace le slime vers le joueur 

    def take_hit(self, dmg, angle=0, force=0):
        super().take_hit(dmg, angle, force)  # BaseEnemy calcule les HP et le recul
        if self.hp <= 0:
            self.anim_state  = "dead"       # S'il n y a plus de HP , animation de mort
            self.frame_index = 0.0
        else:
            self.anim_state  = "hurt"        # S'il est encore en vie , animation de dégâts
            self.frame_index = 0.0
    def current_frame(self):
        if self.anim_state == "attack":
            frames = frames_attack
        elif self.anim_state == "dead":
            frames = frames_dead
        elif self.anim_state == "hurt":
            frames = frames_hurt
        else:
            frames = frames_run
        idx = min(int(self.frame_index), len(frames) - 1) #C'est pour éviter de dépasser la dernière image
        return frames[idx]

    @classmethod
    def spawn_at_border(cls, px, py):
         #Appelée directement sur la classe pour créer un slime autour du joueur
        for _ in range(200):
            angle = random.uniform(0, math.pi * 2)
            dist  = random.uniform(480, 700)
            x = px + math.cos(angle) * dist
            y = py + math.sin(angle) * dist
            if 0 <= x <= MAP_W - cls.SIZE and 0 <= y <= MAP_H - cls.SIZE:
                return cls(float(x), float(y))
        return None
