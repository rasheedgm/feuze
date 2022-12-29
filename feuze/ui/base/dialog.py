from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QLabel

from feuze.ui.base import input


class BaseDialog(QDialog):
    """Base class for dialog"""

    def __init__(self, parent, inputs=None, msg="", title=""):
        super(BaseDialog, self).__init__(parent)
        main_layout = QVBoxLayout()
        self.input_layout = QVBoxLayout()

        self.all_fields = {}

        self.msg = QLabel(msg)
        self.input_layout.addWidget(self.msg)

        self.setWindowTitle(title)

        if inputs:
            self.set_inputs(inputs)

        self.btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )

        main_layout.addLayout(self.input_layout)
        main_layout.addWidget(self.btn_box)

        self.setLayout(main_layout)

        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self.reject)

    def accept(self):
        super(BaseDialog, self).accept()

    def set_msg(self, msg):
        self.msg.setText(msg)

    def set_inputs(self, inputs):
        widgets = self.all_fields.copy()
        for name, widget in widgets.items():
            if name not in [i["name"] for i in inputs]:
                self.input_layout.removeWidget(widget)
                widget.deleteLater()
                self.all_fields.pop(name)

        for field in inputs:
            name = field["name"]
            if name not in self.all_fields.keys():
                if field["input_type"] == "file":
                    del field["input_type"]
                    self.all_fields[name] = input.FileInput(**field)
                else:
                    self.all_fields[field["name"]] = input.BaseInput(**field)
                self.input_layout.addWidget(self.all_fields[name])

    def get_text(self, title="Get Text", message=None, default=None):
        """Dialog with single text input"""

        if not message:
            message = "Please enter a text"

        self.set_msg(message)

        self.setWindowTitle(title)

        self.set_inputs([{"name": "__field", "input_type": "text", "value": default}])
        self.all_fields["__field"].setHidden(True, only_label=True)
        self.exec_()
        if self.result():
            return  self.all_fields["__field"].value, True
        else:
            return None, False

