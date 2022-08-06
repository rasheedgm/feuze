"""
###  Global config format  ###

WORKFLOW_DIR_NAME: 01_Shots
DAILIES_DIR_NAME: 02_Dailies
ASSETS_DIR_NAME: 03_Assets
FROM_CLIENT_DIR_NAME: 04_From_Client
TO_CLIENT_DIR_NAME: 05_To_Client
PROJECT_SUB_DIRS:
  # these folders will be appended
  Sub_dir_1
  Sub_dir_2
SHOT_SUB_DIRS:
  Dir_name1
  Dir_name2
ALL_FOOTAGE_TYPES:
  # these will be updated on default types
  Render: {"name": "Render", "short_name": "GR", "sub_dir": "Renders", "template": "{name}" }
ALL_TASK_TYPES:
  Comp: {"name": "Comp", "short_name": "CMP", "sub_dir": "Comp", "template": "{name}"}
USERS_DIR: <path>
USER_ROLES:
    admin:
        - permissions list(user_admin, project_admin)
"""

import yaml
import os.path

from feuze.core.utility import get_user_config_file, logger
from feuze.core import constant


class _UserConfig(object):
    __instance = None
    config_path = get_user_config_file()
    __data = {}

    def __init__(self):
        super(_UserConfig, self).__init__()
        if self.__class__.__instance is None:
            self.__class__.__instance = self
            # TODO what if file/dir doesnt exists
            with open(self.config_path, "r") as fl:
                self.__data = yaml.safe_load(fl)
                self.__set_attr()

    def __set_attr(self):
        self._central_project_path = self.__data.get("central_project_path")
        self._local_project_path = self.__data.get("local_project_path")

    def update(self, **kwargs):
        self.__data.update(kwargs)
        self.__set_attr()
        base_path = os.path.dirname(self.config_path)
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        with open(self.config_path, "w") as fl:
            yaml.dump(self.__data, fl)

    @property
    def central_project_path(self):
        return self._central_project_path

    @property
    def local_project_path(self):
        return self._local_project_path

    @classmethod
    def validate(cls):
        for key in ("central_project_path", "local_project_path"):
            if getattr(cls, key) is None:
                return False
        return True

    @classmethod
    def exists(cls):
        return os.path.exists(cls.config_path)

    @classmethod
    def get_inst(cls):
        return cls.__instance if cls.__instance else cls()


UserConfig = _UserConfig.get_inst()


class _GlobalConfig(object):
    __instance = None
    config_path = os.path.join(UserConfig.central_project_path, "config.yaml")
    __data = {}

    def __init__(self):
        super(_GlobalConfig, self).__init__()
        if self.__class__.__instance is None:
            self.__class__.__instance = self
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as fl:
                    self.__data = yaml.safe_load(fl) or {}
            self.__set_attr()

    def __set_attr(self):

        media_type_from_config = self.__data.get("MEDIA_TYPES")
        if media_type_from_config:
            constant.MEDIA_TYPES.update(media_type_from_config)
        self._all_media_types = constant.MEDIA_TYPES

        footage_type_from_config = self.__data.get("ALL_FOOTAGE_TYPES")
        if footage_type_from_config:
            constant.ALL_FOOTAGE_TYPES.update(footage_type_from_config)
        self._all_footage_types = constant.ALL_FOOTAGE_TYPES

        task_type_from_config = self.__data.get("ALL_TASK_TYPES")
        if task_type_from_config:
            constant.ALL_TASK_TYPES.update(task_type_from_config)
        self._all_task_types = constant.ALL_TASK_TYPES
        
        self._workflow_dir_name = self.__data.get("WORKFLOW_DIR_NAME") or constant.WORKFLOW_DIR_NAME
        self._dailies_dir_name = self.__data.get("DAILIES_DIR_NAME") or constant.DAILIES_DIR_NAME
        self._assets_dir_name = self.__data.get("ASSETS_DIR_NAME") or constant.ASSETS_DIR_NAME
        self._from_client_dir_name = self.__data.get("FROM_CLIENT_DIR_NAME") or constant.FROM_CLIENT_DIR_NAME
        self._to_client_dir_name = self.__data.get("TO_CLIENT_DIR_NAME") or constant.TO_CLIENT_DIR_NAME

        project_sub_dirs = [
            self._workflow_dir_name, self._dailies_dir_name,
            self._assets_dir_name, self._from_client_dir_name, self._to_client_dir_name]
        project_sub_dirs_from_config = self.__data.get("PROJECT_SUB_DIRS")
        if project_sub_dirs_from_config:
            project_sub_dirs += project_sub_dirs_from_config
        self._project_sub_dirs = list(set(project_sub_dirs))

        self._shot_sub_dirs = self.__data.get("SHOT_SUB_DIRS") or constant.SHOT_SUB_DIRS

        self._users_dir = self.__data.get("USERS_DIR") or None

        user_roles_from_config = self.__data.get("USER_ROLES")
        if user_roles_from_config:
            constant.USER_ROLES.update(user_roles_from_config)
        self._user_roles = constant.USER_ROLES

        task_statuses = self.__data.get("TASK_STATUSES") or []
        task_statuses_names = (n["status"] for n in task_statuses)
        if task_statuses:
            constant.TASK_STATUSES = [s for s in constant.TASK_STATUSES if s.get("status") not in task_statuses_names]
            constant.TASK_STATUSES.extend(task_statuses)
        self._task_statuses = constant.TASK_STATUSES

        shot_statuses = self.__data.get("SHOT_STATUSES") or []
        shot_statuses_names = (n["status"] for n in shot_statuses)
        if shot_statuses:
            constant.SHOT_STATUSES = [s for s in constant.SHOT_STATUSES if s.get("status") not in shot_statuses_names]
            constant.SHOT_STATUSES.extend(shot_statuses)
        self._shot_statuses = constant.SHOT_STATUSES

    def update(self, **kwargs):
        self.__data.update(kwargs)
        self.__set_attr()
        base_path = os.path.dirname(self.config_path)
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        with open(self.config_path, "w") as fl:
            yaml.dump(self.__data, fl)

    @property
    def all_media_types(self):
        return self._all_media_types

    @property
    def shot_statuses(self):
        return self._shot_statuses

    @property
    def task_statuses(self):
        return self._task_statuses

    @property
    def user_roles(self):
        return self._user_roles

    @property
    def users_dir(self):
        return self._users_dir

    @property
    def all_footage_types(self):
        return self._all_footage_types

    @property
    def all_task_types(self):
        return self._all_task_types

    @property
    def workflow_dir_name(self):
        return self._workflow_dir_name
    
    @property
    def dailies_dir_name(self):
        return self._dailies_dir_name
    
    @property
    def assets_dir_name(self):
        return self._assets_dir_name
    
    @property
    def from_client_dir_name(self):
        return self._from_client_dir_name
    
    @property
    def to_client_dir_name(self):
        return self._to_client_dir_name

    @property
    def project_sub_dirs(self):
        return self._project_sub_dirs
    
    @property
    def shot_sub_dirs(self):
        return self._shot_sub_dirs

    @classmethod
    def validate(cls):
        for key in ["central_project_path", "local_project_path"]:
            if getattr(cls, key) is None:
                return False
        return True

    @classmethod
    def exists(cls):
        return os.path.exists(cls.config_path)

    @classmethod
    def get_inst(cls):
        return cls.__instance if cls.__instance else cls()


GlobalConfig = _GlobalConfig.get_inst()
