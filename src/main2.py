
from PySide6.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt, QTimer)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap, QPen,
    QRadialGradient)
from PySide6.QtWidgets import *
from PySide6 import QtWidgets
from utils import *
from ui_swiss import *
from classes import *
import json



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
        # self.ui.generateBracket.clicked.connect(self.on_generate_final_bracket_clicked)
        # self.ui.importButton.clicked.connect(self.import_session)
        # self.ui.exportButton.clicked.connect(self.export_session)

        # set column headers in players table
        self.ui.playersTableWidget.setColumnCount(5)
        self.ui.playersTableWidget.setHorizontalHeaderLabels(["Drop", "Name", "Score", "Resistance", "Win Percentage"])
        # self.ui.playersTableWidget.cellChanged.connect(self.on_player_cell_changed)
        self.ui.tabWidget.currentChanged.connect(self.tab_change_controller)

    def tab_change_controller(self, index):
        """
        We recalculate the players table every time we click on the tab
        """
        tabname = self.ui.tabWidget.tabText(index)
        print("Current tab name:", tabname)

        if tabname == "Players":
            self.create_players_table()



    def import_players_from_file(self):
        filename, _ = QFileDialog.getOpenFileName()
        if not filename:
            return
        count = 0

        current_player_names = {player.name.strip().lower() for player in self.players}
        with open(filename, 'r') as f:
            for name in f:
                name = name.strip()
                if not name or name.lower() in current_player_names:
                    print(f"Duplicate name {name}")
                    continue
                new_player = Player(name)
                self.players.append(new_player)
                # self.create_player_table_entry(new_player)
                count += 1
                current_player_names.add(name.lower())
        self.ui.settingsMessage.setText(f"Imported {count} players successfully")


    def import_players_from_clipboard(self):
        data = get_clipboard_data()
        names = data.split('\n')
        count = 0

        current_player_names = {player.name.strip().lower() for player in self.players}
        for name in names:
            name = name.strip()
            if not name or name.lower() in current_player_names:
                    print(f"Duplicate name {name}")
                    continue
            new_player = Player(name)
            self.players.append(new_player)
            # self.create_player_table_entry(new_player)
            count += 1
            current_player_names.add(name.lower())
        self.ui.settingsMessage.setText(f"Imported {count} players successfully")

    def create_players_table(self):
        # First calculate all the players' stats
        player_list = calculate_players_stats(self.players, self.rounds)
        
        # Create the table
        for player in player_list:
            self.create_player_table_entry(player)
        



    def create_player_table_entry(self, player: Player):
        # Get the table row index
        rowPosition = self.ui.playersTableWidget.rowCount()
        self.ui.playersTableWidget.insertRow(rowPosition)
        self.ui.playersTableWidget.setSortingEnabled(True)

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

        if player.n_played:
            player_win_percentage = player.n_wins / player.n_played * 100
        else:
            player_win_percentage = 0

        self.ui.playersTableWidget.setItem(rowPosition, 1, QTableWidgetItem(player.name))
        self.ui.playersTableWidget.setItem(rowPosition, 2, QTableWidgetItem(str(player.score)))
        self.ui.playersTableWidget.setItem(rowPosition, 3, QTableWidgetItem(str(player.resistance)))
        self.ui.playersTableWidget.setItem(rowPosition, 4, QTableWidgetItem(str(player_win_percentage) + "%"))



    def generate_round(self):
        if len(self.players) == 0:
            self.ui.settingsMessage.setText(f"Import players before generating a round!")
            return
        # Generate the matchups and display them
        matchups = generate_matchups(self.players, self.rounds)

        new_round = Round(matchups)
        self.rounds.append(new_round)
        round_number = len(self.rounds)
        for matchup in new_round.matchups:
            if not matchup.player2:
                matchup.winner = matchup.player1
                matchup.score_player1 = 1.0
                matchup.notes = "BYE"

        self.generate_round_tab(new_round, round_number)


    def generate_round_tab(self, round: Round, round_number: int):
        # Create the table for the new round
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["P1", "P2", "Winner", "P1Score", "P2Score", "Notes"])
        table.setSortingEnabled(True)

        for idx, matchup in enumerate(round.matchups):
            table.insertRow(idx)
            winner_combo = QComboBox()
            winner_combo.setEditable(True)
            winner_combo.lineEdit().setReadOnly(True)

            winner_combo.lineEdit().setPlaceholderText("Select winner...")
            winner_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")  # Optional styling

            winner_combo.addItem(matchup.player1)
            if matchup.player2 != "":
                winner_combo.addItem(matchup.player2)

            # If a winner already exists (e.g., for BYEs), select them
            if matchup.winner:
                winner_combo.setCurrentText(matchup.winner)
            else:
                winner_combo.setCurrentIndex(-1)  # Show placeholder, no selection

            # Name columns should not be editable
            p1_item = QTableWidgetItem(matchup.player1)
            p2_item = QTableWidgetItem(matchup.player2)
            p1_item.setFlags(p1_item.flags() & ~Qt.ItemIsEditable)
            p2_item.setFlags(p2_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(idx, 0, p1_item)
            table.setItem(idx, 1, p2_item)

            table.setCellWidget(idx, 2, winner_combo)
            winner_combo.currentTextChanged.connect(lambda _, row=idx, t=table, m=round.matchups: self.on_cell_changed(t, m, row, 2))

            table.setItem(idx, 3, QTableWidgetItem(str(matchup.score_player1)))
            table.setItem(idx, 4, QTableWidgetItem(str(matchup.score_player2)))
            table.setItem(idx, 5, QTableWidgetItem(str(matchup.notes)))

        table.cellChanged.connect(lambda row, col, t=table, m=round.matchups: self.on_cell_changed(t, m, row, col))


        container = QWidget()
        layout = QVBoxLayout(container)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        paste_winners_button = QPushButton("Paste Winners")
        paste_winners_button.clicked.connect(lambda: self.paste_winners(table))
        button_row.addWidget(paste_winners_button)

        delete_button = QPushButton("Delete Round")
        delete_button.setStyleSheet("background-color: lightcoral;")  # visually distinct
        delete_button.clicked.connect(lambda _, t=table, r=round, i=round_number-1: self.confirm_delete_round(t, r, i))
        button_row.addWidget(delete_button)

        layout.addLayout(button_row)

        layout.addWidget(table)
        container.setLayout(layout)

        # Create the tab
        self.ui.tabWidget.addTab(container, f"R{round_number}")
        self.ui.settingsMessage.setText(f"Created round {round_number}.")



    def on_cell_changed(self, table: QTableWidget, matchups: list, row: int, col: int):
        """
        ["P1", "P2", "Winner", "P1Score", "P2Score", "Notes"]
        """
        if col == 2:
            combo = table.cellWidget(row, col)
            winner_name = combo.currentText()
            matchup = matchups[row]
            matchup.winner = winner_name
            if winner_name == matchup.player1:
                matchup.score_player1 = 1.0
                matchup.score_player2 = 0.0
                table.item(row, col+1).setText(f"{matchup.score_player1}")
                table.item(row, col+2).setText(f"{matchup.score_player2}")
            elif winner_name == matchup.player2:
                matchup.score_player1 = 0.0
                matchup.score_player2 = 1.0
                table.item(row, col+1).setText(f"{matchup.score_player1}")
                table.item(row, col+2).setText(f"{matchup.score_player2}")
            print(f"Updated winner for matchup {row} to {winner_name}")
        elif col == 3:
            new_value = table.item(row, col).text()
            matchups[row].score_player1 = float(new_value)
            print(f"Updated p1score matchup {row} to {new_value}")
        elif col == 4:
            new_value = table.item(row, col).text()
            matchups[row].score_player2 = float(new_value)
            print(f"Updated p2score matchup {row} to {new_value}")
        elif col == 5:
            new_value = table.item(row, col).text()
            matchups[row].notes = new_value
            print(f"Updated notes for matchup {row} to {new_value}")


    def paste_winners(self, table):
        # Get clipboard text and split into lines/names
        text = get_clipboard_data()
        winners = [name.strip().lower() for name in text.splitlines() if name.strip()]

        # Go through each row of the table and find matches
        for row in range(table.rowCount()):
            player1_item = table.item(row, 0)
            player2_item = table.item(row, 1)

            if not player1_item or not player2_item:
                continue  # Skip if row is incomplete

            player1 = player1_item.text().strip().lower()
            player2 = player2_item.text().strip().lower()

            # names to players
            for winner in winners:
                if winner == player1 or winner == player2:
                    widget = table.cellWidget(row, 2)
                    if isinstance(widget, QComboBox):
                        index = widget.findText(winner, Qt.MatchFixedString)
                        if index >= 0:
                            widget.setCurrentIndex(index)
                    break  # Move to next row after a match

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
