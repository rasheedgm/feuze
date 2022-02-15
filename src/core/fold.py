import datetime
import os
import logging
import re
import shutil

import yaml

from .constant import (
    VersionType, DEFAULT_EXTENSIONS, SEQ_FORMAT,
    VERSION_PATTERN, Location,
)
from fileseq import FileSequence, PAD_STYLE_HASH1, findSequencesOnDisk
from src.core.utility import create_symlink, TaskThreader, is_sym_link, logger, find_available_location
from src.core import configs


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
        self._local_path = path.replace(configs.UserConfig.central_project_path, configs.UserConfig.local_project_path)
        self._thumbnail = None
        self._info = dict()
        info_file = os.path.join(path, "info.yaml")
        if os.path.exists(info_file):
            with open(info_file, "r") as file:
                try:
                    self._info = yaml.safe_load(file)
                except yaml.YAMLError as e:
                    logger.info("Error reding info file: {}".format(info_file))
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
        if not os.path.exists(self._info_path):
            self._create_info_file(**kwargs)
        else:
            self._info.update(kwargs)
            with open(self._info_path, "w") as info_file:
                yaml.dump(self._info, info_file)

    def get_info(self, attr):
        return self._info.get(attr, None)

    @property
    def thumbnail(self):
        if not self._thumbnail:
            path = os.path.join(self._path, ".thumbnail")
            if os.path.exists(path) and os.listdir(path):
                file_name = next(iter([f for f in os.listdir(path) if f.endswith(".png")]), "{}.png".format(self._name))
            else:
                file_name = "{}.png".format(self._name)
            self._thumbnail = os.path.join(path, file_name)

        return self._thumbnail

    @property
    def local_path(self):
        return self._local_path

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
            path = os.path.join(configs.UserConfig.central_project_path, name)
        super(Project, self).__init__(name, path)

    def get_reels(self):
        workflow_dir = os.path.join(self.path, configs.GlobalConfig.workflow_dir_name)
        if not os.path.exists(workflow_dir):
            return []
        reel_names = os.listdir(workflow_dir)
        return [Reel(self, reel) for reel in reel_names if os.path.isdir(os.path.join(workflow_dir, reel))]

    def create(self, **kwargs):
        BaseFold.create(self, **kwargs)
        self.create_sub_dirs()

    def create_sub_dirs(self):
        for dr in configs.GlobalConfig.project_sub_dirs:
            path = os.path.join(self.path, dr)
            if not os.path.exists(path):
                os.makedirs(path)


class Reel(BaseFold):
    """"""
    def __init__(self, project, name, path=None):
        self._project = project if isinstance(project, Project) else Project(project)
        if not path:
            path = os.path.join(self._project.path, configs.GlobalConfig.workflow_dir_name, name)
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

        self.create_sub_dirs()

    def create_sub_dirs(self):
        for dr in configs.GlobalConfig.shot_sub_dirs:
            path = os.path.join(self.path, dr)
            if not os.path.exists(path):
                os.makedirs(path)

    def get_footages(self):
        return Footage.get_all_footage_in_shot(self)

    @property
    def project(self):
        return self._project

    @property
    def reel(self):
        return self._reel


