import datetime
import os
# TODO clean imports
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets

from feuze.core import configs
from feuze.core.constant import Align
from feuze.core.fold import get_all_projects, Reel, Shot, Footage, FootageTypes
from feuze.ui.base.dialog import BaseDialog
from feuze.ui.base.input import BaseInput, FileInput
from feuze.ui.widgets import IngestListItem


class SettingWindow(QtWidgets.QDialog):

    def __init__(self, parent):
        super(SettingWindow, self).__init__(parent)
        self.user_config = configs.UserConfig
        self.user_setting_fields = None
        self.setting_list = QtWidgets.QListWidget()
        self.setting_list.insertItem(0, 'General')
        self.setting_list.insertItem(1, 'Software')

        self.stack_general = QtWidgets.QWidget()
        self.stack_software = QtWidgets.QWidget()

        self.set_general_ui()
        self.set_software_ui()

        self.stack = QtWidgets.QStackedWidget(self)
        self.stack.addWidget(self.stack_general)
        self.stack.addWidget(self.stack_software)

        self.btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self
        )

        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self.reject)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.setting_list, 1)
        hbox.addWidget(self.stack, 3)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.btn_box)
        self.setLayout(vbox)

        self.setting_list.currentRowChanged.connect(self.display)
        self.setWindowTitle('Settings')
        self.setParent(parent)

        self.setWindowIcon(QtGui.QIcon(":icon/settings.png"))

        # self.show()
        # self.addAction(QAction("Ok"))
        
    def accept(self):
        fields = {f.name: f.value for f in self.user_setting_fields if f.value is not None}
        self.user_config.update(**fields)
        super(SettingWindow, self).accept()

    def set_general_ui(self):
        layout = QtWidgets.QFormLayout()
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
        # TODO
        layout = QtWidgets.QFormLayout()
        sex = QtWidgets.QHBoxLayout()
        sex.addWidget(QtWidgets.QRadioButton("Male"))
        sex.addWidget(QtWidgets.QRadioButton("Female"))
        layout.addRow(QtWidgets.QLabel("Sex"), sex)
        layout.addRow("Date of Birth", QtWidgets.QLineEdit())

        self.stack_software.setLayout(layout)

    def display(self, i):
        self.stack.setCurrentIndex(i)


