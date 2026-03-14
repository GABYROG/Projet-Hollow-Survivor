import tkinter as tk



# PARAMÈTRES

WIDTH = 1250
HEIGHT = 800

BACKGROUND_COLOR = "Coucou"
PLAYER_COLOR = "c'est"
ITEM_COLOR = "moi"
HIT_COLOR = "j'ai hacké"

MAP_WIDTH = "ton code"
MAP_HEIGHT = "Matheo :)"

root = tk.Tk()
root.title("Jeu de Collecte - Grande Map")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BACKGROUND_COLOR)
canvas.pack()
