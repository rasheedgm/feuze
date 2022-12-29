import os, sys
import re
import datetime
import shutil
from functools import partial
import inspect

import yaml
from fileseq import FileSequence, PAD_STYLE_HASH1, FileSeqException, findSequencesOnDisk

from feuze.core import configs, utility
from feuze.core.fold import Shot

from feuze.core.fold import BaseFold

from feuze.core.constant import VERSION_PATTERN, Location

from feuze.core.user import Auth, User, current_auth

from feuze.core.fold import get_fold_regex_pattern

#  TODO media cannot be modified if its committed, data field is not immutable after create,
#  instead it can be modified until it gets committed


def is_media_class(obj):
    if not inspect.isclass(obj):
        return False
    return issubclass(obj, BaseMedia)

# TODO remove
#
# class Validator():
#     VALIDATORS = {
#         "FileValidator": "file_validator"
#     }
#
#     def __init__(self, validator):
#         self.__validator = validator
#         self.__call__ = self.file_validator
#
#     def __new__(cls, validator=None, *args, **kwargs):
#         cls.__call__ = cls.file_validator
#         return cls
#
#     def __call__(self, *args, **kwargs):
#         print("none")
#
#     def file_validator(self):
#         print("file_validator")
#
#     @classmethod
#     def get(cls):
#         return inspect.getmembers(cls)


class BaseMedia(BaseFold):

    def __init__(self, shot: Shot, name, **kwargs):
        self._shot = shot
        self._media_type = kwargs.get("media_type")
        self._name = name
        self._name_template = kwargs.get("name_template", "{name}")
        self._file_type = kwargs.get("file_type")
        self._extension = kwargs.get("extension")
        self._validators = kwargs.get("validators")
        self._short_name = kwargs.get("short_name")
        self._version_format = kwargs.get("version_format")

        sub_dir = kwargs.get("sub_dir")
        sub_dir = sub_dir.strip("/") if sub_dir else "Files"
        path = os.path.normpath(os.path.join(shot.path, sub_dir, self._media_type, self.name))
        super(BaseMedia, self).__init__(name, path)

        self.commit_data = None

    def __str__(self):
        return "{0}:{1}:{2}".format(self._media_type, self._file_type, self.name)

    def create(self, **kwargs):
        if not self._shot.exists():
            raise Exception("Shot {} does not exist".format(self._shot.name))

        BaseFold.create(
            self,
            project=self._shot.project.name,
            reel=self._shot.reel.name,
            shot=self._shot.name,
            media_type=self._media_type,
            **kwargs
        )

    @property
    def name(self):
        return self.validate_name(self._name)

    @property
    def short_name(self):
        return self._short_name

    @property
    def version_format(self):
        if self._version_format.startswith("{"):
            version_format = "v" + self._version_format
        else:
            version_format = self._version_format
        return version_format

    @property
    def name_template(self):
        return self._name_template

    @property
    def validators(self):
        return self._validators

    @property
    def file_type(self):
        return self._file_type

    @property
    def media_type(self):
        return self._media_type

    @property
    def extension(self):
        return self._extension

    def validate_name(self, name):
        format_dict = self.__formatting_dict()
        pattern = self._name_template.format(name="(.+)", **format_dict)
        if bool(re.match(pattern, name)):
            return name
        else:
            return self._name_template.format(name=name, **format_dict)

    def __formatting_dict(self):
        return {
            "shot": self._shot.name,
            "project": self._shot.project,
            "reel": self._shot.reel,
            "short_name": self._short_name,
            "extension": self._extension,
            "file_type": self._file_type,
            "media_type": self._media_type
        }

    def exists(self, with_versions=False):
        if with_versions:
            versions_details = self.get_info("versions")
            if versions_details:
                return True
            else:
                return False
        else:
            return os.path.exists(self.path)

    def version(self, version=None, suffixes=None, views=None, frame_range=None):
        if not self.exists():
            return None
        return Version(self, version, suffixes=None, views=None, frame_range=None)

    def fetch_versions(self):
        version_details = self.get_info("versions")
        if version_details:
            return list(version_details.keys())

    def get_all_versions(self):
        for version in self.fetch_versions():
            yield self.version(version=version)

    def commit(self):
        pass  # TODO commit media version

    @property
    def crumbs(self):
        return "{project}/{reel}/{shot}/{media}/{name}".format(
            project=self.shot.project,
            reel=self.shot.reel,
            shot=self.shot.name,
            media=self.media_type,
            name=self.name
        )

    @property
    def shot(self):
        return self._shot


