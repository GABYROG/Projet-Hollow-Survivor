import tkinter as tk



# PARAMÈTRES

WIDTH = 1250
HEIGHT = 800

BACKGROUND_COLOR = "white"
PLAYER_COLOR = "black"
ITEM_COLOR = "red"
HIT_COLOR = "blue"

MAP_WIDTH = 3000
MAP_HEIGHT = 3000

root = tk.Tk()
root.title("Jeu de Collecte - Grande Map")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BACKGROUND_COLOR)
canvas.pack()
