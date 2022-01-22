import datetime
import os
import logging
import re
import shutil
import sys

from python.packages import yaml

from constant import (
    DEFAULT_PROJECT_PATH as _DEFAULT_PROJECT_PATH,
    WORKFLOW_DIRECTORY_NAME as _WORKFLOW, VersionType, DEFAULT_EXTENSIONS, SEQ_FORMAT, ALL_FOOTAGE_TYPES,
    VERSION_PATTERN,
)
from fileseq import FileSequence, PAD_STYLE_HASH1, findSequencesOnDisk
from utility import create_symlink, TaskThreader, is_sym_link

_log = logging.getLogger("Fold")


class BaseFold(object):
    """Base object for folder structure.
    """
    def __init__(self, name, path):
        """BaseFold init

        name(str) : name of fold
        path(str): path of fold
        """
        self._name = name
        self._path = path
        self._info = dict()
        info_file = os.path.join(path, "info.yaml")
        if os.path.exists(info_file):
            with open(info_file, "r") as file:
                try:
                    self._info = yaml.safe_load(file)
                except yaml.YAMLError as e:
                    _log.info("Error reding info file: {}".format(info_file))
                    self._info = {}

        self._info_path = info_file

    def __str__(self):
        return self._name

    def exists(self):
        return os.path.exists(self._path)

    def create(self, **kwargs):
        if not os.path.exists(self._path):
            os.makedirs(self._path)

        self._create_info_file(**kwargs)

    def _create_info_file(self, **kwargs):
        info = dict()
        info["name"] = self._name
        info["path"] = self._path
        info["info_file"] = self._info_path
        info["class"] = self.__class__.__name__
        info["created_at"] = datetime.datetime.now()
        info["created_by"] = "username"

        info.update(kwargs)

        self._info.update(info)

        with open(self._info_path, "w") as info_file:
            yaml.dump(self._info, info_file)

    def update_info(self, **kwargs):
        _log.warning("this")
        if not os.path.exists(self._info_path):
            self._create_info_file(**kwargs)
        else:
            self._info.update(kwargs)
            with open(self._info_path, "w") as info_file:
                yaml.dump(self._info, info_file)

    def get_info(self, attr):
        return self._info.get(attr, None)

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def info(self):
        return self._info


class Project(BaseFold):
    def __init__(self, name, path=None):
        if not path:
            path = os.path.join(_DEFAULT_PROJECT_PATH,  name)
        super(Project, self).__init__(name, path)

    def get_reels(self):
        workflow_dir = os.path.join(self.path, _WORKFLOW)
        if not os.path.exists(workflow_dir):
            return []
        reel_names = os.listdir(workflow_dir)
        return [Reel(self, reel) for reel in reel_names if os.path.isdir(os.path.join(workflow_dir, reel))]


class Reel(BaseFold):
    """"""
    def __init__(self, project, name, path=None):
        self._project = project if isinstance(project, Project) else Project(project)
        if not path:
            path = os.path.join(self._project.path, _WORKFLOW, name)
        super(Reel, self).__init__(name, path)

    def get_shots(self):
        if not os.path.exists(self.path):
            return []
        shot_names = os.listdir(self.path)
        return [Shot(self._project, self, shot) for shot in shot_names if os.path.isdir(os.path.join(self.path, shot))]

    def create(self, project=None, **kwargs):
        if not self._project.exists():
            self._project.create()
        BaseFold.create(self, project=self._project.name, **kwargs)

    @property
    def project(self):
        return self._project


class Shot(BaseFold):

    def __init__(self, project, reel, name, path=None):
        self._project = project if isinstance(project, Project) else Project(project)
        self._reel = reel if isinstance(reel, Reel) else Reel(self._project, reel)
        if not path:
            path = os.path.join(self._reel.path, name)
        super(Shot, self).__init__(name, path)

    def create(self, project=None, reel=None, **kwargs):
        if not self._reel.exists():
            self._reel.create()
        BaseFold.create(self, project=self._project.name, reel=self._reel.name, **kwargs)

    def get_footages(self):
        return Footage.get_all_footage_in_shot(self)

    @property
    def project(self):
        return self._project

    @property
    def reel(self):
        return self._reel


