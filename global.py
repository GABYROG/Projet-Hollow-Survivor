# -*- coding: utf-8 -*-
"""
Created on Fri Nov 21 17:52:51 2025

@author: gabri
"""
 
import random
import time

import paramètre as pr 


# JOUEUR

player_width = 50
player_height = 50
player_x = pr.MAP_WIDTH // 2
player_y = pr.MAP_HEIGHT // 2
player_speed = 10

move_left = move_right = move_up = move_down = False

# PV joueur
player_max_hp = 5
player_hp = player_max_hp



# ENNEMI

item_width = 30
item_height = 30
item_speed = 10

# PV ennemis
enemy_hp_max = 3
enemy_hp = enemy_hp_max





# Attaque ennemie
enemy_attack_speed = 800  # ms entre deux attaques
enemy_last_attack_time = 0  

# Stats
score = 0
high_score = 0
missed_items = 0
player_gold = 0
gold_gain = 100


# CAMERA

def get_camera_offset():
    cam_x = player_x - pr.WIDTH // 2
    cam_y = player_y - pr.HEIGHT // 2
    cam_x = max(0, min(cam_x, pr.MAP_WIDTH - pr.WIDTH))
    cam_y = max(0, min(cam_y, pr.MAP_HEIGHT - pr.HEIGHT))
    return cam_x, cam_y


# TEXTURE DE MAP

