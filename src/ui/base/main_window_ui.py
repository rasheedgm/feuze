# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from src.ui.base import icons_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1030, 799)
        MainWindow.setStyleSheet(u"")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(5)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMaximumSize(QSize(220, 220))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)
        self.groupBox.setFont(font)
        self.groupBox.setAutoFillBackground(False)
        self.verticalLayout_6 = QVBoxLayout(self.groupBox)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(5, 5, 5, 5)
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.verticalLayout_6.addWidget(self.label)

        self.projects = QListWidget(self.groupBox)
        QListWidgetItem(self.projects)
        QListWidgetItem(self.projects)
        QListWidgetItem(self.projects)
        self.projects.setObjectName(u"projects")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(2)
        sizePolicy1.setHeightForWidth(self.projects.sizePolicy().hasHeightForWidth())
        self.projects.setSizePolicy(sizePolicy1)

        self.verticalLayout_6.addWidget(self.projects)


        self.verticalLayout.addWidget(self.groupBox)

        self.tab_widget = QTabWidget(self.centralwidget)
        self.tab_widget.setObjectName(u"tab_widget")
        self.tab_widget.setEnabled(True)
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(6)
        sizePolicy2.setHeightForWidth(self.tab_widget.sizePolicy().hasHeightForWidth())
        self.tab_widget.setSizePolicy(sizePolicy2)
        self.tab_widget.setMaximumSize(QSize(220, 16777215))
        font1 = QFont()
        font1.setPointSize(9)
        font1.setBold(True)
        font1.setWeight(75)
        self.tab_widget.setFont(font1)
        self.reel_shot_tab = QWidget()
        self.reel_shot_tab.setObjectName(u"reel_shot_tab")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.reel_shot_tab.sizePolicy().hasHeightForWidth())
        self.reel_shot_tab.setSizePolicy(sizePolicy3)
        self.verticalLayout_3 = QVBoxLayout(self.reel_shot_tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tab_widget.addTab(self.reel_shot_tab, "")
        self.asset_tab = QWidget()
        self.asset_tab.setObjectName(u"asset_tab")
        sizePolicy3.setHeightForWidth(self.asset_tab.sizePolicy().hasHeightForWidth())
        self.asset_tab.setSizePolicy(sizePolicy3)
        self.asset_tab.setMinimumSize(QSize(0, 0))
        self.verticalLayout_4 = QVBoxLayout(self.asset_tab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tab_widget.addTab(self.asset_tab, "")

        self.verticalLayout.addWidget(self.tab_widget)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 2)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox_4 = QGroupBox(self.centralwidget)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy3.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy3)
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.label_2 = QLabel(self.groupBox_4)
        self.label_2.setObjectName(u"label_2")
        sizePolicy3.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy3)
        font2 = QFont()
        font2.setPointSize(20)
        font2.setKerning(False)
        self.label_2.setFont(font2)

        self.verticalLayout_9.addWidget(self.label_2)


        self.verticalLayout_5.addWidget(self.groupBox_4)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(5)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, -1, 5)
        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy3.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy3)
        self.groupBox_2.setFont(font1)
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setSpacing(5)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 5, 5, 5)
        self.add_project = QPushButton(self.groupBox_2)
        self.add_project.setObjectName(u"add_project")
        sizePolicy3.setHeightForWidth(self.add_project.sizePolicy().hasHeightForWidth())
        self.add_project.setSizePolicy(sizePolicy3)
        icon = QIcon()
        icon.addFile(u":/icons/project.png", QSize(), QIcon.Normal, QIcon.Off)
        self.add_project.setIcon(icon)

        self.gridLayout.addWidget(self.add_project, 0, 0, 1, 1)

        self.add_reel = QPushButton(self.groupBox_2)
        self.add_reel.setObjectName(u"add_reel")
        sizePolicy3.setHeightForWidth(self.add_reel.sizePolicy().hasHeightForWidth())
        self.add_reel.setSizePolicy(sizePolicy3)
        icon1 = QIcon()
        icon1.addFile(u":/icons/reel.png", QSize(), QIcon.Normal, QIcon.Off)
        self.add_reel.setIcon(icon1)

        self.gridLayout.addWidget(self.add_reel, 0, 1, 1, 1)

        self.ingest = QPushButton(self.groupBox_2)
        self.ingest.setObjectName(u"ingest")
        icon2 = QIcon()
        icon2.addFile(u":/icons/folder.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.ingest.setIcon(icon2)

        self.gridLayout.addWidget(self.ingest, 1, 0, 1, 1)

        self.add_shot = QPushButton(self.groupBox_2)
        self.add_shot.setObjectName(u"add_shot")
        sizePolicy3.setHeightForWidth(self.add_shot.sizePolicy().hasHeightForWidth())
        self.add_shot.setSizePolicy(sizePolicy3)
        icon3 = QIcon()
        icon3.addFile(u":/icons/shot.png", QSize(), QIcon.Normal, QIcon.Off)
        self.add_shot.setIcon(icon3)

        self.gridLayout.addWidget(self.add_shot, 0, 2, 1, 1)

        self.assign = QPushButton(self.groupBox_2)
        self.assign.setObjectName(u"assign")

        self.gridLayout.addWidget(self.assign, 1, 1, 1, 1)

        self.change_status = QPushButton(self.groupBox_2)
        self.change_status.setObjectName(u"change_status")

        self.gridLayout.addWidget(self.change_status, 1, 2, 1, 1)

        self.gridLayout.setRowStretch(0, 1)
        self.gridLayout.setRowStretch(1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)

        self.horizontalLayout_4.addWidget(self.groupBox_2)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        sizePolicy3.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy3)
        self.groupBox_3.setFont(font1)
        self.gridLayout_2 = QGridLayout(self.groupBox_3)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.gridLayout_2.setRowStretch(0, 1)
        self.gridLayout_2.setColumnStretch(0, 1)

        self.horizontalLayout_4.addWidget(self.groupBox_3)

        self.horizontalLayout_4.setStretch(0, 2)
        self.horizontalLayout_4.setStretch(1, 4)

        self.verticalLayout_5.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")
        font3 = QFont()
        font3.setPointSize(8)
        font3.setBold(True)
        font3.setWeight(75)
        self.label_4.setFont(font3)

        self.verticalLayout_7.addWidget(self.label_4)

        self.types = QListWidget(self.centralwidget)
        QListWidgetItem(self.types)
        QListWidgetItem(self.types)
        QListWidgetItem(self.types)
        self.types.setObjectName(u"types")
        sizePolicy4 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.types.sizePolicy().hasHeightForWidth())
        self.types.setSizePolicy(sizePolicy4)
        self.types.setMaximumSize(QSize(280, 16777215))
        self.types.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.verticalLayout_7.addWidget(self.types)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font3)

        self.verticalLayout_7.addWidget(self.label_3)

        self.details = QTableView(self.centralwidget)
        self.details.setObjectName(u"details")
        sizePolicy4.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy4)
        self.details.setMaximumSize(QSize(280, 16777215))

        self.verticalLayout_7.addWidget(self.details)

        self.verticalLayout_7.setStretch(0, 1)
        self.verticalLayout_7.setStretch(2, 1)
        self.verticalLayout_7.setStretch(3, 22)

        self.horizontalLayout_2.addLayout(self.verticalLayout_7)

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setObjectName(u"scroll_layout")

        self.horizontalLayout_2.addLayout(self.scroll_layout)

        self.horizontalLayout_2.setStretch(0, 1)

        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.verticalLayout_5.setStretch(2, 15)

        self.horizontalLayout.addLayout(self.verticalLayout_5)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 6)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1030, 26))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Deetiem", None))
        self.groupBox.setTitle("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Projects", None))

        __sortingEnabled = self.projects.isSortingEnabled()
        self.projects.setSortingEnabled(False)
        ___qlistwidgetitem = self.projects.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("MainWindow", u"Trance(TRNS)", None));
        ___qlistwidgetitem1 = self.projects.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Kammattipadam(KMT)", None));
        ___qlistwidgetitem2 = self.projects.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Parava(PVD)", None));
        self.projects.setSortingEnabled(__sortingEnabled)

        self.tab_widget.setTabText(self.tab_widget.indexOf(self.reel_shot_tab), QCoreApplication.translate("MainWindow", u"Reel/Shot", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.asset_tab), QCoreApplication.translate("MainWindow", u"Assets", None))
        self.groupBox_4.setTitle("")
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Frolic Browser", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Actions", None))
        self.add_project.setText(QCoreApplication.translate("MainWindow", u"Add Project", None))
        self.add_reel.setText(QCoreApplication.translate("MainWindow", u"Add Reel", None))
        self.ingest.setText(QCoreApplication.translate("MainWindow", u"Ingest", None))
        self.add_shot.setText(QCoreApplication.translate("MainWindow", u"Add Shot", None))
        self.assign.setText(QCoreApplication.translate("MainWindow", u"Assign", None))
        self.change_status.setText(QCoreApplication.translate("MainWindow", u"Change Status", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Filters", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Types", None))

        __sortingEnabled1 = self.types.isSortingEnabled()
        self.types.setSortingEnabled(False)
        ___qlistwidgetitem3 = self.types.item(0)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Render", None));
        ___qlistwidgetitem4 = self.types.item(1)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Quicktime", None));
        ___qlistwidgetitem5 = self.types.item(2)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("MainWindow", u"Plate", None));
        self.types.setSortingEnabled(__sortingEnabled1)

        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Details", None))
    # retranslateUi

