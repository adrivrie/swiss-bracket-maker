# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'swissthOOPq.ui'
##
## Created by: Qt User Interface Compiler version 5.14.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap,
    QRadialGradient)
from PySide6.QtWidgets import *
from PySide6 import QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 801, 571))
        self.settings = QWidget()
        self.settings.setObjectName(u"settings")
        self.gridLayoutWidget = QWidget(self.settings)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(10, 10, 301, 251))
        self.settingsGridLayout = QGridLayout(self.gridLayoutWidget)
        self.settingsGridLayout.setObjectName(u"settingsGridLayout")
        self.settingsGridLayout.setContentsMargins(0, 0, 0, 0)
        self.importButton = QPushButton(self.gridLayoutWidget)
        self.importButton.setObjectName(u"importButton")
        self.importButton.setFlat(False)

        self.settingsGridLayout.addWidget(self.importButton, 0, 0, 1, 1)

        self.ImportPlayersFileButton = QPushButton(self.gridLayoutWidget)
        self.ImportPlayersFileButton.setObjectName(u"ImportPlayersFileButton")

        self.settingsGridLayout.addWidget(self.ImportPlayersFileButton, 1, 0, 1, 1)

        self.generateRound = QPushButton(self.gridLayoutWidget)
        self.generateRound.setObjectName(u"generateRound")

        self.settingsGridLayout.addWidget(self.generateRound, 2, 0, 1, 1)

        self.generateBracket = QPushButton(self.gridLayoutWidget)
        self.generateBracket.setObjectName(u"generateBracket")

        self.settingsGridLayout.addWidget(self.generateBracket, 2, 1, 1, 1)

        self.exportButton = QPushButton(self.gridLayoutWidget)
        self.exportButton.setObjectName(u"exportButton")

        self.settingsGridLayout.addWidget(self.exportButton, 0, 1, 1, 1)

        self.importPlayersClipboardButton = QPushButton(self.gridLayoutWidget)
        self.importPlayersClipboardButton.setObjectName(u"importPlayersClipboardButton")

        self.settingsGridLayout.addWidget(self.importPlayersClipboardButton, 1, 1, 1, 1)

        self.settingsMessage = QLabel(self.settings)
        self.settingsMessage.setObjectName("settingsMessage")
        self.settingsMessage.setWordWrap(True)
        self.settingsMessage.setGeometry(QRect(470, 70, 300, 60))
        self.settingsMessage.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.tabWidget.addTab(self.settings, "")
        self.players = QWidget()
        self.players.setObjectName(u"players")
        self.playersTableWidget = QTableWidget(self.players)
        self.playersTableWidget.setObjectName(u"playersTableWidget")
        self.playersTableWidget.setGeometry(QRect(10, 20, 771, 511))
        self.tabWidget.addTab(self.players, "")
        self.logs = QWidget()
        self.logs.setObjectName(u"logs")
        self.tabWidget.addTab(self.logs, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.importButton.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.ImportPlayersFileButton.setText(QCoreApplication.translate("MainWindow", u"Import Players File", None))
        self.generateRound.setText(QCoreApplication.translate("MainWindow", u"Generate Round", None))
        self.generateBracket.setText(QCoreApplication.translate("MainWindow", u"Generate Final Bracket", None))
        self.exportButton.setText(QCoreApplication.translate("MainWindow", u"Export", None))
        self.importPlayersClipboardButton.setText(QCoreApplication.translate("MainWindow", u"Import Players Clipboard", None))
        self.settingsMessage.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.settings), QCoreApplication.translate("MainWindow", u"Settings", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.players), QCoreApplication.translate("MainWindow", u"Players", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.logs), QCoreApplication.translate("MainWindow", u"Logs", None))
    # retranslateUi

