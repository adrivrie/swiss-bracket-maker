
from PySide6.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt, QTimer)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap, QPen,
    QRadialGradient, QAction, QKeySequence)
from PySide6.QtWidgets import *
from PySide6 import QtWidgets
from utils import *
from ui_swiss import *
from classes import *
import json


# because things are often strings, we need to hard disallow
# some names to prevent things from breaking
# all lowercase so we can check `name.lower() in DISALLOWED_NAMES`
DISALLOWED_NAMES = set(
    ["no winner",
     "delayed",
     "select winner..."]
)


class MainWindow(QtWidgets.QMainWindow):
    players: list[Player] = []
    rounds: list[Round] = []

    def __init__(self, launch_data):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Swiss Bracket Maker")

        self.ui.ImportPlayersFileButton.clicked.connect(self.import_players_from_file)
        self.ui.importPlayersClipboardButton.clicked.connect(self.import_players_from_clipboard)
        self.ui.generateRound.clicked.connect(self.generate_round)
        self.ui.generateBracket.clicked.connect(self.on_generate_final_bracket_clicked)
        self.ui.exportButton.clicked.connect(self.export_session)

        # set column headers in players table
        self.ui.playersTableWidget.setColumnCount(5)
        self.ui.playersTableWidget.setHorizontalHeaderLabels(["Drop", "Name", "Score", "Resistance", "Win Percentage"])
        # self.ui.playersTableWidget.cellChanged.connect(self.on_player_cell_changed)
        self.ui.tabWidget.currentChanged.connect(self.tab_change_controller)

        # Check if we loaded from file or not
        print(f"Launching with previous data: {launch_data is not None}")
        if launch_data:
            self.import_session(launch_data)

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
                if name.lower() in DISALLOWED_NAMES:
                    print(f"Disallowed name {name}")
                    continue
                new_player = Player(name)
                self.players.append(new_player)
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
            if name.lower() in DISALLOWED_NAMES:
                print(f"Disallowed name {name}")
                continue
            new_player = Player(name)
            self.players.append(new_player)
            count += 1
            current_player_names.add(name.lower())
        self.ui.settingsMessage.setText(f"Imported {count} players successfully")

    def create_players_table(self):
        # First calculate all the players' stats
        player_info_list = calculate_players_stats(self.players, self.rounds)

        print([(p.player.name, p.score, p.resistance) for p in player_info_list if p.score > 10])

        # Clear the table
        self.ui.playersTableWidget.setSortingEnabled(False)
        self.ui.playersTableWidget.clearContents()
        self.ui.playersTableWidget.setRowCount(0)

        # Create the table
        for player_info in player_info_list:
            self.create_player_table_entry(player_info)

        self.ui.playersTableWidget.setSortingEnabled(True)


    def create_player_table_entry(self, player_info: PlayerInfo):
        # Get the table row index
        rowPosition = self.ui.playersTableWidget.rowCount()
        self.ui.playersTableWidget.insertRow(rowPosition)

        # Create a centered checkbox cell
        checkbox = QCheckBox()
        checkbox.setChecked(player_info.player.dropped)
        checkbox.stateChanged.connect(lambda state, player=player_info.player: self.on_checkbox_state_changed(state, player))
        # Create a widget to hold the layout
        centered_widget = QWidget()
        layout = QHBoxLayout(centered_widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Dropped checkbox
        self.ui.playersTableWidget.setCellWidget(rowPosition, 0, centered_widget)
        # Player name
        self.ui.playersTableWidget.setItem(rowPosition, 1, QTableWidgetItem(player_info.player.name))
        # Score
        player_score = QTableWidgetItem()
        player_score.setData(Qt.ItemDataRole.EditRole, player_info.score)
        self.ui.playersTableWidget.setItem(rowPosition, 2, player_score)
        # TODO: check if double convert is needed with current python version and floats https://stackoverflow.com/questions/455612/limiting-floats-to-two-decimal-points
        # TODO: number styling to be consistent? 0 padding etc
        # Resistance
        player_res = QTableWidgetItem()
        player_res.setData(Qt.ItemDataRole.EditRole, round(player_info.resistance, 2))
        player_res.setData(Qt.ItemDataRole.DisplayRole, f"{round(player_info.resistance, 2)}%")
        self.ui.playersTableWidget.setItem(rowPosition, 3, player_res)
        # self.ui.playersTableWidget.setItem(rowPosition, 3, QTableWidgetItem("{:.2f}%".format(player_info.resistance)))

        # Win percentage
        if player_info.n_played:
            player_win_percentage = player_info.n_wins / player_info.n_played * 100
        else:
            player_win_percentage = 0

        player_win = QTableWidgetItem()
        player_win.setData(Qt.ItemDataRole.EditRole, round(player_win_percentage, 2))
        player_win.setData(Qt.ItemDataRole.DisplayRole, f"{round(player_win_percentage, 2)}%")
        self.ui.playersTableWidget.setItem(rowPosition, 4, player_win)
        # self.ui.playersTableWidget.setItem(rowPosition, 4, QTableWidgetItem("{:.2f}%".format(player_win_percentage)))



    def generate_round(self):
        if len(self.players) == 0:
            self.ui.settingsMessage.setText(f"Import players before generating a round!")
            return

        if not self.confirm_start_round_generation():
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
            winner_combo.addItem("No Winner")
            winner_combo.addItem("Delayed")

            # If a winner already exists (e.g., for BYEs), select them
            if matchup.winner:
                winner_combo.setCurrentText(matchup.winner)
            else:
                winner_combo.setCurrentIndex(-1)  # Show placeholder, no selection

            winner_combo.setProperty("matchup", matchup)

            # Name columns should not be editable
            p1_item = QTableWidgetItem(matchup.player1)
            p2_item = QTableWidgetItem(matchup.player2)
            p1_item.setFlags(p1_item.flags() & ~Qt.ItemIsEditable)
            p2_item.setFlags(p2_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(idx, 0, p1_item)
            table.setItem(idx, 1, p2_item)

            table.setCellWidget(idx, 2, winner_combo)
            winner_combo.currentTextChanged.connect(lambda _, combo=winner_combo, table=table: self.on_winner_changed(combo, table))

            p1_score_item = QTableWidgetItem(str(matchup.score_player1))
            table.setItem(idx, 3, p1_score_item)

            p2_score_item = QTableWidgetItem(str(matchup.score_player2))
            table.setItem(idx, 4, p2_score_item)

            notes_item = QTableWidgetItem(str(matchup.notes))

            table.setItem(idx, 5, notes_item)

            # attach round index and matchup data to the first column
            p1_item.setData(Qt.UserRole, {"round_idx": round_number-1, "matchup": matchup})


        table.cellChanged.connect(self.on_cell_changed)


        container = QWidget()
        layout = QVBoxLayout(container)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        paste_winners_button = QPushButton("Paste Winners")
        paste_winners_button.clicked.connect(lambda: self.paste_winners(table))
        button_row.addWidget(paste_winners_button)

        clipboard_button = QPushButton("Round to Clipboard")
        clipboard_button.clicked.connect(lambda: self.round_to_clipboard(table))
        button_row.addWidget(clipboard_button)

        # TODO: rethink; remove for now, possibly just remove or only for last round or error if not last round or something
        # delete_button = QPushButton("Delete Round")
        # delete_button.setStyleSheet("background-color: lightcoral;")  # visually distinct
        # delete_button.clicked.connect(lambda _, t=table, r=round, i=round_number-1: self.confirm_delete_round(t, r, i))
        # button_row.addWidget(delete_button)

        layout.addLayout(button_row)

        layout.addWidget(table)
        container.setLayout(layout)

        # Create the tab
        self.ui.tabWidget.addTab(container, f"R{round_number}")
        self.ui.settingsMessage.setText(f"Created round {round_number}.")


    def confirm_start_round_generation(self):
        """
        Displays some (possibly worrying) information about the rounds so far
        and asks for confirmation that the next round is to be generated
        """

        # if first round, don't be scared
        if not self.rounds:
            return True

        # otherwise we do some sanity checks
        # first we check if there's delays left from very old rounds
        text = ""
        for i, old_round in enumerate(self.rounds[:-1]):
            delays = 0
            for matchup in old_round.matchups:
                if matchup.winner == "Delayed":
                    delays += 1
            if delays:
                text += f"Round {i+1} still has {delays} delayed matches.\n"

        # then we gather some numbers from the last round
        last_round = self.rounds[-1]
        non_binary_score = False
        delays = 0
        no_winners = 0
        winners = 0
        for matchup in last_round.matchups:
            if not matchup.winner:
                # TODO: maybe allow user to set every unset match to no winner?
                warning_text = f"Matchup {matchup.player1} vs {matchup.player2} has no winner selected!\n"
                warning_text += "If this is intentional, either select \"No Winner\" or \"Delayed\" before generating the next round."
                QMessageBox.warning(self, "Incomplete information", warning_text)
                return False
            elif matchup.winner == "Delayed":
                delays += 1
            elif matchup.winner == "No Winner":
                no_winners += 1
            else:
                winners += 1
            if matchup.score_player1 + matchup.score_player2 not in [0,1]:
                non_binary_score = (matchup.score_player1, matchup.score_player2)
        if non_binary_score:
            text += f"Last round has matches with nonstandard scores, for example {non_binary_score}\n"
        text += f"Last round had {winners} winners, {no_winners} matches without winners and {delays} delayed matches still to be played.\n"
        if delays:
            text += "Delayed matches will count as half a point to each player for the purposes of generating the next round."
        text += "Are you sure you want to generate the next round?"

        reply = QMessageBox.question(
            self,
            "Confirm Round Generation",
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def on_winner_changed(self, combo: QComboBox, table: QTableWidget):
        matchup = combo.property("matchup")

        winner_name = combo.currentText()
        matchup.winner = winner_name
        print(f"{matchup} winner changed to {matchup.winner}")
        if winner_name == matchup.player1:
            matchup.score_player1 = 1.0
            matchup.score_player2 = 0.0
        elif winner_name == matchup.player2:
            matchup.score_player1 = 0.0
            matchup.score_player2 = 1.0
        else:  # No Winner / Delayed
            matchup.score_player1 = 0.0
            matchup.score_player2 = 0.0

        self.update_matchup_row_scores(table, matchup)

    def on_cell_changed(self, row, col):
        table = self.sender()
        item = table.item(row, col)
        # first column stores the data in userrole
        matchup = table.item(row, 0).data(Qt.UserRole)["matchup"]
        if not matchup:
            print(f"Error: item at row {row} and col {col} does not have matchup data attached")
            return

        value = item.text()

        if col == 3:
            matchup.score_player1 = float(value)
            print(f"Updated p1 score in {matchup} to {value}")
        elif col == 4:
            matchup.score_player2 = float(value)
            print(f"Updated p2 score in {matchup} to {value}")
        elif col == 5:
            matchup.notes = value
            print(f"Updated notes in {matchup} to {value}")


    def update_matchup_row_scores(self, table: QTableWidget, matchup: Matchup):
        """
        Updates *the view of* the scores for a single row after updating the winner.
        Is O(N), if that becomes problematic caching a mapping dict can make it essentially
        O(1) but is a bit painful.
        """
        row = self.find_round_row_by_matchup(table, matchup)
        if row == -1:
            print("Error: matchup row to be updated not found")
            return

        # stops `on_cell_changed` from being hit here
        table.blockSignals(True)
        table.item(row, 3).setText(str(matchup.score_player1))
        table.item(row, 4).setText(str(matchup.score_player2))
        table.blockSignals(False)

    def find_round_row_by_matchup(self, table: QTableWidget, matchup: Matchup):
        for row in range(table.rowCount()):
            p1_item = table.item(row, 0)  # first column has the data in UserRole
            if p1_item.data(Qt.UserRole)["matchup"] is matchup:
                return row
        return -1


    def paste_winners(self, table):
        # Get clipboard text and split into lines/names
        text = get_clipboard_data()
        winners = [name.strip().lower() for name in text.splitlines() if name.strip()]

        # Go through each row of the table and find matches
        for row in range(table.rowCount()):
            player1_item = table.item(row, 0)
            player2_item = table.item(row, 1)

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
                    break


    def round_to_clipboard(self, table: QTableWidget):
        round_index = table.item(0, 0).data(Qt.UserRole)["round_idx"]
        print(f"Saving round {round_index+1} to clipboard")
        round = self.rounds[round_index]
        # take into account only previous rounds to get stats pre-round
        player_stats_dict = calculate_players_stats(self.players, self.rounds[:round_index], as_dict=True)

        output_str = ""
        for row in range(table.rowCount()):
            matchup: Matchup = table.item(row, 0).data(Qt.UserRole)["matchup"]
            output_str += self.format_match_for_clipboard(matchup, player_stats_dict) + "\n"

        QApplication.clipboard().setText(output_str)
        print("Copied")


    def format_match_for_clipboard(self, matchup: Matchup, player_stats_dict: dict[str, PlayerInfo]) -> str:
        """
        Just some annoying formatting to turn a matchup into
        `one_name (6.0/1) — other_name (7.0)`
        where 6.0 and 7.0 are their scores, and the /1 indicates one
        currently delayed game for the first player.
        """

        stats1 = player_stats_dict[matchup.player1]
        result = matchup.player1
        result += f" ({stats1.score}"
        if stats1.active_delays:
            result += f"/{stats1.active_delays}"
        result += ") — "
        if not matchup.player2:
            result += "BYE"
        else:
            stats2 = player_stats_dict[matchup.player2]
            result += matchup.player2
            result += f" ({stats2.score}"
            if stats2.active_delays:
                result += f"/{stats2.active_delays}"
            result += ")"

        return result


    def export_session(self):
        # Convert data to dict
        player_dump = {
            player.name: player.dropped for player in self.players
        }
        data = {
            "players": player_dump,
            "rounds": [r.to_dict() for r in self.rounds]
        }

        # Create new file
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Tournament Data",
            "",
            "JSON Files (*.json)"
        )

        if not file_name:
            return

        # Ensure file ends with .json
        if not file_name.endswith(".json"):
            file_name += ".json"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Export Successful", f"Tournament saved to:\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not save file:\n{e}")


    def import_session(self, data):
        # Delete old tabs
        tabs_to_remove = []
        for i in range(self.ui.tabWidget.count())[::-1]:
            tab_text = self.ui.tabWidget.tabText(i)
            if 'R' in tab_text:
                tabs_to_remove.append(i)
        for i in sorted(tabs_to_remove, reverse=True):
            self.ui.tabWidget.removeTab(i)

        # Step 1: Rebuild players
        self.players = []
        for p_name, p_dropped in data.get("players", {}).items():
            p = Player(p_name, dropped=p_dropped)
            self.players.append(p)

        # Step 2: Rebuild rounds and matchups
        self.rounds = []
        for round_number, r_data in enumerate(data.get("rounds", [])):
            matchups = []
            for saved_matchup in r_data["matchups"]:
                p1 = saved_matchup["player1"]
                p2 = saved_matchup["player2"]
                notes = saved_matchup["notes"]

                matchup = Matchup(p1, p2, notes)
                matchup.score_player1 = saved_matchup["score_player1"]
                matchup.score_player2 = saved_matchup["score_player2"]
                matchup.winner = saved_matchup["winner"]

                matchups.append(matchup)
            saved_round = Round(matchups)
            self.rounds.append(saved_round)
            self.generate_round_tab(saved_round, round_number + 1)

        # Make all the tabs
        pass


    def on_checkbox_state_changed(self, state: int, player: Player):
        if state == Qt.CheckState.Checked.value:
            print(f"{player.name} is now dropped.")
            player.dropped = True
        else:
            print(f"{player.name} is now active.")
            player.dropped = False



    def on_generate_final_bracket_clicked(self):
        choice_box = QMessageBox(self)
        choice_box.setWindowTitle("Final Bracket Setup")

        # Clean text with padding and slightly larger font
        choice_box.setText(
            "<div style='padding: 32px; font-size: 11pt;'>"
            "How would you like to select players for the final bracket?"
            "</div>"
        )

        choice_box.setIcon(QMessageBox.Icon.NoIcon)

        # Add buttons
        top_x_button = choice_box.addButton("Top X Players", QMessageBox.ButtonRole.AcceptRole)
        score_cut_button = choice_box.addButton("Score Threshold", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = choice_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        # Style the buttons
        button_style = "padding: 6px 12px; font-size: 9pt;"
        for button in (top_x_button,score_cut_button,cancel_button):
            button.setStyleSheet(button_style)
            button.setMinimumWidth(140)

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

                player_info_list = calculate_players_stats(self.players, self.rounds)
                sorted_players_info = sorted(player_info_list, key=lambda p: (p.score, p.resistance), reverse=True)
                print(sorted_players_info)
                selected_players = sorted_players_info[:num]
                if len(selected_players) == 0:
                    raise ValueError()
                round1_matches = create_bracket(selected_players)
                # TODO: Future work. Create full interactive bracket page
                # bracket = build_full_bracket_from_first_round(round1_matches)
                self.show_classic_bracket(round1_matches)
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
                player_info_list = calculate_players_stats(self.players, self.rounds)
                selected_players_info = [p for p in player_info_list if p.score >= threshold_score]
                if len(selected_players_info) < 2:
                    QMessageBox.warning(self, "Invalid Input", "Not enough players have a high enough score.")
                    return
                sorted_players_info = sorted(selected_players_info, key=lambda p: (p.score, p.resistance), reverse=True)
                round1_matches = create_bracket(sorted_players_info)
                # TODO: Future work. Create full interactive bracket page
                # bracket = build_full_bracket_from_first_round(round1_matches)
                # self.show_classic_bracket(round1_matches)
                dialog.accept()
            except ValueError:
                QMessageBox.warning(self, "Invalid Format", "Enter valid numbers only.")

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()



    def show_classic_bracket(self, matchups: list[Matchup]):
        """
        Displays a single-round bracket as a table for copy-pasting to Excel.
        """

        # Create the table
        table = QTableWidget()

        table.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        copy_action = QAction("Copy", table)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(lambda: self.copy_selection_to_clipboard(table))

        table.addAction(copy_action)

        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["P1", "P2"])
        table.setSortingEnabled(False)

        # Enable multi-cell selection
        table.setSelectionBehavior(QTableWidget.SelectItems)
        table.setSelectionMode(QTableWidget.ExtendedSelection)

        for idx, matchup in enumerate(matchups):
            table.insertRow(idx)
            table.setItem(idx, 0, QTableWidgetItem(matchup.player1))
            table.setItem(idx, 1, QTableWidgetItem(matchup.player2))

        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)

        # Add a copy button for first 2 columns
        copy_button = QPushButton("Copy player columns to clipboard (for exporting to Excel)")
        copy_button.clicked.connect(lambda: self.copy_first_two_columns(table))
        layout.addWidget(copy_button)

        layout.addWidget(table)
        container.setLayout(layout)

        self.ui.tabWidget.addTab(container, "Final Bracket")
        self.ui.settingsMessage.setText("Bracket matchups displayed.")


    def copy_selection_to_clipboard(self, table: QTableWidget):
        selection = table.selectedRanges()
        if not selection:
            return

        selected_range = selection[0]  # contiguous block
        rows = range(selected_range.topRow(), selected_range.bottomRow() + 1)
        cols = range(selected_range.leftColumn(), selected_range.rightColumn() + 1)

        lines = []
        for row in rows:
            line = []
            for col in cols:
                item = table.item(row, col)
                line.append(item.text() if item else "")
            lines.append("\t".join(line))

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)


    def copy_first_two_columns(self, table: QTableWidget):
        rows = table.rowCount()
        output = ""
        for row in range(rows):
            p1 = table.item(row, 0).text() if table.item(row, 0) else ""
            p2 = table.item(row, 1).text() if table.item(row, 1) else ""
            output += f"{p1}\t{p2}\n"
        QApplication.clipboard().setText(output)
        self.ui.settingsMessage.setText("Copied first two columns to clipboard.")


class StartupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Swiss Bracket Maker")
        self.choice = None

        layout = QVBoxLayout(self)
        label = QLabel("How do you want to launch?")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        layout.addStretch(1)

        label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                padding: 20px;
            }
        """)
        label.setMinimumHeight(100)

        button_layout = QHBoxLayout()
        # Spacing between the 2 buttons
        button_layout.setSpacing(16)
        # Margin around the horizontal layout
        button_layout.setContentsMargins(16, 0, 16, 16)
        button_new = QPushButton("New")
        button_prev = QPushButton("Open tournament file")
        button_new.setMinimumSize(160, 36)
        button_prev.setMinimumSize(160, 36)
        button_layout.addWidget(button_new)
        button_layout.addWidget(button_prev)

        button_new.clicked.connect(lambda: self.select("new"))
        button_prev.clicked.connect(lambda: self.select("prev"))

        layout.addLayout(button_layout)

    def select(self, value):
        if value == "prev":
            self.choice = self.read_input_file()

        self.accept()

    def read_input_file(self) -> dict:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Tournament Data",
            "",
            "JSON Files (*.json)"
        )
        if not file_name:
            return
        # Parse the file
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Could not load file:\n{e}")
            return None, None

if __name__ == '__main__':

    app = QtWidgets.QApplication([])

    dialog = StartupDialog()
    dialog.exec()

    # Launch main window based on choice
    print(dialog.choice)
    window = MainWindow(dialog.choice)



    # window = MainWindow()
    window.show()
    app.exec()
