import os
from functools import partial
from PySide2 import QtWidgets, QtCore, QtGui

from feuze.core.constant import Location
from feuze.core.fold import Reel, Shot, FootageTypes, Footage, BaseFold
from feuze.core.version import FootageVersion
from feuze.ui.base.placer_ui import Ui_placer
from feuze.ui.utility import get_main_window
from feuze.core.media import Version as MediaVersion


class ProjectItem(QtWidgets.QListWidgetItem):

    def __init__(self, project):
        super(ProjectItem, self).__init__(project.name)
        self.project = project
        self.name = project.name


class ReelShotTree(QtWidgets.QTreeWidget):

    def __init__(self, main_window, layout=None, *args, **kwargs):
        super(ReelShotTree, self).__init__(*args, **kwargs)
        if layout:
            layout.addWidget(self)
        self.expandToDepth(0)
        self.setHeaderHidden(True)
        self.main_window = main_window

        self.setSelectionMode(self.ExtendedSelection)

        self.main_window.project_changed.connect(self.load_reels)

        # Add right-click menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def context_menu(self, pos):
        menu = QtWidgets.QMenu()
        menu.addAction("Some test menu")
        item = self.itemAt(pos)
        if isinstance(item, ShotItem):
            menu.addSeparator()
            for act in item.menu_actions():
                menu.addAction(act)
            menu.exec_(self.mapToGlobal(pos))

    def load_reels(self, project_item):
        if not isinstance(project_item, ProjectItem):
            return None
        self.clear()
        self.addTopLevelItems([ReelItem(reel) for reel in project_item.project.get_reels()])
        self.expandToDepth(0)


class ReelItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, reel: Reel):
        super(ReelItem, self).__init__([reel.name])
        self.reel = reel
        self.name = reel.name

        self.addChildren([ShotItem(shot) for shot in reel.get_shots()])

        # self.setExpanded(True)


class ShotItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, shot):
        super(ShotItem, self).__init__([shot.name])
        self.shot = shot
        self.name = shot.name

    def menu_actions(self):
        act = QtWidgets.QAction('Create shot')
        act.triggered.connect(lambda: print("clicked"))
        return [act]
        # menu.exec_(map(pos))


class TypeItem(QtWidgets.QListWidgetItem):

    def __init__(self, footage_type):
        super(TypeItem, self).__init__(footage_type.name)
        self.footage_type = footage_type
        self.name = footage_type.name

        self.__items = set()

    def add_items(self, items):
        for item in items:
            self.__items.add(item)

        self.setText("{}({})".format(self.name, len(self.items)))

    def clear(self):
        self.__items.clear()

    @property
    def items(self):
        return self.__items


