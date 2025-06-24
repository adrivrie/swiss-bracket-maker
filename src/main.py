
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
        self.ui.generateBracket.clicked.connect(self.on_generate_final_bracket_clicked)

        # set column headers in players table
        self.ui.playersTableWidget.setColumnCount(4)
        self.ui.playersTableWidget.setHorizontalHeaderLabels(["Drop", "Name", "Score", "Resistance"])


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
                self.create_player_table_entry(new_player)
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
            self.create_player_table_entry(new_player)
            count += 1
            current_player_names.add(name.lower())
        self.ui.settingsMessage.setText(f"Imported {count} players successfully")


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
        if len(self.players) == 0:
            self.ui.settingsMessage.setText(f"Import players before generating a round!")
            return
        # Check if last round was locked
        if len(self.rounds) >=1 and not self.rounds[-1].locked:
            self.ui.settingsMessage.setText("Previous round is not locked.")
            return

        # Create the table for the new round
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["P1", "P2", "Winner", "Notes", "P1Score", "P2Score"])
        table.setSortingEnabled(True)

        # Generate the matchups and display them
        matchups = generate_matchups(self.players)
        new_round = Round(matchups)
        self.rounds.append(new_round)
        round_number = len(self.rounds)
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
                matchup.score_player1 = 1.0


            table.setItem(idx, 0, QTableWidgetItem(str(p1.name)))
            table.setItem(idx, 1, QTableWidgetItem(str(p2.name)))

            combo = QComboBox()
            combo.setEditable(True)
            combo.lineEdit().setReadOnly(True)
            combo.lineEdit().setPlaceholderText("Select winner...")
            combo.setStyleSheet("QComboBox { combobox-popup: 0; }")  # Optional styling

            combo.addItem(p1.name)
            if p2.name != "-":
                combo.addItem(p2.name)

            # If a winner already exists (e.g., for BYEs), select them
            if winner.name:
                combo.setCurrentText(winner.name)
            else:
                combo.setCurrentIndex(-1)  # Show placeholder, no selection

            combo.currentTextChanged.connect(lambda name, row=idx: self.on_winner_changed(row, name, table, matchups))
            table.setCellWidget(idx, 2, combo)

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

        delete_button = QPushButton("Delete Round")
        delete_button.setStyleSheet("background-color: lightcoral;")  # visually distinct
        delete_button.clicked.connect(lambda _, t=table, r=new_round, i=round_number-1: self.confirm_delete_round(t, r, i))
        button_row.addWidget(delete_button)

        layout.addLayout(button_row)

        layout.addWidget(table)
        container.setLayout(layout)

        # Create the tab
        self.ui.tabWidget.addTab(container, f"R{round_number}")
        self.ui.settingsMessage.setText(f"Created round {round_number}.")


    def confirm_delete_round(self, table: QTableWidget, round: Round, round_index: int):
        reply = QMessageBox.question(
            self,
            "Confirm Delete Round",
            f"Are you sure you want to delete Round {round_index + 1}?\n"
            "This will disable editing and undo any scores if the round was locked.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_round(table, round, round_index)


    def delete_round(self, table: QTableWidget, round: Round, round_index: int):
        if round.locked:
            # Undo scores
            for matchup in round.matchups:
                matchup.player1.score -= matchup.score_player1
                if matchup.player2:
                    matchup.player2.score -= matchup.score_player2

            print(f"Reverted scores for round {round_index + 1}")

        # Mark round as deleted
        round.deleted = True
        round.locked = True  # Treat as locked for future checks

        # Disable all editing in table
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            # Disable dropdowns
            widget = table.cellWidget(row, 2)
            if isinstance(widget, QComboBox):
                widget.setEnabled(False)

        # Grey out table (optional styling)
        table.setStyleSheet("color: gray;")

        # Rename tab
        tab_index = round_index + 3
        tab_text = self.ui.tabWidget.tabText(tab_index)
        self.ui.tabWidget.setTabText(tab_index, f"DELETED ({tab_text})")

        # Refresh player table
        self.update_player_table()

    def on_winner_changed(self, row, winner_name, table, matchups):
        if not winner_name.strip():
            print(f"No winner selected for row {row}")
            return  # Do not update scores if blank selected

        winner = get_player_by_name(self.players, winner_name)
        matchup = matchups[row]
        matchup.winner = winner

        if winner == matchup.player1:
            matchup.score_player1 = 1.0
            matchup.score_player2 = 0.0
        elif winner == matchup.player2:
            matchup.score_player2 = 1.0
            matchup.score_player1 = 0.0

        table.setItem(row, 4, QTableWidgetItem(str(matchup.score_player1)))
        table.setItem(row, 5, QTableWidgetItem(str(matchup.score_player2)))

        print(f"Winner for matchup {row} set to {winner.name}")


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


    def on_cell_changed(self, table: QTableWidget, matchups: list, row: int, col: int):
        if col == 0:
            new_value = table.item(row, col).text()
            new_player = get_player_by_name(self.players, new_value)
            matchups[row].player1 = new_player
            print(f"Updated player1 for matchup {row} to {new_player.name}")
        elif col == 1:
            new_value = table.item(row, col).text()
            new_player = get_player_by_name(self.players, new_value)
            if new_player:
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
        if not round.locked:
            # Disable editing on all editable columns (Winner and Notes)
            row_count = table.rowCount()
            for row in range(row_count):
                for col in [2, 3]:
                    item = table.item(row, col)
                    if item is not None:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                widget = table.cellWidget(row, 2)
                if isinstance(widget, QComboBox):
                    widget.setEnabled(False)

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


    def on_generate_final_bracket_clicked(self):
        choice_box = QMessageBox(self)
        choice_box.setWindowTitle("Final Bracket Setup")

        # Clean text with padding and slightly larger font
        choice_box.setText(
            "<div style='padding: 6px; font-size: 11pt;'>"
            "How would you like to select players for the final bracket?"
            "</div>"
        )

        choice_box.setIcon(QMessageBox.Icon.NoIcon)
        choice_box.setMinimumWidth(420)  # Slightly wider than before

        # Add buttons
        top_x_button = choice_box.addButton("Top X Players", QMessageBox.ButtonRole.AcceptRole)
        score_cut_button = choice_box.addButton("Score Threshold", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = choice_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        # Style the buttons with normal font (no bold), slightly larger
        button_style = "padding: 6px 12px; font-size: 10.5pt;"
        top_x_button.setStyleSheet(button_style)
        score_cut_button.setStyleSheet(button_style)
        cancel_button.setStyleSheet(button_style)

        # Show the message box
        choice_box.exec()

        selected_button = choice_box.clickedButton()

        if selected_button == top_x_button:
            self.show_top_x_input()
        elif selected_button == score_cut_button:
            self.show_score_threshold_input()



    def show_top_x_input(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Top X Players")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Enter number of top players (must be a power of 2):"))
        input_field = QLineEdit()
        layout.addWidget(input_field)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def on_ok():
            try:
                num = int(input_field.text())
                if num < 2 or (num & (num - 1)) != 0:
                    QMessageBox.warning(self, "Invalid Input", "Number must be a power of 2 (e.g. 2, 4, 8...).")
                    return
                if num > len(self.players):
                    QMessageBox.warning(self, "Invalid Input", "More players selected than are listed.")
                    return
                sorted_players = sorted(self.players, key=lambda p: p.score, reverse=True)
                selected_players = sorted_players[:num]
                if len(selected_players) == 0:
                    raise ValueError()
                round1_matches = create_bracket(selected_players)
                bracket = build_full_bracket_from_first_round(round1_matches)
                print(bracket)
                self.show_classic_bracket(bracket)
                dialog.accept()
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid integer.")

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()


    def show_score_threshold_input(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Score Threshold")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Enter score threshold (e.g. 5 points/wins):"))
        input_field = QLineEdit()
        layout.addWidget(input_field)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def on_ok():
            text = input_field.text().strip()
            try:
                wins = int(text)
                threshold_score = wins  # Adjust if you use a different score metric
                selected_players = [p for p in self.players if p.score >= threshold_score]
                if len(selected_players) < 2:
                    QMessageBox.warning(self, "Invalid Input", "Not enough players have a high enough score.")
                    return
                sorted_players = sorted(selected_players, key=lambda p: p.score, reverse=True)
                round1_matches = create_bracket(sorted_players)
                bracket = build_full_bracket_from_first_round(round1_matches)
                print(bracket)
                self.show_classic_bracket(bracket)
                dialog.accept()
            except ValueError:
                QMessageBox.warning(self, "Invalid Format", "Enter valid numbers only.")

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()




if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
