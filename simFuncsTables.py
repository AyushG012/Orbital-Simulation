import pygame
import tkinter as tk
from sys import platform
import sqlite3

#create connection to database
conn = sqlite3.connect("NEA_database.db")
#get cursor to use db
cur = conn.cursor()

#create tables for saved scenarios
cur.execute("""
            CREATE TABLE if not exists savedScenarios
            (
                sScenarioName   TEXT,
                userName         TEXT,
                PRIMARY KEY (sScenarioName,userName)
            )
        """)

cur.execute("""
            CREATE TABLE if not exists savedScenarioBodyLink
            (
                sScenarioName   TEXT,
                userName         TEXT,
                bodyID          INTEGER PRIMARY KEY, 
                FOREIGN KEY (sScenarioName,userName) REFERENCES savedScenarios(sScenarioName,userName) ON DELETE CASCADE
            )
        """)
cur.execute("""
            CREATE TABLE if not exists savedBodies
            (
                bodyID          integer primary key autoincrement,
                type            text,
                velX            float,
                velY            float,
                ordX            float,
                ordY            float,
                mass            float,
                FOREIGN KEY (bodyID) REFERENCES savedScenarioBodyLink(bodyID) ON DELETE CASCADE
            )
        """)
conn.commit()




#draws an arrow on the pygame window with specified start and end arrows
def draw_arrow(
        surface: pygame.Surface,
        start: pygame.Vector2,
        end: pygame.Vector2,
        color: pygame.Color,
        body_width: int = 4,
        head_width: int = 8,
        head_height: int = 8,
    ):
    """Draw an arrow between start and end with the arrow head at the end.

    Args:
        surface (pygame.Surface): The surface to draw on
        start (pygame.Vector2): Start position
        end (pygame.Vector2): End position
        color (pygame.Color): Color of the arrow
        body_width (int, optional): Defaults to 2.
        head_width (int, optional): Defaults to 4.
        head_height (float, optional): Defaults to 2.
    """
    arrow = start - end
    angle = arrow.angle_to(pygame.Vector2(0, -1))
    body_length = arrow.length() - head_height

    # Create the triangle head around the origin
    head_verts = [
        pygame.Vector2(0, head_height / 2),  # Center
        pygame.Vector2(head_width / 2, -head_height / 2),  # Bottomright
        pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]
    # Rotate and translate the head into place
    translation = pygame.Vector2(0, arrow.length() - (head_height / 2)).rotate(-angle)
    for i in range(len(head_verts)):
        head_verts[i].rotate_ip(-angle)
        head_verts[i] += translation
        head_verts[i] += start

    pygame.draw.polygon(surface, color, head_verts)

    # Stop weird shapes when the arrow is shorter than arrow head
    if arrow.length() >= head_height:
        # Calculate the body rect, rotate and translate into place
        body_verts = [
            pygame.Vector2(-body_width / 2, body_length / 2),  # Topleft
            pygame.Vector2(body_width / 2, body_length / 2),  # Topright
            pygame.Vector2(body_width / 2, -body_length / 2),  # Bottomright
            pygame.Vector2(-body_width / 2, -body_length / 2),  # Bottomleft
        ]
        translation = pygame.Vector2(0, body_length / 2).rotate(-angle)
        for i in range(len(body_verts)):
            body_verts[i].rotate_ip(-angle)
            body_verts[i] += translation
            body_verts[i] += start

        pygame.draw.polygon(surface, color, body_verts)

#returns height of title bar
def getTitleBarHeight():
    newWindow = tk.Tk()
    tk.Frame(newWindow).update_idletasks()
    newWindow.geometry('350x200+100+100')
    newWindow.update_idletasks()
    newWindow.update_idletasks()
    offset_y = 0
    if platform in ('win32', 'darwin'):
        import ctypes
        try: # >= win 8.1
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except: # win 8.0 or less
            ctypes.windll.user32.SetProcessDPIAware()
        offset_y = int(newWindow.geometry().rsplit('+', 1)[-1])

    bar_height = newWindow.winfo_rooty() - offset_y
    newWindow.destroy()
    return bar_height