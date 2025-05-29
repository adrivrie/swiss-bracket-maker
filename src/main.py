
from PySide6.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap,
    QRadialGradient)
from PySide6.QtWidgets import *
from PySide6 import QtWidgets
from utils import *
from ui_swiss import *
from classes import *


class MainWindow(QtWidgets.QMainWindow):
    players: list[Player] = []
    rounds: list[Round] = []

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.ImportPlayersFileButton.clicked.connect(self.import_players_from_file)
        self.ui.importPlayersClipboardButton.clicked.connect(self.import_players_from_clipboard)
        self.ui.generateRound.clicked.connect(self.generate_round)

        # set column headers in players table
        self.ui.playersTableWidget.setColumnCount(4)
        self.ui.playersTableWidget.setHorizontalHeaderLabels(["Drop", "Name", "Score", "Resistance"])


    def import_players_from_file(self):
        filename,  _ = QFileDialog.getOpenFileName()       

        with open(filename, 'r') as f:
            for name in f:
                new_player = Player(name.strip())
                self.players.append(new_player)
                self.create_player_table_entry(new_player)
        self.ui.settingsMessage.setText(f"Imported {len(self.players)} players successfully")


    def import_players_from_clipboard(self):
        data = get_clipboard_data()
        names = data.split('\n')
        for name in names:
            new_player = Player(name.strip())
            self.players.append(new_player)
            self.create_player_table_entry(new_player)
        self.ui.settingsMessage.setText(f"Imported {len(self.players)} players successfully")


    def create_player_table_entry(self, player: Player):
        # Get the table row index
        rowPosition = self.ui.playersTableWidget.rowCount()
        self.ui.playersTableWidget.insertRow(rowPosition)

        # Create a centered checkbox cell
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(lambda state, p=player: self.on_checkbox_state_changed(state, p))
        # Create a widget to hold the layout
        centered_widget = QWidget()
        layout = QHBoxLayout(centered_widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Set the widget in the cell
        self.ui.playersTableWidget.setCellWidget(rowPosition, 0, centered_widget)

        self.ui.playersTableWidget.setItem(rowPosition, 1, QTableWidgetItem(player.name))
        self.ui.playersTableWidget.setItem(rowPosition, 2, QTableWidgetItem(str(player.score)))
        self.ui.playersTableWidget.setItem(rowPosition, 3, QTableWidgetItem(str(player.resistance)))


    def on_checkbox_state_changed(self, state: int, player: Player):
            if state == Qt.CheckState.Checked.value:
                print(f"{player.name} is now dropped.")
                player.dropped = True
            else:
                print(f"{player.name} is now active.")
                player.dropped = False


    def generate_round(self):
        # Check if last round was locked
        if len(self.rounds) >=1 and not self.rounds[-1].locked:
            self.ui.settingsMessage.setText("Previous round is not locked.")
            return

        # Create the table for the new round      
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["P1", "P2", "Winner", "Notes", "P1Score", "P2Score"])

        # Generate the matchups and display them
        matchups = generate_matchups(self.players)
        new_round = Round(matchups)
        self.rounds.append(new_round)
        for idx, matchup in enumerate(matchups):
            table.insertRow(idx)
            # in case of BYE
            winner = Player("")
            p1 = matchup.player1
            if matchup.player2:
                p2 = matchup.player2
            else:
                p2 = Player("-")
                winner = p1
                matchup.score_player1 = 1
            

            table.setItem(idx, 0, QTableWidgetItem(str(p1.name)))
            table.setItem(idx, 1, QTableWidgetItem(str(p2.name)))
            table.setItem(idx, 2, QTableWidgetItem(str(winner.name)))
            table.setItem(idx, 3, QTableWidgetItem(str(matchup.notes)))
            table.setItem(idx, 4, QTableWidgetItem(str(matchup.score_player1)))
            table.setItem(idx, 5, QTableWidgetItem(str(matchup.score_player2)))

        table.cellChanged.connect(lambda row, col, t=table, m=matchups: self.on_cell_changed(t, m, row, col))

        container = QWidget()
        layout = QVBoxLayout(container)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        
        lock_button = QPushButton("Lock Round")
        lock_button.clicked.connect(lambda _, t=table, r=new_round: self.lock_round(t, r))
        button_row.addWidget(lock_button)

        paste_winners_button = QPushButton("Paste Winners")
        paste_winners_button.clicked.connect(lambda: self.paste_winners(table))
        button_row.addWidget(paste_winners_button)

        layout.addLayout(button_row)
    
        layout.addWidget(table)
        container.setLayout(layout)

        # Create the tab
        round_number = len(self.rounds)
        self.ui.tabWidget.addTab(container, f"R{round_number}")
        self.ui.settingsMessage.setText(f"Created round {round_number}.")


    def paste_winners(self, table):
        # Get clipboard text and split into lines/names
        text = get_clipboard_data()
        winners = [name.strip() for name in text.splitlines() if name.strip()]

        # Go through each row of the table and find matches
        for row in range(table.rowCount()):
            player1_item = table.item(row, 0)
            player2_item = table.item(row, 1)

            if not player1_item or not player2_item:
                continue  # Skip if row is incomplete

            player1 = player1_item.text().strip()
            player2 = player2_item.text().strip()

            # names to players
            for winner in winners:
                if winner == player1 or winner == player2:
                    table.setItem(row, 2, QTableWidgetItem(winner))
                    break  # Move to next row after a match

    def on_cell_changed(self, table: QTableWidget, matchups: list, row: int, col: int):
        if col == 0:
            new_value = table.item(row, col).text()
            new_player = get_player_by_name(self.players, new_value)
            matchups[row].player1 = new_player
            print(f"Updated player1 for matchup {row} to {new_player.name}")
        elif col == 1:
            new_value = table.item(row, col).text()
            new_player = get_player_by_name(self.players, new_value)
            matchups[row].player2 = new_player
            print(f"Updated player2 for matchup {row} to {new_player.name}")
        elif col == 2:
            winner_name = table.item(row, col).text()
            winner = get_player_by_name(self.players, winner_name)
            matchups[row].winner = winner
            matchup = get_matchup_by_player(matchups, winner)
            if winner == matchup.player1:
                matchup.score_player1 = 1.0
                table.item(row, col+2).setText("1.0")
            elif winner == matchup.player2:
                matchup.score_player2 = 1.0
                table.item(row, col+3).setText("1.0")
            print(f"Updated winner for matchup {row} to {winner.name}")
        elif col == 3:
            new_value = table.item(row, col).text()
            matchups[row].notes = new_value
            print(f"Updated notes for matchup {row} to {new_value}")
        elif col == 4:
            new_value = table.item(row, col).text()
            matchups[row].score_player1 = float(new_value)
            print(f"Updated p1score matchup {row} to {new_value}")
        elif col == 5:
            new_value = table.item(row, col).text()
            matchups[row].score_player2 = float(new_value)
            print(f"Updated p2score matchup {row} to {new_value}")


    def lock_round(self, table: QTableWidget, round: Round):
        # Disable editing on all editable columns (Winner and Notes)
        row_count = table.rowCount()
        for row in range(row_count):
            for col in [2, 3]:
                item = table.item(row, col)
                if item is not None:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Lock the round
        round.locked = True

        # Update the scores for every player
        for matchup in round.matchups:
            matchup.player1.score += matchup.score_player1
            if matchup.player2:
                matchup.player2.score += matchup.score_player2

        self.update_player_table()

        print("Round locked! Editing disabled.")
    

    def update_player_table(self):
        row_count = self.ui.playersTableWidget.rowCount()

        for row in range(row_count):
            # update score, resistance and matches
            name = self.ui.playersTableWidget.item(row, 1).text()
            player = get_player_by_name(self.players, name)
            print(player)
            self.ui.playersTableWidget.setItem(row, 2, QTableWidgetItem(f"{player.score}"))




if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()