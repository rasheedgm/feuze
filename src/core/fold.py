import datetime
import os
import re

import yaml

from feuze.core.constant import (
    VERSION_PATTERN, )
from feuze.core import configs
from feuze.core import utility
from feuze.core.user import current_auth
from feuze.core.version import FootageVersion


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
        self._info, self._info_path = utility.read_info_yaml(path)

    def __str__(self):
        return self._name

    def exists(self):
        return os.path.exists(self._path)

    def create(self, local=False, **kwargs):
        if not os.path.exists(self._path):
            os.makedirs(self._path)

        if local and not os.path.exists(self._local_path):
            os.makedirs(self._local_path)

        self._create_info_file(**kwargs)

    def _create_info_file(self, **kwargs):
        info = dict()
        info["name"] = self._name
        info["path"] = self._path
        info["info_file"] = self._info_path
        info["class"] = self.__class__.__name__
        info["created_at"] = datetime.datetime.now()
        if not current_auth():
            raise Exception("You are not authorised")
        info["created_by"] = current_auth().user.name

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

    def set_name(self, value):
        # TODO need to remove
        self._name = value

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
        auth = current_auth()
        if not auth or not auth.role.has("project_admin"):
            raise Exception("Not authorised to create")
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
        auth = current_auth()
        if not auth or not auth.role.has("project_admin"):
            raise Exception("Not authorised to create")

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
        auth = current_auth()
        if not auth or not auth.role.has("project_admin"):
            raise Exception("Not authorised to create")

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

    def __str__(self):
        return self.name

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
            type=self._type.name,
            **kwargs
        )

    def new(self):
        return FootageVersion(self)

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
        return FootageVersion.get_version_instance(self, version)

    def get_versions(self):
        return FootageVersion.get_all_version_instances(self)

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
            utility.logger.info("Error reding info file: {}".format(info_file))
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
    if bool(re.match(FootageVersion._pattern, last_dir)):
        version = last_dir
        footage_dir = os.path.dirname(path)
        footage = fold_from_info(footage_dir)
        return FootageVersion(footage, version)
    else:
        return fold_from_info(path)






