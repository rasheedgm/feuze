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

"""

import yaml
import os.path

from src.core.constant import ALL_FOOTAGE_TYPES, WORKFLOW_DIR_NAME, DAILIES_DIR_NAME, ASSETS_DIR_NAME, \
    FROM_CLIENT_DIR_NAME, TO_CLIENT_DIR_NAME, SHOT_SUB_DIRS
from src.core.utility import get_user_config_file, logger


class _UserConfig(object):
    __instance = None
    config_path = get_user_config_file()
    __data = {}

    def __init__(self):
        super(_UserConfig, self).__init__()
        if self.__class__.__instance is None:
            self.__class__.__instance = self
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
        footage_type_from_config = self.__data.get("ALL_FOOTAGE_TYPES")
        if footage_type_from_config:
            ALL_FOOTAGE_TYPES.update(footage_type_from_config)
        self._all_footage_types = ALL_FOOTAGE_TYPES
        
        self._workflow_dir_name = self.__data.get("WORKFLOW_DIR_NAME") or WORKFLOW_DIR_NAME
        self._dailies_dir_name = self.__data.get("DAILIES_DIR_NAME") or DAILIES_DIR_NAME
        self._assets_dir_name = self.__data.get("ASSETS_DIR_NAME") or ASSETS_DIR_NAME
        self._from_client_dir_name = self.__data.get("FROM_CLIENT_DIR_NAME") or FROM_CLIENT_DIR_NAME
        self._to_client_dir_name = self.__data.get("TO_CLIENT_DIR_NAME") or TO_CLIENT_DIR_NAME

        project_sub_dirs = [
            self._workflow_dir_name, self._dailies_dir_name,
            self._assets_dir_name, self._from_client_dir_name, self._to_client_dir_name]
        project_sub_dirs_from_config = self.__data.get("PROJECT_SUB_DIRS")
        if project_sub_dirs_from_config:
            project_sub_dirs += project_sub_dirs_from_config
        self._project_sub_dirs = list(set(project_sub_dirs))

        self._shot_sub_dirs = self.__data.get("SHOT_SUB_DIRS") or SHOT_SUB_DIRS

    def update(self, **kwargs):
        self.__data.update(kwargs)
        self.__set_attr()
        base_path = os.path.dirname(self.config_path)
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        with open(self.config_path, "w") as fl:
            yaml.dump(self.__data, fl)

    @property
    def all_footage_types(self):
        return self._all_footage_types
    
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
