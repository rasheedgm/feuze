import os.path

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import QSize
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QStyle

from feuze.core.constant import Align



class BaseInput(QtWidgets.QWidget):
    supported = ["text", "number", "multiline", "choice", "checkbox", "file", "list"]

    # TODO props, value setter, etc validation

    def __init__(self, name, input_type, label=None, value=None, values=None, align=None):
        super(BaseInput, self).__init__()
        if input_type not in self.supported:
            raise Exception("Input type {} is not supported".format(input_type))

        self.__name = name
        self.__input_type = input_type
        self.__value = value
        self.__values = values
        self.__align = align
        self.__label = label if label is not None else name.title()

        self.__input_widget = QtWidgets.QWidget()
        self.__label_widget = QtWidgets.QWidget()

        if align == Align.VERTICAL:
            self.setLayout(QtWidgets.QVBoxLayout(self))
        else:
            self.setLayout(QtWidgets.QHBoxLayout(self))
            self.__align = Align.HORIZONTAL
        self.layout().setMargin(0)
        self.layout().setSpacing(2)

        self.__create_input()

    def __create_input(self):
        if self.__input_type in ["text", "file", "number"]:
            self.__input_widget = QtWidgets.QLineEdit()
            self.__input_widget.textChanged.connect(self.update_value)
        elif self.__input_type == "multiline":
            self.__input_widget = QtWidgets.QTextEdit()
            self.__input_widget.textChanged.connect(self.update_value)
        elif self.__input_type == "choice":
            self.__input_widget = QtWidgets.QComboBox()
            self.__input_widget.currentTextChanged.connect(self.update_value)
        elif self.__input_type == "checkbox":
            self.__input_widget = QtWidgets.QCheckBox()
            self.__input_widget.stateChanged.connect(self.update_value)
            # TODO make horizontal
        else:
            raise Exception("Unable to create input widget")

        self.__label_widget = QtWidgets.QLabel()
        self.__label_widget.setTextFormat(QtCore.Qt.RichText)
        self.update_label()

        # set initial value if value is passed with init
        if self.__value is not None:
            self.set_value(self.__value)
        else:
            self.update_value()

        self.layout().addWidget(self.__label_widget, 1)
        self.layout().addWidget(self.__input_widget, 3)

    def set_value(self, value):
        if self.__input_type in ["text", "file", "number", "multiline"]:
            self.__input_widget.setText(value)
        elif self.__input_widget == "choice":
            self.__input_widget.setCurrentText(value)
        elif self.__input_type == "checkbox":
            if value:
                self.__input_widget.setCheckState(QtCore.Qt.Checked)
            else:
                self.__input_widget.setCheckState(QtCore.Qt.Unchecked)

    def update_value(self, **kwargs):
        if self.__input_type in ["text", "file", "number"]:
            self.__value = self.__input_widget.text()
        elif self.__input_type == "multiline":
            self.__value = self.__input_widget.toPlainText()
        elif self.__input_type == "choice":
            self.__value = self.__input_widget.currentText()
        elif self.__input_type == "checkbox":
            self.__value = self.__input_widget.checkState() == QtCore.Qt.Checked
        else:
            self.__value = None

    def update_label(self):
        self.__label_widget.setText("<b>{}</b>".format(self.__label))

    def setHidden(self, hidden=True, only_label=False):
        if only_label:
            self.__label_widget.setHidden(hidden)
        else:
            super(BaseInput, self).setHidden(hidden)
        if not hidden:
            # un hide in case hidden only label
            self.__label_widget.setHidden(hidden)

    @property
    def name(self):
        return self.__name

    @property
    def value(self):
        return self.__value

    @property
    def input_widget(self):
        return self.__input_widget


class FileInput(BaseInput):
    def __init__(self, name, label=None, value=None, values=None, align=None):
        super(FileInput, self).__init__(name, "file", label, value, values, align)
        self.action = self.input_widget.addAction(
            QtGui.QIcon(":icons/folder.png"), QtWidgets.QLineEdit.ActionPosition.TrailingPosition
        )
        # QtWidgets.QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon),
        # QtWidgets.QLineEdit.ActionPosition.TrailingPosition
        self.action.triggered.connect(self.get_path_dialogue)

    def get_path_dialogue(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Path"
        )
        self.set_value(os.path.normpath(path))

