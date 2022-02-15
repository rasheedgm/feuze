# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'placer.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_placer(object):
    def setupUi(self, placer):
        if not placer.objectName():
            placer.setObjectName(u"placer")
        placer.resize(129, 94)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(placer.sizePolicy().hasHeightForWidth())
        placer.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(placer)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.header = QLabel(placer)
        self.header.setObjectName(u"header")
        sizePolicy.setHeightForWidth(self.header.sizePolicy().hasHeightForWidth())
        self.header.setSizePolicy(sizePolicy)
        self.header.setMinimumSize(QSize(0, 0))
        self.header.setMaximumSize(QSize(166666, 16777215))
        font = QFont()
        font.setPointSize(6)
        font.setBold(True)
        font.setWeight(75)
        self.header.setFont(font)
        self.header.setTextFormat(Qt.RichText)
        self.header.setScaledContents(True)
        self.header.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.header.setWordWrap(True)

        self.verticalLayout.addWidget(self.header)

        self.image = QLabel(placer)
        self.image.setObjectName(u"image")
        sizePolicy.setHeightForWidth(self.image.sizePolicy().hasHeightForWidth())
        self.image.setSizePolicy(sizePolicy)
        self.image.setMinimumSize(QSize(120, 50))
        palette = QPalette()
        brush = QBrush(QColor(255, 255, 255, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Base, brush)
        brush1 = QBrush(QColor(70, 70, 70, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        self.image.setPalette(palette)
        self.image.setAutoFillBackground(True)

        self.verticalLayout.addWidget(self.image)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.footage = QLabel(placer)
        self.footage.setObjectName(u"footage")
        sizePolicy.setHeightForWidth(self.footage.sizePolicy().hasHeightForWidth())
        self.footage.setSizePolicy(sizePolicy)
        self.footage.setFont(font)

        self.horizontalLayout_2.addWidget(self.footage, 0, Qt.AlignLeft)

        self.version_label = QLabel(placer)
        self.version_label.setObjectName(u"version_label")
        sizePolicy.setHeightForWidth(self.version_label.sizePolicy().hasHeightForWidth())
        self.version_label.setSizePolicy(sizePolicy)
        self.version_label.setFont(font)

        self.horizontalLayout_2.addWidget(self.version_label, 0, Qt.AlignRight)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(placer)

        QMetaObject.connectSlotsByName(placer)
    # setupUi

    def retranslateUi(self, placer):
        placer.setWindowTitle(QCoreApplication.translate("placer", u"Form", None))
        self.header.setText(QCoreApplication.translate("placer", u"REEL01/SHOT_011212", None))
        self.image.setText("")
        self.footage.setText(QCoreApplication.translate("placer", u"Render", None))
        self.version_label.setText(QCoreApplication.translate("placer", u"v01", None))
    # retranslateUi

