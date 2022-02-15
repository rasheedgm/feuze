from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QDialog, QListWidget, QWidget,
    QStackedWidget, QHBoxLayout, QFormLayout,
    QLineEdit, QRadioButton, QLabel, QCheckBox, QVBoxLayout, QAction, QDialogButtonBox
)
from PySide2.QtCore import Qt

from src.core import configs
from src.core.constant import Align
from src.ui.base.input import BaseInput, FileInput


class SettingWindow(QDialog):

    def __init__(self, parent):
        super(SettingWindow, self).__init__(parent)
        self.user_config = configs.UserConfig
        self.user_setting_fields = None
        self.setting_list = QListWidget()
        self.setting_list.insertItem(0, 'General')
        self.setting_list.insertItem(1, 'Software')

        self.stack_general = QWidget()
        self.stack_software = QWidget()

        self.set_general_ui()
        self.set_software_ui()

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.stack_general)
        self.stack.addWidget(self.stack_software)

        self.btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )

        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self.reject)

        hbox = QHBoxLayout()
        hbox.addWidget(self.setting_list, 1)
        hbox.addWidget(self.stack, 3)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.btn_box)
        self.setLayout(vbox)

        self.setting_list.currentRowChanged.connect(self.display)
        self.setWindowTitle('Settings')
        self.setParent(parent)

        self.setWindowIcon(QIcon(":icon/settings.png"))

        # self.show()
        # self.addAction(QAction("Ok"))
        
    def accept(self):
        fields = {f.name: f.value for f in self.user_setting_fields if f.value is not None}
        print(fields)
        self.user_config.update(**fields)
        super(SettingWindow, self).accept()


    def set_general_ui(self):
        layout = QFormLayout()
        central_project_path = FileInput(
            "central_project_path",
            label="Central Project Path",
            value=self.user_config.central_project_path or ""
        )
        local_project_path = FileInput(
            "local_project_path",
            label="Local Project Path",
            value=self.user_config.local_project_path or ""
        )
        layout.addRow(central_project_path)
        layout.addRow(local_project_path)
        self.stack_general.setLayout(layout)
        self.user_setting_fields = [
            central_project_path,
            local_project_path
        ]

    def set_software_ui(self):
        layout = QFormLayout()
        sex = QHBoxLayout()
        sex.addWidget(QRadioButton("Male"))
        sex.addWidget(QRadioButton("Female"))
        layout.addRow(QLabel("Sex"), sex)
        layout.addRow("Date of Birth", QLineEdit())

        self.stack_software.setLayout(layout)

    def display(self, i):
        self.stack.setCurrentIndex(i)