class FileMedia(BaseMedia):
    pass


class DataMedia(BaseMedia):
    pass


class MediaFactory(BaseMedia):
    __MEDIA_CLASSES = {k: v for k, v in inspect.getmembers(sys.modules[__name__], is_media_class)}
    __ALL_TYPES = configs.GlobalConfig.all_media_types

    def __new__(cls, shot, name, media_type=None):
        """Create media
        Args:
            shot(Shot): shot
            name(str): name of the media
            media_type: type_of_media
        Returns:
            BaseMedia
        """
        if not isinstance(shot, Shot):
            raise Exception("{} is not a shot".format(shot))

        if not media_type:
            media_type = "_default"

        media_type_dict = cls.get_type(media_type)
        media_class_name = media_type_dict.get("media_class")
        if not media_class_name:
            raise Exception("Media class {} is not defined in the config".format(media_class_name))

        media_class = cls.__MEDIA_CLASSES.get(media_class_name)
        if not media_class:
            raise Exception("Media class {} not found".format(media_class_name))
        media_type_dict["name"] = name
        return media_class(shot=shot, **media_type_dict)

    @classmethod
    def get_type(cls, type_name):
        _type = cls.__ALL_TYPES.get(type_name, {})
        if not _type:
            for t in cls.__ALL_TYPES.values():
                if t["media_type"] == type_name:
                    _type = t
                    break
        if not _type:
            return None
        falloff_from = _type.get("__falloff")
        if falloff_from:
            falloff = cls.__ALL_TYPES.get(falloff_from, {}).copy()
        else:
            falloff = cls.__ALL_TYPES.get("_default", {}).copy()
        falloff.update(_type)

        return falloff.copy()


    @classmethod
    def get_media_path_patterns(cls):
        for key in cls.__ALL_TYPES.keys():
            media_type = cls.get_type(key)
            if media_type.get("file_type") == "SingleFile":
                filename_regex = r"(?P=name)(_(?P<suffix>[\w]+))?_(?P<version>[\w\.]+)\.(?P<ext>[\w]+))?"
            else:
                filename_regex = r"(?P=name)(_(?P<suffix>[\w]+))?_(?P=version)\.(?P<ext>[\w]+))?"
            pattern_format = cls.get_media_path_format(media_type)
            pattern_format = pattern_format.replace("\\", "\\\\")
            pattern = pattern_format.format(
                shot_dir=get_fold_regex_pattern(),
                sub_dir=media_type.get("sub_dir", "").replace("\\", "\\\\"),
                media_type="(?P<media_type>{0})".format(media_type.get("media_type"), r"[\w]+"),
                name=r"(?P<name>[\w]+)(",
                filename=filename_regex,
                version=r"(?P<version>[\w\.]+))?("
            )
            yield media_type.get("media_type"), pattern

    @classmethod
    def get_media_path_format(cls, media_type, file_path=True):
        if isinstance(media_type, str):
            media_type = cls.get_type(media_type)
        elements = ["{shot_dir}"]
        sub_dir = media_type.get("sub_dir")
        if sub_dir:
            elements.append("{sub_dir}")
        elements.append("{media_type}")
        elements.append("{name}")
        if file_path:
            if media_type.get("file_type") == "SingleFile":
                elements.append("{filename}")
            else:
                elements.append("{version}")
                elements.append("{filename}")

        pattern_format = os.path.join(*elements)

        return pattern_format

    @classmethod
    def get_all_media_type(cls, filters=None):
        # TODO implement filter
        return list(cls.__ALL_TYPES.keys())

    @classmethod
    def is_media(cls, obj):
        """checks if object is media type object or not"""
        for media_class in cls.__MEDIA_CLASSES.values():
            if isinstance(obj, media_class):
                return True
        return False