def draw_map_texture(cam_x, cam_y):
    square_size = 50
    color1 = "#7AC957"  # vert clair
    color2 = "#6AB04C"  # vert foncé

    for x in range(0, pr.MAP_WIDTH, square_size):
        for y in range(0, pr.MAP_HEIGHT, square_size):
            draw_x = x - cam_x
            draw_y = y - cam_y

            # Couleur de base damier
            color = color1 if (x // square_size + y // square_size) % 2 == 0 else color2
            pr.canvas.create_rectangle(
                draw_x, draw_y,
                draw_x + square_size, draw_y + square_size,
                fill=color, outline=""
            )


# ENNEMI : respawn loin du joueur

def respawn_item_far_from_player():
    global item_x, item_y, enemy_hp
    enemy_hp = enemy_hp_max

    while True:
        x = random.randint(0, pr.MAP_WIDTH - item_width)
        y = random.randint(0, pr.MAP_HEIGHT - item_height)

        dx = x - player_x
        dy = y - player_y
        dist = (dx*dx + dy*dy)**0.5

        if dist > 300 and dist <3000:
            item_x, item_y = x, y
            break

respawn_item_far_from_player()
# Mort de l’ennemi
if enemy_hp <= 0:
    respawn_item_far_from_player()
    player_gold += gold_gain

# DESSIN

def draw_game():
    pr.canvas.delete("all")
    cam_x, cam_y = get_camera_offset()

    draw_map_texture(cam_x, cam_y)

    # Joueur
    pr.canvas.create_rectangle(
        player_x - cam_x-25,
        player_y - cam_y-25,
        player_x - cam_x + player_width-25,
        player_y - cam_y + player_height-25,
        fill=pr.PLAYER_COLOR
    )

    

    # Ennemi
    pr.canvas.create_rectangle(
        item_x - cam_x-15,
        item_y - cam_y-15,
        item_x - cam_x + item_width-15,
        item_y - cam_y + item_height-15,
        fill=pr.ITEM_COLOR
    )

    # PV ennemis
    pr.canvas.create_text(
        item_x - cam_x + item_width/2,
        item_y - cam_y - 25,
        text=f"{enemy_hp}/{enemy_hp_max}",
        fill="red",
        font=("Arial", 14)
    )

    # HUD
    pr.canvas.create_text(10, 10, text=f"Score: {score}", anchor="nw", font=("Arial", 14))
    pr.canvas.create_text(10, 30, text=f"High Score: {high_score}", anchor="nw", font=("Arial", 14))
    pr.canvas.create_text(10, 50, text=f"PV: {player_hp}", anchor="nw", font=("Arial", 14), fill="red")
    pr.canvas.create_text(10, 70, text=f"Or: {player_gold}", anchor="nw", font=("Arial", 14))


# DÉPLACEMENT

def move_player():
    global player_x, player_y
    if move_left and player_x > 0:
        player_x -= player_speed
    if move_right and player_x < pr.MAP_WIDTH - player_width:
        player_x += player_speed
    if move_up and player_y > 0:
        player_y -= player_speed
    if move_down and player_y < pr.MAP_HEIGHT - player_height:
        player_y += player_speed


# UPDATE

def update_game():
    global item_x, item_y, score, high_score, player_gold, player_hp
    global enemy_hp, enemy_last_attack_time

    dx = player_x - item_x
    dy = player_y - item_y
    dist = (dx * dx + dy * dy) ** 0.5

    # Déplacement ennemi
    if dist != 0:
        move_dist = min(item_speed, dist)
        item_x += (dx / dist) * move_dist
        item_y += (dy / dist) * move_dist

    # Collision joueur/ennemi
    if (player_x < item_x + item_width and player_x + player_width > item_x and
        player_y < item_y + item_height and player_y + player_height > item_y):

        now = int(time.time() * 1000)  # temps en ms

        if now - enemy_last_attack_time >= enemy_attack_speed:
            enemy_last_attack_time = now

            # le joueur prend un coup
            player_hp -= 1

            # Mort du joueur
            if player_hp <= 0:
                return game_over()

    move_player()
    draw_game()
    pr.root.after(20, update_game)


# AMÉLIORATIONS

def buy_increase_player_speed(event=None):
    global player_gold, player_speed
    if player_gold >= 100:
        player_gold -= 100
        player_speed += 2
    show_menu()

def buy_more_coin_per_enemy(event=None):
    global player_gold, gold_gain
    if player_gold >= 100:
        player_gold -= 100
        gold_gain += 5
    show_menu()
def buy_more_hp(event=None):
    global player_gold,player_hp,player_max_hp
    if player_gold>=100:
        player_gold-=100
        player_max_hp +=1
    show_menu()


# MENU

def show_menu():
    pr.canvas.delete("all")

    pr.canvas.create_text(pr.WIDTH//2, 80, text="trial of death", font=("Arial", 30))
    pr.canvas.create_text(pr.WIDTH//2, 140, text=f"Meilleur score : {high_score}", font=("Arial", 16))
    pr.canvas.create_text(pr.WIDTH//2, 170, text=f"Or : {player_gold}", font=("Arial", 16))
    pr.canvas.create_text(pr.WIDTH//2, 200, text=f"PV max : {player_max_hp}", font=("Arial", 16))

    pr.canvas.create_text(pr.WIDTH//2, 260, text="Améliorations :", font=("Arial", 18))
    pr.canvas.create_text(pr.WIDTH//2, 330, text="1: +2 vitesse joueur  — 100 or", font=("Arial", 14))
    pr.canvas.create_text(pr.WIDTH//2, 360, text="2: +5 or par kill     — 100 or", font=("Arial", 14))
    pr.canvas.create_text(pr.WIDTH//2, 390, text="3: + 1 PV   — 100 or", font=("Arial", 14))
    pr.canvas.create_text(pr.WIDTH//2, 430, text="Appuie sur ENTRÉE pour jouer", font=("Arial", 16))

    pr.root.bind("<Return>", start_game)
    pr.root.bind("<KeyPress-1>", buy_increase_player_speed)
    pr.root.bind("<KeyPress-2>", buy_more_coin_per_enemy)
    pr.root.bind("<KeyPress-3>",buy_more_hp)



# GAME OVER

def game_over():
    pr.canvas.delete("all")
    pr.canvas.create_text(pr.WIDTH//2, pr.HEIGHT//3, text="GAME OVER", font=("Arial", 30), fill="red")
    pr.canvas.create_text(pr.WIDTH//2, pr.HEIGHT//3 + 50, text=f"Score final : {score}", font=("Arial", 18))
    pr.canvas.create_text(pr.WIDTH//2, pr.HEIGHT//3 + 100, text="Appuie sur ÉCHAP pour retourner au menu", font=("Arial", 14))
    pr.root.bind("<Escape>", return_to_menu)

def return_to_menu(event=None):
    show_menu()


# START GAME

def start_game(event=None):
    global score, missed_items, player_hp, enemy_hp
    global player_x, player_y, enemy_last_attack_time

    score = 0
    missed_items = 0
    player_hp = player_max_hp
    enemy_hp = enemy_hp_max
    enemy_last_attack_time = 0

    player_x = pr.MAP_WIDTH // 2
    player_y = pr.MAP_HEIGHT // 2

    respawn_item_far_from_player()
    update_game()

    pr.root.bind("<q>", lambda e: set_move("left", True))
    pr.root.bind("<d>", lambda e: set_move("right", True))
    pr.root.bind("<z>", lambda e: set_move("up", True))
    pr.root.bind("<s>", lambda e: set_move("down", True))

    pr.root.bind("<KeyRelease-q>", lambda e: set_move("left", False))
    pr.root.bind("<KeyRelease-d>", lambda e: set_move("right", False))
    pr.root.bind("<KeyRelease-z>", lambda e: set_move("up", False))
    pr.root.bind("<KeyRelease-s>", lambda e: set_move("down", False))

def set_move(direction, state):
    global move_left, move_right, move_up, move_down
    if direction == "left": move_left = state
    if direction == "right": move_right = state
    if direction == "up": move_up = state
    if direction == "down": move_down = state


show_menu()
pr.root.mainloop()