class IngestListItem(QtWidgets.QTreeWidgetItem):
    """Ingest window list item"""
    def __init__(self, path):
        basename = os.path.basename(path)
        super(IngestListItem, self).__init__([basename])
        self._path = os.path.normpath(path)
        self._format_string = ""
        self.setToolTip(2,"Rename Expression:\n"
                          "{project}: replaces with project name\n"
                          "{reel}: replaces with reel name\n"
                          "{shot}: shot name(only available on footges/shot types\n"
                          "{type}: type of this\n"
                          "{current_name}:  for current name.\n"
                          "{origin_name}: original folder name.")

    def get_parent_fold(self):
        result = None
        item = self.parent()
        while item:
            if getattr(item, "fold", None):
                result = item, item.fold
                item = None
            else:
                item = item.parent()

        if result:
            return result
        else:
            return None, None

    def set_fold(self, fold_type, fold_name=None):
        # if fold.__class__.__name__ not in ["Reel", "Shot", "Footage"]:
        #     return False
        # self.setText(1, fold.__class__.__name__)
        # self.setText(2, fold.name)
        # self._fold = fold
        # unset all children if same type exits
        self.unset_fold(by_type=fold_type)
        # unset from parent if exits with same type
        parent_item = self.parent()
        while parent_item:
            p_type = getattr(parent_item, "fold_type", None)
            if p_type == fold_type:
                parent_item.unset_fold(by_type=fold_type, unset_children=False)
            parent_item = parent_item.parent()
        valid_types = ["Reel", "Shot", "Footage"] + [f.name for f in FootageTypes.get_all()]
        fold_name = fold_name if fold_name else self.text(0)
        if fold_type not in valid_types:
            return False
        self.fold_type = fold_type
        self.fold_name = fold_name
        self._format_string = fold_name

    def string_convert(self, case):
        case = case.lower()
        if case == "upper":
            self.fold_name = self.fold_name.upper()
        if case == "lower":
            self.fold_name = self.fold_name.lower()
        if case == "title":
            self.fold_name = self.fold_name.title()

    def unset_fold(self, by_type=None, unset_children=True):
        if not by_type or self.fold_type == by_type:
            self.fold_type = ""
            self.fold_name = ""
            self._format_string = ""

        # unset if footage type matches
        foot_types = FootageTypes.get_all()
        if by_type in foot_types and self.fold_type in foot_types:
            self.fold_type = ""
            self.fold_name = ""
            self._format_string = ""

        if unset_children:
            for idx in range(self.childCount()):
                child = self.child(idx)
                child.unset_fold(by_type=by_type)

    def rename(self, value):
        fold = self.fold
        if not fold or not value:
            return
        attrs = self.__get_attrs_for_format()

        try:
            new_name = value.format(**attrs)
            self.fold_name = new_name
            self._format_string = value
        except KeyError:
            pass

    def __get_attrs_for_format(self):
        fold = self.fold
        if not fold:
            return {}
        attrs = {}
        fold_type = fold.__class__.__name__
        if fold_type == "Reel":
            attrs["project"] = fold.project
            attrs["reel"] = fold.name
        elif fold_type == "Shot":
            attrs["project"] = fold.project
            attrs["reel"] = fold.reel
            attrs["shot"] = fold.name
        elif fold_type == "Footage":
            attrs["project"] = fold.shot.project
            attrs["reel"] = fold.shot.reel
            attrs["shot"] = fold.shot.name

        attrs["type"] = self.fold_type
        attrs["current_name"] = self.fold_name
        attrs["origin_name"] = self.text(0)

        return attrs

    @property
    def format_string(self):
        return self._format_string

    @property
    def fold(self):
        if not self.fold_name or not self.fold_type:
            return None
        _, parent_fold = self.get_parent_fold()
        if not parent_fold:
            parent_fold_type = None
        else:
            parent_fold_type = parent_fold.__class__.__name__

        if parent_fold_type is None:
            main_window = get_main_window()
            if not main_window:
                return None
            project = main_window.current_project()
            if not project:
                raise(Exception("Project is not selected"))
            return Reel(
                project.name,
                self.fold_name
            )
        if parent_fold_type == "Reel":
            return Shot(
                parent_fold.project,
                parent_fold.name,
                self.fold_name
            )
        if parent_fold_type == "Shot":
            return Footage(
                shot=parent_fold,
                name=self.fold_name,
                footage_type=self.fold_type
            )

    @property
    def fold_name(self):
        return self.text(2)

    @fold_name.setter
    def fold_name(self, value):
        self.setText(2, value)

    @property
    def fold_type(self):
        return self.text(1)

    @fold_type.setter
    def fold_type(self, value):
        self.setText(1, value)

    @property
    def level(self):
        return len(self._path.split(os.path.sep))

    @property
    def path(self):
        return self._path