class Version(object):
    _instances = {}
    _pattern = re.compile(VERSION_PATTERN)
    _valid_views = ["left", "right"]

    def __init__(self, media: BaseMedia, version=None, suffixes=None, views=None, frame_range=None):
        super(Version, self).__init__()
        self._thumbnail = None
        self._media = media

        self._suffixes = suffixes if suffixes else []

        if views and not all([v in self._valid_views for v in views]):
            raise Exception("Only {} are supported as views".format(",".join(self._valid_views)))
        self._views = views if views else []

        self._seq = None
        self._filepaths = None
        self._filepath = None
        self._created_by = None
        self._created_at = None
        self._data = {}

        if version not in (None, "latest"):
            self._major, self._minor = self.get_major_minor(version)
            if self._major is None:
                raise Exception("Version({0}) could not be parsed. ".format(version))

            self._version = self.media.version_format.format(major=self._major, minor=self._minor)
        else:
            self._version = version
            self._major = self._minor = None
        versions_info = self._media.info.get("versions", {})
        info = versions_info.get(self._version)
        if info:
            # set self._suffixes
            # set self._views
            self.set_attributes_from_info(info)
        else:
            if versions_info:
                latest_major, _ = max([self.get_major_minor(k) for k in versions_info.keys()])
                if self._version is None:
                    self._version = self.media.version_format.format(major=int(latest_major) + 1, minor=0)
                    self._major, self._minor = self.get_major_minor(self._version)
                    self.set_attributes(frame_range)
                elif self._version == "latest":
                    self._version = self.media.version_format.format(major=int(latest_major), minor=0)
                    self._major, self._minor = self.get_major_minor(self._version)
                    info = versions_info.get(self._version)
                    if info:
                        # set self._suffixes
                        # set self._views
                        self.set_attributes_from_info(info)
            else:
                self._version = self.media.version_format.format(major=1, minor=0)
                self._major = 1
                self._minor = 0

                self.set_attributes(frame_range)

    def __str__(self):
        return self.version

    def set_attributes(self, frame_range=None):
        name_format = "{name}"
        if not frame_range:
            frame_range = "1-1"
        if self._suffixes:
            if self.file_type in ("Sequence", "SingleFile") and len(self._suffixes) > 1:
                raise Exception("{} can only have one suffix got {}".format(self.file_type, len(self._suffixes)))
            name_format += "_{suffix}"  # "{name}_{suffix}_{version}.{ext}"
        if self._views:
            name_format += "_%V"
        name_format += "_{version}"
        if self.file_type == "SingleFile":
            name_format += ".{ext}"
            filename = name_format.format(
                name=self.media.name,
                suffix=self._suffixes[0] if self._suffixes else None,
                version=self.version,
                ext=self.media.extension
            )
            self._filepath = os.path.join(self.path, filename)
        elif self.file_type == "Sequence":
            name_format += ".####.{ext}"
            filename = name_format.format(
                name=self.media.name,
                suffix=self._suffixes[0] if self._suffixes else None,
                version=self.version,
                ext=self.media.extension
            )
            self._filepath = os.path.join(self.path, filename)
            self._seq = FileSequence(self._filepath, pad_style=PAD_STYLE_HASH1)
            self._seq.setFrameRange(frame_range)
        elif self.file_type == "MultiSequence":
            if not self._suffixes:
                raise Exception("MultiSequence cannot be created without suffix")

            self._filepath = []
            self._seq = []
            for suffix in self._suffixes:
                name_format += ".####.{ext}"
                filename = name_format.format(
                    name=self.media.name,
                    suffix=suffix,
                    version=self.version,
                    ext=self.media.extension
                )
                file_path = os.path.join(self.path, filename)
                self._filepath.append(file_path)
                seq = FileSequence(file_path, pad_style=PAD_STYLE_HASH1)
                seq.setFrameRange(frame_range)
                self._seq.append(seq)

    def set_attributes_from_info(self, info):
        # set data.
        self._filepath = info.get("filepath")
        frame_range = info.get("frame_range")
        if self.file_type == "MultiSequence":
            self._seq = []
            for filepath in self._filepath:
                seq = FileSequence(filepath, pad_style=PAD_STYLE_HASH1)
                seq.setFrameRange(frame_range)
                self._seq.append(seq)
        else:
            self._seq = FileSequence(self._filepath, pad_style=PAD_STYLE_HASH1)
        self._seq.setFrameRange(frame_range)
        self._data = info.get("data")
        self._created_by = info.get("created_by")
        self._created_at = info.get("created_at")
        self._suffixes = info.get("suffixes")
        self._views = info.get("views")

    def get_major_minor(self, version=None):
        if version is None:
            version = self.version
        if version:
            if isinstance(version, int):
                return version, 0
            if isinstance(version, float):
                if version.is_integer():
                    return int(version), 0
                else:
                    splits = str(version).split(".")
                    return int(splits[0]), int(splits[1])
            if version.isdigit():
                return int(version), 0

            match = self.version_pattern.match(version)
            if bool(match):
                group_dict = match.groupdict()
                major = group_dict.get("major")
                minor = group_dict.get("minor", 0)
                return int(major), int(minor)

        return None, None

    def create(self, location=Location.CENTRAL, **kwargs):
        exists = self.exists(all_files=True)
        if exists == location or exists == Location.BOTH:
            raise Exception("Files already exists")

        paths = []
        if location == Location.BOTH:
            paths = [self.local_path, self.path]
        elif location == Location.LOCAL:
            paths = [self.local_path]
        elif location == Location.CENTRAL:
            paths = [self.path]

        if not paths:
            return None

        for path in paths:
            if not os.path.exists(path):
                os.makedirs(path)

        self.media.create()

        self._created_at = datetime.datetime.now()
        self._created_by = current_auth().user.name

        data = kwargs.get("data", None)
        if data is not None:
            del kwargs["data"]
        self.update_info(data=data, **kwargs)

    def create_link_from(self, source):
        # TODO now only support single seq, without any views
        # need to integrate MUltiseq supoort and views support
        # suffix, vies has to be parsed from file path
        if self.file_type == "SingleFile":
            raise Exception("SingleFile cannot be linked")

        if isinstance(source, self.__class__):
            if source.file_type == "SingleFile":
                raise Exception("SingleFile cannot be linked")
            src = source.path
        else:
            src = None
            for parent, dirs, files in os.walk(source):
                if files:
                    src = parent
                    break
        if src:
            seqs = findSequencesOnDisk(src, pad_style=PAD_STYLE_HASH1)
            if not seqs:
                raise Exception("Seq not found in the path")
            if self.file_type != "MultiSequence" and len(seqs) > 1:
                raise Exception("Found multiple seq in the path cannot sink it with {}".format(self.file_type))

            utility.create_symlink(src, self.path)
            seqs = findSequencesOnDisk(self.path, pad_style=PAD_STYLE_HASH1)
            if len(seqs) > 1:
                raise NotImplementedError("not implemented")
            else:
                self._seq = seqs[0]
                self._filepath = self._seq.format("{dirname}{basename}{padding}{extension}")
            self._created_by = current_auth().user.name
            self._created_at = datetime.datetime.now()

            self.update_info(data={"original_path": src})

    def create_copy_from(self, source, copy_to=Location.CENTRAL):
        # TODO test it in both local and central
        if self.file_type == "Singlefile":
            raise Exception("Single file type is not supported")
        if self.exists(all_files=True) == copy_to:
            raise Exception("Files already exists")

        if copy_to == Location.BOTH:
            paths = (self.path, self.local_path)
        elif copy_to == Location.LOCAL:
            paths = (self.local_path,)
        elif copy_to == Location.CENTRAL:
            paths = (self.path,)
        else:
            return None

        src = None
        for parent, dirs, files in os.walk(source):
            if files:
                src = parent
                break

        if src:
            src_seqs = findSequencesOnDisk(src)
            if len(src_seqs) > 1:
                raise Exception("More than one seq found in the path")
            for path in paths:
                if not os.path.exists(path):
                    os.makedirs(path)
                for fs in src_seqs:
                    cp = fs.copy()
                    cp.setDirname(path)
                    if len(src_seqs) == 1:
                        cp.setBasename(self.seq.basename())
                        self.seq.setFrameRange(fs.frameRange())
                    copy_tasks = [(shutil.copy, fs.frame(frame), cp.frame(frame)) for frame in cp.frameSet()]
                    utility.TaskThreader.add_to_queue(copy_tasks)

            self._created_by = current_auth().user.name
            self._created_at = datetime.datetime.now()

            self.update_info(data={"original_path": src})

    def delete(self):
        if not os.path.exists(self.path) or not os.listdir(self.path):
            return None
        if utility.is_sym_link(self.path):
            os.remove(self.path)
            # TODO test it in linux and mac
        else:
            if isinstance(self.seq, list):
                for seq in self._seq:
                    utility.TaskThreader.add_to_queue([(os.remove, seq.frame(frame)) for frame in seq.frameSet()])
            else:
                utility.TaskThreader.add_to_queue([(os.remove, self.seq.frame(frame)) for frame in self.seq.frameSet()])

            os.rmdir(self.path)

        info = self.media.info.get("versions", {})
        info.update({"_del_{}".format(self._version): {
            "deleted": datetime.datetime.now()
        }})
        # TODO save more data on delete
        del info[self._version]
        self.media.update_info(versions=info)

    def new(self):
        versions_info = self._media.get_info("versions")
        latest_major, _ = max([self.get_major_minor(k) for k in versions_info.keys()])
        return self.media.version_format.format(major=latest_major + 1, minor=0)

    def exists(self, all_files=False):
        filepaths = self.filepaths
        if filepaths:
            if all_files:
                # availability = set([utility.find_available_location(filepath, filepath.replace(self.path, self.local_path))
                #                     for filepath in filepaths])
                # if len(availability) == 1:
                #     return availability.pop()
                central = local = True
                for filepath in filepaths:
                    available = utility.find_available_location(filepath, filepath.replace(self.path, self.local_path))
                    if central and available not in (Location.BOTH, Location.CENTRAL):
                        central = False
                    if local and available not in (Location.BOTH, Location.LOCAL):
                        local = False
                    if not local and not central:
                        # if both false then the file is unavailable in both placen we dont have to loop any more
                        break
                if central and local:
                    return Location.BOTH
                elif central:
                    return Location.CENTRAL
                elif local:
                    return Location.LOCAL
                else:
                    return Location.NONE
            else:
                return utility.find_available_location(filepaths[0], filepaths[0].replace(self.path, self.local_path))
        else:
            return Location.NONE

    def centralise(self):
        exists = self.exists(all_files=True)
        if self.exists() in (Location.CENTRAL, Location.BOTH):
            utility.logger.warning("Version already exists in central")
            return None

        if not os.listdir(self.local_path):
            raise Exception("Local version is not available")

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        copy_tasks = [(shutil.copy, path.replace(self.path, self.local_path),  path) for path in self.filepaths]
        utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

    def localise(self):
        if self.exists() in (Location.LOCAL, Location.BOTH):
            utility.logger.warning("Version already exists in local")
            return None
        if self.exists() is not Location.CENTRAL:
            raise Exception("Central version is not available")

        self.create(location=Location.LOCAL)
        copy_tasks = [(shutil.copy, path, path.replace(self.path, self.local_path)) for path in self.filepaths]
        utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

    def update_info(self, **kwargs):

        self_info = {
            "filepath": self.filepath,
            "frame_range": self.frame_range,
            "created_by": self._created_by,
            "created_at": self._created_at,
            "modified_at": datetime.datetime.now(),
            "suffixes": self._suffixes,
            "views": self._views
        }

        self_info.update(kwargs)
        versions_info = self.media.info.get("versions", {})
        if kwargs.get("data") and versions_info.get(self.version, {}).get("data"):
            raise Exception("Data cannot be updated")
        versions_info.update({self.version: self_info})
        self.media.update_info(versions=versions_info)

    def get_info(self, key):
        return self.info.get(key)

    @property
    def info(self):
        return self.media.info.get("versions", {}).get(self.version, {})

    @property
    def data(self):
        return self._data

    @property
    def filepaths(self):
        paths = []
        seq = self.seq
        if self.file_type == "SingleFile":
            if self._views:
                paths = [self.filepath.replace("%V", v) for v in self._views]
            else:
                paths = [self.filepath]
        elif self.file_type == "Sequence":
            if self._views:
                for f in seq.frameSet():
                    paths.extend([seq.frame(f).replace("%V", v) for v in self._views])
            else:
                paths = [seq.frame(f) for f in seq.frameSet()]

        elif self.file_type == "MultiSequence":
            for seq in seq:
                if self._views:
                    for f in seq.frameSet():
                        paths.extend([seq.frame(f).replace("%V", v) for v in self._views])
                else:
                    paths.extend([seq.frame(f) for f in seq.frameSet()])
        return paths

    @property
    def start(self):
        seq = self.seq
        if isinstance(seq, list):
            return seq[0].start()
        if seq:
            return seq.start()

    @property
    def end(self):
        seq = self.seq
        if isinstance(seq, list):
            return seq[0].end()
        if seq:
            return seq.end()

        return None

    @property
    def frame_range(self):
        seq = self.seq
        if isinstance(seq, list):
            return seq[0].frameRange()
        if seq:
            return seq.frameRange()

        return None

    @property
    def filepath(self):
        return self._filepath
    
    @property
    def local_filepath(self):
        return self._filepath.replace(configs.UserConfig.central_project_path, configs.UserConfig.local_project_path)

    @property
    def seq(self):
        return self._seq if self._seq else self._set_seq()

    @property
    def crumbs(self):
        return self.media.crumbs + "/{}".format(self.version)

    def _set_seq(self):
        if self.filepath is None:
            return None
        seqs = []
        if isinstance(self.filepath, list):
            for filepath in self.filepath:
                if self._views:
                    for view in self._views:
                        filepath = filepath.replace("%V", "{0}".format(view))
                        try:
                            seq = FileSequence.findSequenceOnDisk(filepath)
                            seq.setPadStyle(PAD_STYLE_HASH1)
                        except FileSeqException:
                            seq = FileSequence(filepath, pad_style=PAD_STYLE_HASH1)
                        seqs.append(seq)
                else:
                    try:
                        seq = FileSequence.findSequenceOnDisk(filepath)
                        seq.setPadStyle(PAD_STYLE_HASH1)
                    except FileSeqException:
                        seq = FileSequence(filepath, pad_style=PAD_STYLE_HASH1)
                    seqs.append(seq)
        else:
            if self._views:
                for view in self._views:
                    filepath = self.filepath.replace("%V", "{0}".format(view))
                    try:
                        seq = FileSequence.findSequenceOnDisk(filepath)
                        seq.setPadStyle(PAD_STYLE_HASH1)
                    except FileSeqException as e:
                        seq = FileSequence(self.filepath, pad_style=PAD_STYLE_HASH1)
                    seqs.append(seq)
            else:
                try:
                    seq = FileSequence.findSequenceOnDisk(self.filepath)
                    seq.setPadStyle(PAD_STYLE_HASH1)
                except FileSeqException as e:
                    seq = FileSequence(self.filepath, pad_style=PAD_STYLE_HASH1)

        self._seq = seqs

        return self._seq

    @property
    def path(self):
        if self.file_type == "SingleFile":
            return self.media.path
        else:
            return os.path.join(self.media.path, self.version)

    @property
    def local_path(self):
        return self.path.replace(configs.UserConfig.central_project_path, configs.UserConfig.local_project_path)

    @property
    def file_type(self):
        return self.media.file_type

    @property
    def version(self):
        return self._version

    @property
    def version_pattern(self):
        pattern = self.media.version_format.format(major="])?(?P<major>[0-9]+)", minor="(?P<minor>[0-9]+)")
        pattern = "^([" + pattern + "$"
        c_pattern = re.compile(pattern)
        if c_pattern.groupindex.get("major") is None or c_pattern.groupindex.get("major") != 2:
            # if index not 2 then pattern we crated will fail
            raise Exception("{major} is required in version format or not placed in the beginning, please check config")
        return c_pattern

    @property
    def thumbnail(self):
        if not self._thumbnail:
            path = os.path.join(self.media.path, ".thumbnail")
            file_name = "{}_{}.png".format(self.media.name, self.version)
            self._thumbnail = os.path.join(path, file_name)

        return self._thumbnail

    @property
    def media(self):
        return self._media


