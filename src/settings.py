
from PySide6.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt, QTimer)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap, QPen,
    QRadialGradient, QAction, QKeySequence)
from PySide6.QtWidgets import *
from PySide6 import QtWidgets
from ui_swiss import *
from classes import *
import json

class SettingsDialog(QDialog):
    p1_ext_point = 1.0
    p2_ext_point = 0.0
    random_ext_point_assignment = True
    selected_format = "default"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(320)
        self.setModal(True)
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # --- Extension point distribution ---
        dist_group = QGroupBox("Extension Point Distribution")
        dist_layout = QFormLayout()
        dist_layout.setSpacing(8)

        self.p1_spinbox = QDoubleSpinBox()
        # TODO: range needed? 
        # self.p1_spinbox.setRange(0.0, 1.0)
        self.p1_spinbox.setSingleStep(0.01)
        self.p1_spinbox.setDecimals(1)
        self.p1_spinbox.setValue(self.p1_ext_point)

        self.p2_spinbox = QDoubleSpinBox()
        # TODO: range needed? 
        # self.p2_spinbox.setRange(0.0, 1.0)
        self.p2_spinbox.setSingleStep(0.01)
        self.p2_spinbox.setDecimals(1)
        self.p2_spinbox.setValue(self.p2_ext_point)

        dist_layout.addRow("Player 1:", self.p1_spinbox)
        dist_layout.addRow("Player 2:", self.p2_spinbox)
        dist_group.setLayout(dist_layout)
        layout.addWidget(dist_group)

        self.random_assignment_checkbox = QCheckBox("Random assignment")
        self.random_assignment_checkbox.setChecked(self.random_ext_point_assignment)
        dist_layout.addRow(self.random_assignment_checkbox)

        fmt_group = QGroupBox("Copy Format")
        fmt_layout = QVBoxLayout()
        fmt_layout.setSpacing(6)

        self.fmt_button_group = QButtonGroup(self)

        self.fmt_default = QRadioButton("Default")
        self.fmt_default.setChecked(True)
        self.fmt_option2 = QRadioButton("Format 2")
        self.fmt_option3 = QRadioButton("Format 3")

        self.fmt_button_group.addButton(self.fmt_default, id=1)
        self.fmt_button_group.addButton(self.fmt_option2, id=2)
        self.fmt_button_group.addButton(self.fmt_option3, id=3)

        fmt_layout.addLayout(
            self.create_radio_with_info(
                self.fmt_default,
                "<Player 1 name> (<Player 1 score> / <currently delayed>) — <Player 2 name> (<Player 2 score> / <currently delayed>)"
            )
        )

        fmt_layout.addLayout(
            self.create_radio_with_info(
                self.fmt_option2,
                "Alternative layout with different ordering"
            )
        )

        fmt_layout.addLayout(
            self.create_radio_with_info(
                self.fmt_option3,
                "Compact format for quick sharing"
            )
        )


        fmt_group.setLayout(fmt_layout)
        layout.addWidget(fmt_group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save_settings(self):
        self.p1_ext_point = self.p1_spinbox.value()
        self.p2_ext_point = self.p2_spinbox.value()
        self.random_ext_point_assignment = self.random_assignment_checkbox.isChecked()

        # TODO: create actual formats
        selected_format_id = self.fmt_button_group.checkedId()
        format_names = {1: "default", 2: "format_2", 3: "format_3"}
        self.selected_format = format_names.get(selected_format_id, "default")

        print(f"""Saved the following settings:
Player 1: {self.p1_ext_point}, Player 2: {self.p2_ext_point}
Randomly assigned: {self.random_ext_point_assignment}
Format: {self.selected_format}""")

        self.accept()

    def create_radio_with_info(self, radio_button, tooltip_text):
        layout = QHBoxLayout()
        layout.setSpacing(6)

        # Create info icon using Qt standard icon
        info_label = QLabel()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        info_label.setPixmap(icon.pixmap(14, 14))

        info_label.setToolTip(tooltip_text)

        layout.addWidget(radio_button)
        layout.addWidget(info_label)
        layout.addStretch()

        return layout

    # def create_radio_with_info(self, radio_button, tooltip_text):
    #     layout = QHBoxLayout()
    #     layout.setSpacing(6)

    #     info_label = QLabel()
    #     icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
    #     info_label.setPixmap(icon.pixmap(14, 14))
    #     info_label.setCursor(Qt.CursorShape.PointingHandCursor)
    #     info_label.setToolTip(tooltip_text)

    #     # Toggle state
    #     info_label._open = False

    #     def toggle_info(event):
    #         if not info_label._open:
    #             QWhatsThis.showText(
    #                 info_label.mapToGlobal(info_label.rect().bottomLeft()),
    #                 tooltip_text,
    #                 info_label
    #             )
    #             info_label._open = True
    #         else:
    #             QWhatsThis.hideText()
    #             info_label._open = False

    #     info_label.mousePressEvent = toggle_info

    #     layout.addWidget(radio_button)
    #     layout.addWidget(info_label)
    #     layout.addStretch()

    #     return layout
