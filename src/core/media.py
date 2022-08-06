import os, sys
import re
from functools import partial
import inspect

import yaml

from feuze.core import configs
from feuze.core.fold import Shot


def is_media_class(obj):
    if not inspect.isclass(obj):
        return False
    return issubclass(obj, BaseMedia)


class Validator():
    VALIDATORS = {
        "FileValidator": "file_validator"
    }

    def __init__(self, validator):
        self.__validator = validator
        self.__call__ = self.file_validator

    def __new__(cls, validator=None, *args, **kwargs):
        cls.__call__ = cls.file_validator
        return cls

    def __call__(self, *args, **kwargs):
        print("none")

    def file_validator(self):
        print("file_validator")

    @classmethod
    def get(cls):
        return inspect.getmembers(cls)


class SourceTypes(object):
    __ALL_TYPES = configs.GlobalConfig.all_media_types

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


# class BaseSource(BaseFold):
#
#     def __init__(self, shot, name, source_type):
#         footage_type = source_type if isinstance(source_type, SourceTypes) else SourceTypes(source_type)
#         sub_dir = footage_type.sub_dir
#         name = footage_type.validate_name(name=name, shot=shot.name, **shot.__dict__)
#         path = os.path.join(shot.path, sub_dir, name)
#         super(BaseSource, self).__init__(name, path)
#         self._type = footage_type
#         self._shot = shot
#
#     def create(self, project=None, reel=None, shot=None, **kwargs):
#         if not self._shot.exists():
#             raise Exception("Shot {} does not exist".format(self._shot.name))
#
#         BaseFold.create(
#             self,
#             project=self._shot.project.name,
#             reel=self._shot.reel.name,
#             shot=self._shot.name,
#             type=self._type.name,
#             **kwargs
#         )
#
#     def new(self):
#         return FootageVersion(self)
#
#     def latest(self):
#         version = "v01"
#         if os.path.exists(self.path):
#             versions = [v for v in os.listdir(self.path) if bool(re.compile(VERSION_PATTERN).match(v))]
#             if versions:
#                 version = max(versions)
#
#         return self.version(version)
#
#     def version(self, version):
#         if isinstance(version, int):
#             version = "v%02d" % version
#         return FootageVersion.get_version_instance(self, version)
#
#     def get_versions(self):
#         return FootageVersion.get_all_version_instances(self)
#
#     def get_version_info(self, version):
#         if "versions" in self.info.keys():
#             return self.info["versions"].get(version)
#         else:
#             return None
#
#     @property
#     def crumbs(self):
#         return "{}/{}/{}".format(
#             self.shot.project,
#             self.shot.reel,
#             self.shot.name
#         )
#
#     @property
#     def thumbnail(self):
#         return self.latest().thumbnail
#
#     @property
#     def type(self):
#         return self._type
#
#     @property
#     def shot(self):
#         return self._shot
#
#     @classmethod
#     def get_all_footage_in_shot(cls, shot):
#         footages = []
#         for _type in SourceTypes.get_all():
#             path = os.path.join(shot.path, _type.sub_dir)
#             if os.path.exists(path):
#                 # TODO make utils method to get list of directories
#                 footages += [cls(shot, name, _type.name) for name in os.listdir(path)
#                              if os.path.isdir(os.path.join(path, name))]
#         return footages



class BaseMedia(object):

    def __init__(self, shot, **kwargs):
        self.__shot = shot
        self.__media_type = kwargs.get("media_type")
        sub_dir = kwargs.get("sub_dir")
        sub_dir = sub_dir.stip("/") if sub_dir else "Files"
        self.__path = os.path.normpath(os.path.join(shot.path, sub_dir, self.__media_type))
        self.__info_file = os.path.join(self.__path, "info.yaml")

        self.commit_data = None

    def get_info(self):
        with open(self.__info_file, "r") as info_file:
            info = yaml.load(info_file.read())
        return info

    def update_info(self, **kwargs):
        current_info = self.get_info()
        current_info.update(kwargs)
        with open(self.__info_file, "w") as info_file:
            yaml.dump(current_info, info_file)
        return True

    def commit(self):
        pass

    @property
    def shot(self):
        return self.__shot


class FileMedia(BaseMedia):

    def __init__(self, shot, **kwargs):
        super(FileMedia, self).__init__(shot=shot, **kwargs)
        print(kwargs)

class DataMedia(BaseMedia):
    pass




class MediaTypes(object):
    __MEDIA_CLASSES = {k: v for k, v in inspect.getmembers(sys.modules[__name__], is_media_class)}
    __ALL_TYPES = configs.GlobalConfig.all_media_types

    def __new__(cls, shot, media_type=None):
        if not isinstance(shot, Shot):
            raise Exception("{} is not a shot".format(shot))

        if not media_type:
            media_type = "_default"

        media_type_dict = cls.get_type(media_type)
        media_class_name = media_type_dict.get("media_class")
        if not media_class_name:
            raise Exception("Media class is not defined in the config")

        media_class = cls.__MEDIA_CLASSES.get(media_class_name)
        if not media_class:
            raise Exception("Media class {} not found".format(media_class_name))

        return media_class(shot=shot, **media_type_dict)

    @classmethod
    def get_type(cls, type_name):
        _type = cls.__ALL_TYPES.get(type_name)
        if not _type:
            for t in cls.__ALL_TYPES.values():
                if t["media_type"] == type_name:
                    _type = t
                    break
        if not _type:
            return None
        falloff_from = _type.get("__falloff")
        falloff = cls.__ALL_TYPES.get(falloff_from) or cls.__ALL_TYPES.get("_default")
        falloff.update(_type)

        return falloff


class Version(object):
    # init with source,
    # set file paths
    # file type need to take from soure
    # major minor version
    # get version from yaml
    # new to check file path.
    # data source

    pass

# shot = Shot("PROJ", "REEL01", "SHOT_01")
# mc = MediaTypes(shot=shot, media_type="Render")
#
# print(mc)
v = "/this/istest/"
print(os.path.join("/this/is/test","next/ned", "last"))