def media_from_path(path):

    for media_type, pattern in MediaFactory.get_media_path_patterns():
        match = re.match(pattern, os.path.normpath(path))
        if bool(match):
            media = MediaFactory(
                shot=Shot(match.group("project"), match.group("reel"), match.group("shot")),
                name=match.group("name"),
                media_type=media_type
            )
            if match.group("version"):
                return Version(media, match.group("version"))
            else:
                return media


def get_all_media(shot, filters=None):
    # TODO implement filters
    for key in MediaFactory.get_all_media_type():
        media_type = MediaFactory.get_type(key)
        path_format = MediaFactory.get_media_path_format(media_type, file_path=False)
        path = path_format.format(
            shot_dir=shot.path,
            media_type=media_type.get("media_type"),
            sub_dir=media_type.get("sub_dir"),
            name=""
        ).strip()
        if os.path.exists(path):
            for dir in os.listdir(path):
                yield MediaFactory(shot, dir, media_type.get("media_type"))


# shot = Shot("PROJ", "REEL01", "SHOT_01")
# mc = MediaFactory(shot=shot, name="Final2", media_type="Render")
#
# auth = Auth("admin", "admin")
# mc.create()
#
# v = Version(mc, "latest")
# v.create()
# print(v.filepath)
# res = auth.authorise()
#
# # path = "F:\\NAS\\PROJ\\01_Shots\\REEL01\\SHOT_01\\Files\\NukeScript\\Final2\\Final2_v01.000.nk"
# path = "F:\\NAS\\PROJ\\01_Shots\\REEL01\\SHOT_01\\Renders\\Render\\Final2"
#
#
# for m in get_all_media(shot):
#     print("_media", m)