class FootageTypes(object):
    __ALL_TYPES = ALL_FOOTAGE_TYPES

    def __init__(self, name):
        f_type = self.__ALL_TYPES.get(name, self.__ALL_TYPES.get("Render"))
        self.name = f_type["name"]
        self.short_name = f_type["short_name"]
        self.sub_dir = f_type["sub_dir"]
        self.name_template = f_type["template"]


    def validate_name(self, name, **kwargs):
        pattern = self.name_template.format(name="(.+)", **kwargs)
        if bool(re.match(pattern, name)):
            return name
        else:
            return self.name_template.format(name=name, **kwargs)

    @classmethod
    def get_all(cls):
        return [cls(t) for t in cls.__ALL_TYPES]


class Footage(BaseFold):

    def __init__(self, shot: Shot, name, footage_type="Render"):
        footage_type = footage_type if isinstance(footage_type, FootageTypes) else FootageTypes(footage_type)
        sub_dir = footage_type.sub_dir
        name = footage_type.validate_name(name=name, shot=shot.name, **shot.__dict__)
        path = os.path.join(shot.path, sub_dir, name)
        super(Footage, self).__init__(name, path)
        self._type = footage_type.name
        self._shot = shot

    def create(self, project=None, reel=None, shot=None, **kwargs):
        if not self._shot.exists():
            raise Exception("Shot {} does not exist".format(self._shot.name))

        BaseFold.create(
            self,
            project=self._shot.project.name,
            reel=self._shot.reel.name,
            shot=self._shot.name,
            type=self._type,
            **kwargs
        )

    def new(self):
        return Version(self)

    def latest(self):
        version = "v01"
        if os.path.exists(self.path):
            versions = [v for v in os.listdir(self.path) if bool(re.compile(VERSION_PATTERN).match(v))]
            if versions:
                version = max(versions)

        return self.version(version)

    def version(self, version):
        if isinstance(version, int):
            version = "v%02d" % version
        return Version.get_version_instance(self, version)

    def get_versions(self):
        return Version.get_all_version_instances(self)

    def get_version_info(self, version):
        if "versions" in self.info.keys():
            return self.info["versions"].get(version)
        else:
            return None

    @property
    def type(self):
        return self._type

    @property
    def shot(self):
        return self._shot

    @classmethod
    def get_all_footage_in_shot(cls, shot):
        footages = []
        for _type in FootageTypes.get_all():
            path = os.path.join(shot.path, _type.sub_dir)
            if os.path.exists(path):
                # TODO make utils method to get list of directories
                footages += [cls(shot, name, _type.name) for name in os.listdir(path)
                             if os.path.isdir(os.path.join(path, name))]
        return footages


