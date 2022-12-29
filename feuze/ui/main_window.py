import os.path
import sys

from PySide2.QtWidgets import QApplication, QMainWindow, QInputDialog, QMessageBox, QAction
from PySide2.QtGui import QPalette, QColor, QIcon
from PySide2.QtCore import Qt, Signal, QAbstractTableModel

import feuze.core.media
from feuze.core.utility import get_user_config_file
from feuze.ui.widgets import ProjectItem, ReelItem, TypeItem, ShotItem, Placer, ReelShotTree, ScrollArea
from feuze.ui.base.main_window_ui import Ui_MainWindow
from feuze.core.fold import get_all_projects, Project, Shot, FootageTypes, Reel
from feuze.ui.windows import SettingWindow, IngestInputs
from feuze.core import configs, media


class MainWindow(QMainWindow, Ui_MainWindow):
    project_changed = Signal(Project)
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.user_config = configs.UserConfig

        setting_action = QAction("Setting", self)
        setting_action.triggered.connect(self.show_setting)
        self.menubar.addAction(setting_action)

        self.reels_shots = ReelShotTree(main_window=self, layout=self.reel_shot_tab.layout())

        self.scroll_area = ScrollArea(types=self.types)
        self.scroll_layout.addWidget(self.scroll_area)

        self.projects.itemClicked.connect(self.project_item_clicked)
        self.reels_shots.itemClicked.connect(self.reel_shot_clicked)
        # self.types.itemClicked.connect(self.load_places)
        self.add_project.clicked.connect(self.add_project_slot)
        self.add_reel.clicked.connect(self.add_reel_slot)
        self.add_shot.clicked.connect(self.add_shot_slot)
        self.ingest.clicked.connect(self.show_ingest)

        if not self.user_config.exists() or not self.user_config.validate():
            self.show_setting(True)
        else:
            self.load_projects()
            self.init_types()

    def show_ingest(self):
        ingest_input = IngestInputs(self)
        ingest_input.show()


    def show_setting(self, show=False):
        setting = SettingWindow(self)
        # TODO load project only if proj path is changed
        setting.accepted.connect(self.load_projects)
        if show:
            setting.show()
        else:
            setting.exec_()


    def add_project_slot(self):
        name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
        # TODO need input getter which gets all required inputs
        if ok:
            project = Project(str(name))
            project.create()
            self.load_projects()
            item = self.projects.findItems(name, Qt.MatchExactly)
            self.projects.setItemSelected(item[0], True)
            self.projects.setCurrentItem(item[0])
            self.project_changed.emit(item[0])

    def add_reel_slot(self):
        selected_project = self.projects.selectedItems()
        msg = None
        if not selected_project:
            msg = "Please select a project"
        elif len(selected_project) > 1:
            msg = "Please select one project"

        if msg:
            # TODO need input getter which gets all required inputs
            QMessageBox.information(self, "Select reel", msg)
            return None

        name, ok = QInputDialog.getText(self, "New Reel", "Enter reel name:")
        if ok:
            project_item = selected_project[0]
            reel = Reel(project_item.project.name, name)
            reel.create()
            self.reels_shots.load_reels(project_item)
            item = self.reels_shots.findItems(name, Qt.MatchExactly, 0)
            self.reels_shots.setItemSelected(item[0],True)
            self.reels_shots.setCurrentItem(item[0])

    def add_shot_slot(self):
        selected_reel = self.reels_shots.selectedItems()
        msg = None
        if not selected_reel:
            msg = "Please select a reel"
        elif len(selected_reel) > 1:
            msg = "Please select one reel"
        elif not isinstance(selected_reel[0], ReelItem):
            msg = "Please select reel"

        if msg:
            # TODO need input getter which gets all required inputs
            QMessageBox.information(self, "Select reel", msg)
            return None

        name, ok = QInputDialog.getText(self, "New Shot", "Enter shot name:")
        if ok:
            project = selected_reel[0].reel.project
            reel = selected_reel[0].reel.name
            shot = Shot(project, reel, name)
            shot.create()
            self.reels_shots.load_reels(self.projects.selectedItems()[0])
            items = self.reels_shots.findItems(name, Qt.MatchExactly | Qt.MatchRecursive, 0)
            print(items)
            for item in items:
                if item.parent().name == reel:
                    self.reels_shots.setItemSelected(item, True)
                    self.reels_shots.setCurrentItem(item)
                    break


    def project_item_clicked(self, item):
        self.project_changed.emit(item)
        # self.load_reels(item)

    def reel_shot_clicked(self):
        # self.load_types()
        items = []
        for item in self.reels_shots.selectedItems():
            if isinstance(item, ReelItem):
                items += [item.child(i) for i in range(item.childCount())]
            else:
                items.append(item)
        self.load_places(items)
        # item = self.reels_shots.currentItem()
        # if isinstance(item, ShotItem):
        #     model = QAbstractTableModel()
        #     for key, value in item.shot.info:
        #         model.setData(key,value)
        #     self.details.item


    def load_projects(self):
        print("loading projects")
        self.projects.clear()
        for proj in get_all_projects():
            self.projects.addItem(ProjectItem(proj))

    def load_places(self, shot_items):
        if not shot_items:
            return

        self.scroll_area.clear()

        for shot_item in shot_items:

            for media_ in media.get_all_media(shot_item.shot):
                self.scroll_area.add_widget(Placer(self, media_.version("latest")))


        # if not types:
        #     types = self.types.currentItem()
        #
        # if not types:
        #     return
        #
        # self.scroll_area.clear()
        #
        # # TODO filter places in scroll area
        # for item in sorted(types.items, key=lambda x: x.name):
        #     self.scroll_area.add_widget(Placer(self, item.latest()))

    def load_types(self, parent_item=None):
        if not parent_item:
            # TODO switch if multiple selected
            parent_item = self.reels_shots.currentItem()
        # self.types.clear()
        if isinstance(parent_item, ShotItem):
            parent_item = parent_item.shot
        elif not isinstance(parent_item, Shot):
            # TODO if item is reel item do something
            return None

        footages = parent_item.get_footages()
        items = [self.types.item(i) for i in range(self.types.count())]
        for item in items:
            item.clear()
            item.add_items([f for f in footages if f.type.name == item.name])
            self.types.addItem(item)

    def init_types(self):
        self.types.clear()
        items = [TypeItem(t) for t in FootageTypes.get_all()]
        for item in items:
            self.types.addItem(item)

    def current_project(self):
        return self.projects.selectedItems()[0].project if self.projects.selectedItems() else None



