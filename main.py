# CJM
from ui.gui import TournamentApp
import data.mongodb_client as m

if __name__ == '__main__':
    m.run_server_in_thread()
    app = TournamentApp()
    app.mainloop()