class Placer(QtWidgets.QWidget, Ui_placer):
    clicked = QtCore.Signal(QtGui.QMouseEvent)

    def __init__(self, main_widget: QtWidgets.QMainWindow =None, version=None):
        super(Placer, self).__init__()
        self.setupUi(self)
        self.version = None
        self._selected = False

        self.main_widget = main_widget

        self.setAutoFillBackground(True)
        self.set_selected(False)

        self.set_version(version)

        # Add right-click menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.clicked.connect(self.on_click)

    def on_click(self):
        print(self.parent())
        places = [p for p in self.parent().children() if isinstance(p, self.__class__)]
        selected = [p for p in places if p.selected]
        self_idx = self.parent().layout().indexOf(self)
        increment = 1
        last_selected_idx = None
        mod = QtWidgets.QApplication.keyboardModifiers()

        if selected:
            last_selected_idx = max([places.index(p) for p in selected if places.index(p) <= self_idx] or [None])
            if last_selected_idx is None:
                increment = -1
                last_selected_idx = min([places.index(p) for p in selected if places.index(p) >= self_idx] or [None])

        if mod == QtCore.Qt.ShiftModifier and last_selected_idx is not None:
            for idx in range(last_selected_idx, self_idx+increment, increment):
                item = places[idx]
                item.set_selected(True)
        elif mod == QtCore.Qt.ControlModifier:
            self.toggle_selection()
        elif len(selected) == 1 and selected[0] == self:
            self.toggle_selection()
        else:
            for item in selected:
                item.toggle_selection()
            self.set_selected(True)


    def toggle_selection(self):
        self.set_selected(not self.selected)

    def set_selected(self, value=True):
        plt = QtGui.QPalette()
        if value:
            plt.setColor(plt.Window, plt.color(plt.Highlight))
        else:
            plt.setColor(plt.Window, plt.color(plt.AlternateBase))

        self._selected = value
        self.setPalette(plt)


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(event)
        super(Placer, self).mousePressEvent(event)

    def set_version(self, version: MediaVersion):
        if not version:
            return None
        self.version = version

        header = "/".join(version.crumbs.split("/")[1:])
        foot = version.media.name
        ver = version.version if version.exists() else "*{}".format(version.version)
        img = version.thumbnail

        self.header.setText("<font color='gray'>{}</font>".format(header))
        self.footage.setText("<font color='gray'>{}</font>".format(foot))
        self.version_label.setText("<font color='gray'>{}</font>".format(ver))

        if os.path.exists(img):
            pixmap = QtGui.QPixmap.fromImage(img)
            self.image.setPixmap(pixmap)
            self.image.setFixedHeight(50)
            self.image.setFixedWidth(120)
        else:
            self.image.setPixmap(None)

    def version_menu_action(self, ver):
        self.set_version(self.version.parent.version(ver))

    def context_menu(self, pos):
        menu = QtWidgets.QMenu()
        menu.addAction('Show info', lambda: QtWidgets.QMessageBox.information(
            self.main_widget,
            "Version info",
            self.version.get_inf_str()
        ))
        menu.addAction('Test menu', lambda: print("clicked"))
        menu.addAction('Play', lambda: print("play clicked"))
        if self.version.exists() == Location.CENTRAL:
            menu.addAction('Localise', lambda: self.version.localise())
        if self.version.exists() == Location.LOCAL:
            menu.addAction('Centralise', lambda: self.version.centralise())
        menu.addSeparator()
        version_submenu = menu.addMenu("Versions")
        versions = self.version.media.get_all_versions()
        for ver in versions:
            act = partial(self.version_menu_action, ver)
            version_submenu.addAction(ver, act)

        menu.exec_(self.mapToGlobal(pos))

    @property
    def selected(self):
        return self._selected


class ScrollArea(QtWidgets.QScrollArea):

    def __init__(self, types):
        super(ScrollArea, self).__init__()
        widget = QtWidgets.QWidget()
        self._layout = FlowLayout(widget)
        self.setWidget(widget)
        self.setWidgetResizable(True)

        self.types = types
        self.types.itemClicked.connect(self.apply_filter)
        # self.clicked.connect(self.on_click)
        # TODO filter widgets inside

    def filter_verify(self, widget: Placer):
        types = self.types.currentItem()
        if types:
            print(types.footage_type.name, widget.version.footage_type.name)
            return types.footage_type.name == widget.version.footage_type.name
        return True

    def apply_filter(self):
        for placer in [self._layout.itemAt(i).widget() for i in range(self._layout.count())]:
            placer.setHidden(not self.filter_verify(placer))

    def on_click(self, event: QtGui.QMouseEvent):
        # TODO click actions
        pass
        # Deselect all placer in the scroll area
        # for placer in [self._layout.itemAt(i).widget() for i in range(self._layout.count())]:
        #     if isinstance(placer, Placer) and placer.selected:
        #         print(placer.pos()) # .set_selected(False)

    def add_widget(self, widget):
        self._layout.addWidget(widget)
        widget.setHidden(not self.filter_verify(widget))

    def clear(self):
        self._layout.clear()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.on_click(event)
        super(ScrollArea, self).mousePressEvent(event)


class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        self._item_list = []


    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def clear(self):
        for item in self._item_list:
            item.widget().deleteLater()
            # self.removeItem(item)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            if item.widget().isHidden():
                continue
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Horizontal
            )
            layout_spacing_y = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Vertical
            )
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