class FootageTypes(object):
    __ALL_TYPES = configs.GlobalConfig.all_footage_types

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
        self._type = footage_type
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
    def crumbs(self):
        return "{}/{}/{}".format(
            self.shot.project,
            self.shot.reel,
            self.shot.name
        )

    @property
    def thumbnail(self):
        return self.latest().thumbnail

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
        self._local_path = self._path.replace(
            configs.UserConfig.central_project_path,configs.UserConfig.local_project_path)
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
        self._thumbnail = None

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
        # TODO might not work on local file as findseq is running on central
        file_path = self._seq[0].frame(self._seq[0].start())
        return find_available_location(file_path, file_path.replace(self._path, self._local_path))

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

    def create(self, local=False):
        exists = find_available_location(self._path, self._local_path)
        if exists == Location.BOTH:
            return self

        if not self._parent.exists():
            self._parent.create()

        if exists != Location.CENTRAL:
            os.makedirs(self._path)
            self._created_by = "username"
            self._created_at = datetime.datetime.now()

        if local and exists != Location.LOCAL:
            os.makedirs(self._local_path)

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

    def create_link(self, path, link_to=Location.CENTRAL):
        # only link to central
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

    def copy_files_from(self, path, copy_to=Location.CENTRAL):
        # TODO test it in both local and central
        if self.exists() == copy_to:
            raise Exception("Files already exists")

        if copy_to == Location.BOTH:
            paths = (self._path, self._local_path)
        elif copy_to == Location.LOCAL:
            paths = (self._local_path,)
        elif copy_to == Location.CENTRAL:
            paths = (self._path,)
        else:
            return None

        src = None
        for parent, dirs, files in os.walk(path):
            if files:
                src = parent
                break

        if src:
            src_seqs = findSequencesOnDisk(src)
            for path in paths:
                if not os.path.exists(path):
                    os.makedirs(path)
                for fs in src_seqs:
                    cp = fs.copy()
                    cp.setDirname(path)
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

    def centralise(self):
        if self.exists() in (Location.CENTRAL, Location.BOTH):
            logger.warning("Version already exists in central")
            return None

        if not os.listdir(self._local_path):
            raise Exception("Local version is not available")

        src_seqs = findSequencesOnDisk(self._local_path)
        for seq in src_seqs:
            central_copy = seq.copy()
            central_copy.setDirname(self._path)
            copy_tasks = [(shutil.copy,seq.frame(frame), central_copy.frame(frame)) for frame in central_copy.frameSet()]
            TaskThreader.add_to_queue(copy_tasks)

    def localise(self):
        if self.exists() in (Location.LOCAL, Location.BOTH):
            logger.warning("Version already exists in local")
            return None
        if self.exists() is not Location.CENTRAL:
            raise Exception("Central version is not available")

        self.create(local=True)
        for seq in self._seq:
            local_copy = seq.copy()
            local_copy.setDirname(self._local_path)
            copy_tasks = [(shutil.copy, seq.frame(frame), local_copy.frame(frame)) for frame in local_copy.frameSet()]
            TaskThreader.add_to_queue(copy_tasks)

    def find_sequence(self):
        self._seq = findSequencesOnDisk(self._path, pad_style=PAD_STYLE_HASH1)

        if len(self._seq) > 1:
            self._type = VersionType.MULTISEQ
        elif self._seq:
            if self._seq[0].frameSet():
                self._type = VersionType.IMAGESEQ
            else:
                if self._seq[0].extension() == "mov":
                    self._type = VersionType.QUICKTIME
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

    def latest(self):
        try:
            versions = self.get_all_versions()
            if versions:
                return max(versions)
            else:
                return "v01"
        except FileNotFoundError:
            return "v01"

    def get_all_versions(self):
        return [v for v in os.listdir(self._parent.path) if bool(self._pattern.match(v))]

    def get_inf_str(self, html=False):
        line = "<b>{}:</b>\t<b>{}</b>\n" if html else "{}:\t{}\n"
        str_info = ""
        for key, value in self.info.items():
            str_info += line.format(key, value)
        return str_info

    @property
    def thumbnail(self):
        if not self._thumbnail:
            path = os.path.dirname(BaseFold.thumbnail.fget(self._parent))
            file_name = "{}_{}.png".format(self._parent.name, self.version)
            self._thumbnail = os.path.join(path, file_name)

        return self._thumbnail

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
            "local_path": self._local_path,
            "filepaths": self._filepaths,
            "local_filepaths": self.local_filepaths,
            "created_by": self._created_by,
            "created_at": self._created_at
        }

    @property
    def crumbs(self):
        return self._parent.crumbs

    @property
    def footage_type(self):
        return self._parent.type

    @property
    def parent(self):
        return self._parent

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
    def local_path(self):
        return self._local_path

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
    
    @property
    def local_filepaths(self):
        return [path.replace(self.path, self._local_path) for path in self._filepaths]

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
    # TODO only return active projects
    if not configs.UserConfig.exists():
        return []
    return [Project(p) for p in os.listdir(configs.UserConfig.central_project_path)
            if os.path.isdir(os.path.join(configs.UserConfig.central_project_path, p))]


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
            logger.info("Error reding info file: {}".format(info_file))
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






