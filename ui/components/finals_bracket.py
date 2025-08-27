"""
Finals bracket window for the tournament application.
"""

import tkinter as tk

class FinalsBracket(tk.Toplevel):
    def __init__(self, parent, schedule, settings):
        super().__init__(parent)
        self.parent = parent
        self.schedule = schedule
        self.settings = settings

        self.title("SCORIX Finals Bracket")
        self.geometry("850x600")

        self.canvas = tk.Canvas(self, bg=self.settings.get("theme_color", "#f0f0f0"))
        self.canvas.pack(fill="both", expand=True)

        self.BOX_WIDTH = 180
        self.BOX_HEIGHT = 45
        self.WIN_COLOR = "#d4edda"
        self.LOSE_COLOR = "#f8d7da"
        self.NORMAL_COLOR = "#ffffff"
        self.HOVER_COLOR = "#e2e6ea"

        self.draw_bracket()

    def draw_bracket(self):
        self.canvas.delete("all")
        semifinals = [m for m in self.schedule.get('finals', []) if m['round'] == 'semifinal']
        if not semifinals:
            return

        sf1_y, sf2_y = 150, 450
        final_y = (sf1_y + sf2_y) / 2
        third_y = final_y + 120
        col1_x, col2_x, col3_x = 20, 320, 620

        # Draw Bracket Structure
        self.canvas.create_line(col1_x + self.BOX_WIDTH, sf1_y, col2_x, sf1_y, width=2)
        self.canvas.create_line(col1_x + self.BOX_WIDTH, sf2_y, col2_x, sf2_y, width=2)
        self.canvas.create_line(col2_x, sf1_y, col2_x, sf2_y, width=2)
        self.canvas.create_line(col2_x + self.BOX_WIDTH, final_y, col3_x, final_y, width=2)
        self.canvas.create_line(col2_x + self.BOX_WIDTH, third_y, col2_x + self.BOX_WIDTH + 50, third_y, width=2)

        # Draw Titles
        self.canvas.create_text(col1_x + self.BOX_WIDTH / 2, 50, text="Semifinals", font=("Arial", 14, "bold"))
        self.canvas.create_text(col2_x + self.BOX_WIDTH / 2, 50, text="Final", font=("Arial", 14, "bold"))
        self.canvas.create_text(col3_x + 20, 50, text="Champion", font=("Arial", 14, "bold"), anchor="w")
        self.canvas.create_text(col2_x + self.BOX_WIDTH / 2, third_y - 60, text="3rd Place Match", font=("Arial", 12, "bold"))

        # Draw Matches
        sf1, sf2 = semifinals[0], semifinals[1]
        self.draw_match(col1_x, sf1_y, sf1)
        self.draw_match(col1_x, sf2_y, sf2)

        if "winner" in sf1 and "winner" in sf2:
            winner1, loser1 = (sf1["team1"], sf1["team2"]) if sf1["winner"] == sf1["team1"] else (sf1["team2"], sf1["team1"])
            winner2, loser2 = (sf2["team1"], sf2["team2"]) if sf2["winner"] == sf2["team1"] else (sf2["team2"], sf2["team1"])
            self.draw_match(col2_x, final_y, {"team1": winner1, "team2": winner2, "round": "final"})
            self.draw_match(col2_x, third_y, {"team1": loser1, "team2": loser2, "round": "third"})

    def draw_match(self, x, y, match):
        """Draw a match box with team names"""
        color1 = self.WIN_COLOR if match.get("winner") == match["team1"] else self.NORMAL_COLOR
        color2 = self.WIN_COLOR if match.get("winner") == match["team2"] else self.NORMAL_COLOR
        
        # Top team box
        self.canvas.create_rectangle(x, y - self.BOX_HEIGHT/2, x + self.BOX_WIDTH, y, fill=color1)
        self.canvas.create_text(x + self.BOX_WIDTH/2, y - self.BOX_HEIGHT/4, text=match["team1"])
        
        # Bottom team box
        self.canvas.create_rectangle(x, y, x + self.BOX_WIDTH, y + self.BOX_HEIGHT/2, fill=color2)
        self.canvas.create_text(x + self.BOX_WIDTH/2, y + self.BOX_HEIGHT/4, text=match["team2"])
