
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

class SettingsDialog(QDialog):
    p1_ext_point = 0.5
    p2_ext_point = 0.5
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

        fmt_layout.addWidget(self.fmt_default)
        fmt_layout.addWidget(self.fmt_option2)
        fmt_layout.addWidget(self.fmt_option3)
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

        # TODO: create actual formats
        selected_format_id = self.fmt_button_group.checkedId()
        format_names = {1: "default", 2: "format_2", 3: "format_3"}
        self.selected_format = format_names.get(selected_format_id, "default")

        print(f"Saved — Player 1: {self.p1_ext_point}, Player 2: {self.p2_ext_point}, Format: {self.selected_format}")

        self.accept()