class IngestInputs(QtWidgets.QDialog):
    
    def __init__(self, parent):
        super(IngestInputs, self).__init__(parent)
        self._path = None
        self.setWindowTitle("Ingest Inputs")
        self.setWindowIcon(QtGui.QIcon(":icons/document.png"))
        vbox = QtWidgets.QVBoxLayout()
        self.browse_button = QtWidgets.QPushButton(QtGui.QIcon(":icons/folder.png"), "Browse Folder")
        vbox.addWidget(self.browse_button)
        self.fold_list = QtWidgets.QTreeWidget()
        # self.fold_list.setHeaderHidden(True)
        self.fold_list.setColumnCount(3)
        self.fold_list.setHeaderItem(QtWidgets.QTreeWidgetItem(["From", "Type", "Name"]))
        vbox.addWidget(self.fold_list)

        bottom_box = QtWidgets.QHBoxLayout()
        self.progress = QtWidgets.QProgressBar()
        self.ingest_button = QtWidgets.QPushButton("Ingest")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        bottom_box.addWidget(self.progress)
        bottom_box.addWidget(self.ingest_button)
        bottom_box.addWidget(self.cancel_button)

        vbox.addLayout(bottom_box)

        self.setLayout(vbox)

        self.setMinimumWidth(550)

        self.browse_button.clicked.connect(self.browse_click_slot)
        self.ingest_button.clicked.connect(self.ingest_button_slot)
        self.cancel_button.clicked.connect(self.reject)

        self.fold_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.fold_list.customContextMenuRequested.connect(self.context_menu)

    def ingest_button_slot(self):
        iterator = QtWidgets.QTreeWidgetItemIterator(self.fold_list)
        all_items = [item.value() for item in iterator]
        log = "Main path: {}\n".format(self._path)
        total_count = len(all_items)
        progress = 0
        step = 100.0 / total_count
        for item in all_items:
            fold = item.fold if isinstance(item, IngestListItem) else None
            if fold:
                if isinstance(fold, Footage):
                    ver = fold.new().create()
                    ver.create_link(item.path)
                    path = ver.path
                else:
                    fold.create()
                    path = fold.path
                log += "{}\t{}\n".format(item.path, path)
            progress += 1
            self.progress.setValue(int(progress*step))
        log_file = os.path.join(self._path, "log_{}.txt".format(datetime.datetime.now().strftime("%Y_%M_%d_%H_%M")))
        with open(log_file, "w") as f:
            f.write(log)

        return 1


    def browse_click_slot(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Path"
        )
        if path:
            self._path = os.path.normpath(path)
            self.load_fold_list()

    def load_fold_list(self):
        if self._path is None:
            return
        self.fold_list.clear()
        root_name = os.path.basename(self._path)
        header = QtWidgets.QTreeWidgetItem([root_name, "",""])
        # self.fold_list.setHeaderItem(header)
        self.fold_list.addTopLevelItem(header)
        self.add_list_items(self._path, header)

    def add_list_items(self, path, parent):
        for fold in os.listdir(path):
            fold_path = os.path.normpath(os.path.join(path, fold))
            if os.path.isdir(fold_path):
                item = IngestListItem(path=fold_path)
                parent.addChild(item)
                self.add_list_items(fold_path, item)


    # def __get_fold_from_item(self, item: IngestListItem, from_parent=True):
    #     result = None
    #     while item:
    #         fold_type = item.text(1)
    #         if not fold_type:
    #             if from_parent:
    #                 item = item.parent()
    #             else:
    #                 item = None
    #         else:
    #             if fold_type == "Reel":
    #                 reel_name = item.text(2) or item.text(0)
    #                 result = item, Reel(project=self.project_combo.currentText(), name=reel_name)
    #                 item = None
    #             elif fold_type == "Shot":
    #                 shot_name = item.text(2) or item.text(0)
    #                 _, reel = self.__get_fold_from_item(item.parent())
    #                 result = item, Shot(
    #                     project=self.project_combo.currentText(),
    #                     reel=reel.name,
    #                     name=shot_name,
    #                 )
    #                 item = None
    #             elif fold_type in FootageTypes.get_all():
    #                 foot_name = item.text(2) or item.text(0)
    #                 _, shot = self.__get_fold_from_item(item.parent())
    #                 result = item, Footage(
    #                     shot=shot,
    #                     name=foot_name,
    #                     footage_type=fold_type)
    #                 item = None
    #
    #     if result:
    #         return result
    #     else:
    #         return None, None

    def rename_item(self, item: IngestListItem, similar=False):
        get_input = BaseDialog(self)
        name, ok = get_input.get_text("Rename", "Enter new name:", item.format_string)
        if ok and name:
            if similar:
                self.run_on_similar(item, "rename", name)
            else:
                item.rename(name)

    def run_on_similar(self, item, func_name, *arg):
        def _mark_it_recurse(t_item, level):
            if isinstance(t_item, IngestListItem) and t_item.level == level:
                func = getattr(t_item, func_name)
                if func:
                    func(*arg)
            for c in [t_item.child(i) for i in range(t_item.childCount())]:
                _mark_it_recurse(c, level)
        top_item = item
        while top_item.parent():
            top_item = top_item.parent()

        _mark_it_recurse(top_item, item.level)


    def context_menu(self, pos):
        menu = QtWidgets.QMenu()
        item = self.fold_list.itemAt(pos)
        if item:
            if item.fold:
                act_rename = menu.addAction("Rename")
                act_rename_sim = menu.addAction("Rename similar")
                act_rename.triggered.connect(lambda: self.rename_item(item))
                act_rename_sim.triggered.connect(lambda: self.rename_item(item, True))
                act_unmark = menu.addAction("Un mark this and children")
                act_unmark.triggered.connect(lambda: item.unset_fold())
                menu_convert = menu.addMenu("Convert name to")
                menu_convert_sim = menu.addMenu("Convert similar to")
                for case in ["Upper", "Lower", "Title"]:
                    act_conv = menu_convert.addAction(case)
                    act_conv_sim = menu_convert_sim.addAction(case)
                    act_conv.triggered.connect(partial(item.string_convert, case))
                    act_conv_sim.triggered.connect(partial(self.run_on_similar, item, "string_convert", case))
            else:
                parent_item, parent_fold = item.get_parent_fold()
                if parent_fold is None:
                    act = menu.addAction("Mark as Reel")
                    act.triggered.connect(lambda: item.set_fold("Reel"))
                    act_sim = menu.addAction("Mark similar as Reel")
                    act_sim.triggered.connect(partial(self.run_on_similar, item, "set_fold", "Reel"))
                elif isinstance(parent_fold, Reel):
                    act = menu.addAction("Mark as Shot")
                    act.triggered.connect(lambda: item.set_fold("Shot"))
                    act_sim = menu.addAction("Mark similar as Shot")
                    act_sim.triggered.connect(partial(self.run_on_similar, item, "set_fold", "Shot"))
                else:
                    foot_menu = menu.addMenu("Mark as ..")
                    for foot in FootageTypes.get_all():
                        foot_act = foot_menu.addAction(foot.name)
                        foot_act.triggered.connect(partial(item.set_fold, foot.name))

                    foot_menu_sim = menu.addMenu("Mark similar as ..")
                    for foot in FootageTypes.get_all():
                        foot_act = foot_menu_sim.addAction(foot.name)
                        foot_act.triggered.connect(partial(self.run_on_similar, item, "set_fold", foot.name))

            menu.exec_(self.fold_list.mapToGlobal(pos))