class Version(object):
    _instances = {}
    _pattern = re.compile(VERSION_PATTERN)

    def __init__(self, parent: Footage, version=None, ext=None, version_type=VersionType.IMAGESEQ):
        super(Version, self).__init__()
        self._parent = parent or None
        if not version:
            version = self.new()
        if not bool(self._pattern.match(version)) and not bool(re.match("^([0-9]+)$", str(version))):
            raise ValueError("Version should be either v%02d or number")
        if not bool(self._pattern.match(version)):
            version = "v%02d" % int(version)
        self._version = version
        self._path = os.path.join(self._parent.path, self._version)
        ext = ext if ext else DEFAULT_EXTENSIONS[version_type]
        if not ext.startswith("."):
            ext = "." + ext

        self._type = version_type
        self._created_by = None
        self._created_at = None
        self._filepaths = []
        self._ext = ext
        self._start = 0
        self._end = 0
        self._frame_range = None
        self._seq = []

        info = self._parent.get_version_info(self._version)
        if info:
            for key, item in info.items():
                if hasattr(self, "_{}".format(key)):
                    setattr(self, "_{}".format(key), item)

        self.find_sequence()

        if info and info["filepaths"] != self._filepaths:
            self.update_info(**self.info)

        if version not in self.__class__._instances.keys():
            self.__class__._instances[parent] = {version: self}
        if version not in self.__class__._instances[parent].keys():
            self.__class__._instances[parent][version] = self

    def format_sequence(self, fileseq):
        if not isinstance(fileseq, FileSequence):
            return fileseq
        return fileseq.format(SEQ_FORMAT)

    def exists(self):
        return os.path.exists(
            self._seq[0].frame(self._seq[0].start())
        )

    def new(self):
        try:
            # TODO need better way of replacing vV
            versions = [v.replace("v", "").replace("V", "") for v in os.listdir(self._parent.path)
                        if bool(self._pattern.match(v)) and os.listdir(os.path.join(self._parent.path, v))]
            if versions:
                return "%02d" % (int(max(versions)) + 1)
            else:
                return "v01"
        except FileNotFoundError:
            return "v01"

    def create(self):
        if os.path.exists(self._path):
            return self

        if not self._parent.exists():
            self._parent.create()

        os.makedirs(self._path)

        self._created_by = "username"
        self._created_at = datetime.datetime.now()

        self.update_info(**self.info)
        return self

    def delete(self):
        if not os.path.exists(self._path) or not os.listdir(self._path):
            return None
        if is_sym_link(self._path):
            os.remove(self._path)
            # TODO test it in linux and mac
        else:
            for seq in self._seq:
                TaskThreader.add_to_queue([(os.remove, seq.frame(frame)) for frame in seq.frameSet()])

            os.rmdir(self._path)

        info = self._parent.info.get("versions", {})
        info.update({"_del_{}".format(self._version): {
            "deleted": datetime.datetime.now()
        }})
        # TODO save more data on delete
        del info[self._version]
        self._parent.update_info(versions=info)

    def create_link(self, path):
        src = None
        for parent, dirs, files in os.walk(path):
            if files:
                src = parent
                break
        if src:
            create_symlink(src, self.path)
            self.find_sequence()
            self._created_by = "username"
            self._created_at = datetime.datetime.now()

            self.update_info(original_path=path, **self.info)

    def copy_files_from(self, path):
        if self.exists():
            raise Exception("Files already exists")

        src = None
        for parent, dirs, files in os.walk(path):
            if files:
                src = parent
                break

        if src:
            os.makedirs(self._path)
            src_seqs = findSequencesOnDisk(src)
            for fs in src_seqs:
                cp = fs.copy()
                cp.setDirname(self.path)
                if len(src_seqs) == 1:
                    cp.setBasename("{}_{}.".format(self._parent.name, self._version))
                copy_tasks = [(shutil.copy, fs.frame(frame), cp.frame(frame)) for frame in cp.frameSet()]
                TaskThreader.add_to_queue(copy_tasks)

            self.find_sequence()
            self._created_by = "username"
            self._created_at = datetime.datetime.now()
            self.update_info(copied_from=path, **self.info)

    def update_info(self, **kwargs):
        info = self._parent.info.get("versions", {})
        info.update({self._version: kwargs})
        self._parent.update_info(versions=info)

    def find_sequence(self):
        self._seq = findSequencesOnDisk(self._path, pad_style=PAD_STYLE_HASH1)

        if len(self._seq) > 1:
            self._type = VersionType.MULTISEQ
        elif self._seq:
            if self._seq[0].frameSet():
                self._type = VersionType.IMAGESEQ
            else:
                self._type = VersionType.SINGLEFILE
        else:
            # if there are no sequence then its new version
            if self._type is VersionType.SINGLEFILE:
                seq_path = os.path.join(
                    self._path,
                    "{}_{}{}".format(self._parent.name, self._version, self._ext)
                )
            else:
                seq_path = os.path.join(
                    self._path,
                    "{}_{}.####{}".format(self._parent.name, self._version, self._ext)
                )

            self._seq = [FileSequence(seq_path, pad_style=PAD_STYLE_HASH1)]

        self._filepaths = [self.format_sequence(fs) for fs in self._seq]
        self._ext = self._seq[0].extension()
        self._start = self._seq[0].start()
        self._end = self._seq[0].end()
        self._frame_range = self._seq[0].frameRange()

    def __str__(self):
        return self._version

    def set_frame_range(self, value):
        for fs in self._seq:
            fs.setFrameRange(value)
            self._frame_range = self._seq[0].frameRange()

    @property
    def info(self):
        return {
            "version": self._version,
            "type": self._type,
            "frame_range": self._frame_range,
            "start": self._start,
            "end": self._end,
            "extension": self._ext,
            "path": self._path,
            "filepaths": self._filepaths,
            "created_by": self._created_by,
            "created_at": self._created_at
        }

    @property
    def created_by(self):
        return self._created_by

    @property
    def created_at(self):
        return self._created_at

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def frame_range(self):
        return self._frame_range

    @property
    def type(self):
        return self._type

    @property
    def path(self):
        return self._path

    @property
    def extension(self):
        return self._ext

    @property
    def sequences(self):
        return self._seq

    @property
    def version(self):
        return self._version

    @property
    def filepaths(self):
        return self._filepaths

    def latest(self):
        try:
            versions = [v for v in os.listdir(self._parent.path) if bool(self._pattern.match(v))]
            if versions:
                return max(versions)
            else:
                return "v01"
        except FileNotFoundError:
            return "v01"

    @classmethod
    def get_all_version_instances(cls, parent):
        if not os.path.exists(parent.path):
            return []
        versions = [v for v in os.listdir(parent.path) if bool(cls._pattern.match(v))]
        version_ins = []
        for version in versions:
            version_ins.append(cls.get_version_instance(parent, version))
        return version_ins

    @classmethod
    def get_version_instance(cls, parent, version):
        parent_ins = cls._instances.get(parent)
        if parent_ins and version in parent_ins.keys():
            return parent_ins[version]
        else:
            return cls(parent, version)


def get_all_projects():
    if not os.path.exists(_DEFAULT_PROJECT_PATH):
        return []
    return [Project(p) for p in os.listdir(_DEFAULT_PROJECT_PATH)]


def fold_from_info(info_file):
    os.path.normpath(info_file)
    if os.path.isdir(info_file):
        info_file = os.path.join(info_file, "info.yaml")

    if not os.path.exists(info_file):
        return None

    _info = None

    with open(info_file, "r") as f:
        try:
            _info = yaml.safe_load(f)
        except yaml.YAMLError:
            _log.info("Error reding info file: {}".format(info_file))
            _info = {}
    if _info:
        _class = _info.get("class")
        if _class == "Footage":
            name = _info.get("name")
            foot_type = _info.get("type")
            shot = Shot(_info.get("project"), _info.get("reel"), _info.get("shot"))
            return Footage(shot, name, footage_type=foot_type)
        elif _class == "Shot":
            return Shot(_info.get("project"), _info.get("reel"), _info.get("shot"))
        elif _class == "Reel":
            return Reel(_info.get("project"), _info.get("reel"))
        elif _class == "Project":
            return Project(_info.get("project"))
        else:
            return None
    else:
        return None


def fold_from_path(path):
    """Create fold from a path"""
    path = os.path.join(path)
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    if path.endswith(os.path.sep):
        path = os.path.split(path)[0]
    last_dir = os.path.split(path)[1]
    if bool(re.match(VERSION_PATTERN, last_dir)):
        version = last_dir
        footage_dir = os.path.dirname(path)
        footage = fold_from_info(footage_dir)
        return Version(footage, version)
    else:
        return fold_from_info(path)






