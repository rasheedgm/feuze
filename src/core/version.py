import datetime
import os
import re
import shutil

import fileseq
from fileseq import FileSequence, findSequencesOnDisk, PAD_STYLE_HASH1, FrameSet

from feuze.core import configs, utility
from feuze.core.constant import VERSION_PATTERN, VersionType, DEFAULT_EXTENSIONS, SEQ_FORMAT, Location
from feuze.core.user import current_auth

# TODO removing

class BaseVersion(object):
    _instances = {}
    _pattern = "[vV]([0-9]+)$"
    _version_format = "v{:02d}"
    _filename_format = ""

    def __init__(self, parent, version_type, suffix=None, version=None, ext=None):
        super(TaskVersion, self).__init__()
        self._parent = parent or None
        self._suffix = suffix or ""
        if not version:
            version = self.new()
        if not bool(self.match_pattern(version)) and not bool(re.match("^([0-9]+)$", str(version))):
            raise ValueError("Version should be either {} or number".format(self._version_format))
        if not bool(self.match_pattern(version)):
            version = self.formatted_version(version)
        self._version = version
        # TODO make prop

        if version_type in (VersionType.IMAGESEQ, VersionType.MULTISEQ):
            self._path = os.path.join(self._parent.path, self._version)
        else:
            self._path = self._parent.path
        self._local_path = self._path.replace(
            configs.UserConfig.central_project_path, configs.UserConfig.local_project_path)
        ext = ext if ext else DEFAULT_EXTENSIONS[version_type]
        if not ext.startswith("."):
            ext = "." + ext

        self._type = version_type
        self._created_by = None
        self._created_at = None
        self._filepaths = []
        self._ext = ext
        self._thumbnail = None

        parent_info = self._parent.get_info("versions")
        self._info = parent_info.get(version) if parent_info else {}

        if self._info:
            for key, item in self._info.items():
                if hasattr(self, "_{}".format(key)):
                    setattr(self, "_{}".format(key), item)


        # self.find_files()

        if not self._filepaths:
            self.__set_filepaths()

        if parent not in self.__class__._instances.keys():
            self.__class__._instances[parent] = {version: self}
        if version not in self.__class__._instances[parent].keys():
            self.__class__._instances[parent][version] = self

    def __int__(self):
        return self.__int_version_from_str()

    def __str__(self):
        return self.version

    def create(self, local=False):
        """Created version folder if required, updates current info to info file"""
        exists = utility.find_available_location(self._path, self._local_path)
        if exists == Location.BOTH:
            return self

        if not self._parent.exists() and self._path != self._parent.path:
            self._parent.create(local=local)

        if exists != Location.CENTRAL:
            os.makedirs(self._path)
            self._created_by = current_auth().user.name
            self._created_at = datetime.datetime.now()

        if local and exists != Location.LOCAL:
            os.makedirs(self._local_path)

        self.update_info(**self.info)
        return self

    def new(self):
        try:
            versions = self.get_all_versions()

            if versions:
                return self.formatted_version(int(max(versions)) + 1)
            else:
                return self.formatted_version(1)
        except FileNotFoundError:
            return self.formatted_version(1)

    def latest(self):
        try:
            versions = self.get_all_versions()
            if versions:
                return self.formatted_version(version=max(versions))
            else:
                return self.formatted_version(version=1)
        except FileNotFoundError:
            return self.formatted_version(1)

    def update_info(self, **kwargs):
        info = self._parent.info.get("versions", {})
        info.update({self._version: kwargs})
        self._parent.update_info(versions=info)

    def get_info(self, attr):
        return self._info.get(attr)

    def exists(self):
        # TODO might not work on local file as findseq is running on central
        seq = FileSequence(self.filepaths[0])
        file_path = seq[0].frame(seq[0].start())
        return utility.find_available_location(file_path, file_path.replace(self._path, self._local_path))

    def delete(self):
        ## TODO CHECK
        if not os.path.exists(self._path) or not os.listdir(self._path):
            return None
        if utility.is_sym_link(self._path):
            if self._parent.path != self.path:
                os.remove(self._path)
            # TODO test it in linux and mac
        else:
            for filepath in self._filepaths:
                seq = fileseq.findSequenceOnDisk(filepath)
                if seq:
                    utility.TaskThreader.add_to_queue([(os.remove, seq.frame(frame)) for frame in seq.frameSet()])
            if self._parent.path != self.path:
                os.rmdir(self._path)

        info = self._parent.info.get("versions", {})
        info.update({"_del_{}".format(self._version): {
            "deleted": datetime.datetime.now()
        }})
        # TODO save more data on delete
        del info[self._version]
        self._parent.update_info(versions=info)

    def centralise(self):
        if self.exists() in (Location.CENTRAL, Location.BOTH):
            utility.logger.warning("Version already exists in central")
            return None

        if not os.listdir(self._local_path):
            raise Exception("Local version is not available")

        # src_seqs = findSequencesOnDisk(self._local_path)
        for path in self.local_filepaths:
            seq = FileSequence(path)
            central_copy = seq.copy()
            central_copy.setDirname(self._path)
            copy_tasks = [(shutil.copy, seq.frame(frame), central_copy.frame(frame))
                          for frame in central_copy.frameSet()]
            utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

    def localise(self):
        if self.exists() in (Location.LOCAL, Location.BOTH):
            utility.logger.warning("Version already exists in local")
            return None
        if self.exists() is not Location.CENTRAL:
            raise Exception("Central version is not available")

        self.create(local=True)
        for path in self.filepaths:
            seq = FileSequence(path)
            local_copy = seq.copy()
            local_copy.setDirname(self._local_path)
            copy_tasks = [(shutil.copy, seq.frame(frame), local_copy.frame(frame)) for frame in local_copy.frameSet()]
            utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

    def create_link(self, path, link_to=Location.CENTRAL):
        # only link to central
        # TODO if signle file then link file or fail
        src = None
        for parent, dirs, files in os.walk(path):
            if files:
                src = parent
                break
        if src:
            utility.create_symlink(src, self.path)
            self.update_from_path()
            self._created_by = current_auth()
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
                        cp.setBasename("{}.".format(self.formatted_file_name(with_extension=False)))
                    copy_tasks = [(shutil.copy, fs.frame(frame), cp.frame(frame)) for frame in cp.frameSet()]
                    utility.TaskThreader.add_to_queue(copy_tasks)

            self.update_from_path()
            self._created_by = current_auth()
            self._created_at = datetime.datetime.now()
            self.update_info(copied_from=path, **self.info)

    def update_from_path(self):
        # TODO check path and update version info.
        versions = self.get_all_versions()
        if self._version in [self.formatted_version(v) for v in versions]:
            seq = []
            if os.path.isdir(self._path) and self._path != self._parent.path:
                seq = findSequencesOnDisk(self._path, pad_style=PAD_STYLE_HASH1)
            else:
                # if it path and parent path is same it means file is in same path and
                # we expect that to be in same name as its allowed

                file_name = self.formatted_file_name(with_extension=False) + ".*"  # TODO replace version with wild card
                pattern = os.path.join(self._path, file_name)
                seq = findSequencesOnDisk(pattern, pad_style=PAD_STYLE_HASH1)

                # file_name = [f for f in os.listdir(self._parent.path) if self.match_pattern(os.path.splitext(f)[0])]
                # self._filepaths = [os.path.join(self._parent.path, f) for f in file_name]

            if len(seq) > 1:
                self._type = VersionType.MULTISEQ
            elif seq:
                if seq[0].frameSet():
                    self._type = VersionType.IMAGESEQ
                else:
                    if seq[0].extension() == "mov":
                        self._type = VersionType.QUICKTIME
                    else:
                        self._type = VersionType.SINGLEFILE

            self._filepaths = [fs.format(SEQ_FORMAT) for fs in seq]  # TODO format test

            _, self._ext = os.path.splitext(self._filepaths[0])

        self.update_info(**self.info)

    def get_info_str(self, html=False):
        line = "<b>{}:</b>\t<b>{}</b>\n" if html else "{}:\t{}\n"
        str_info = ""
        for key, value in self.info.items():
            str_info += line.format(key, value)
        return str_info

    def __set_filepaths(self):
        if self._type in (VersionType.SINGLEFILE, VersionType.QUICKTIME):
            self._filepaths = [os.path.join(
                self._path,
                self.formatted_file_name()
            )]
        else:
            self._filepaths = [os.path.join(
                self._path,
                self.formatted_file_name(seq=True)
            )]

    def match_pattern(self, string):
        return re.match(self._regex, str(string))

    def __int_version_from_str(self, string=None):
        if string is None:
            string = self._version
        match = re.search(self._pattern, string)
        if match:
            return int((re.search("([0-9]+)$", string)[0]))

    def __valid_filename_format(self, seq=False, with_extension=True):
        """Validated filename format, adds extensions if missing"""
        filename_format = self._filename_format
        if self._filename_format:
            if not self._filename_format.find("{extension}") == -1:
                filename_format += "{extension}"
        else:
            filename_format = "{parent_name}_{version}{extension}"

        if seq and "#" not in self._filename_format:
            splits = self._filename_format.split("{")
            splits.insert(-1, "####")
            filename_format = "{".join(splits)
        if with_extension:
            return filename_format
        else:
            return "{".join(filename_format.split("{")[:-1])

    def formatted_file_name(self, seq=False, with_extension=True):
        return self.__valid_filename_format(seq=seq, with_extension=with_extension).format(
            version=self._version,
            extension=self._ext,
            **self.__get_format_args()
        )

    def formatted_version(self, version):
        return self._version_format.format(int(version))

    def get_all_versions(self):
        versions = []
        for v in os.listdir(self._parent.path):
            if bool(self.match_pattern(v)):
                versions.append(self.__int_version_from_str(v))
            else:
                if os.path.isfile(os.path.join(self._parent.path, v)):
                    file_name, ext = os.path.splitext(v)
                    if bool(self.match_pattern(file_name)):
                        versions.append(self.__int_version_from_str(file_name))
        return versions

    def __get_format_args(self):
        shot_inst = getattr(self._parent, "shot")
        if shot_inst.__class__.__name__ == "Shot":
            shot = shot_inst.name
            reel = shot_inst.reel.name
            project = shot_inst.project.name
        else:
            shot = reel = project = ""
        parent_type = getattr(self._parent, "type") or ""
        return {
            "shot": shot,
            "reel": reel,
            "project": project,
            "parent_type": parent_type,
            "parent_name": self._parent.name,
            "suffix": self.suffix
        }

    @property
    def _regex(self):
        version_regex = "^{}".format(self._pattern)

        filename_format = "^" + self.__valid_filename_format(with_extension=False)
        filename_regex = filename_format.format(
            version=self._pattern,
            **self.__get_format_args()
        )
        return "{}|{}".format(version_regex, filename_regex)

    @property
    def suffix(self):
        return self._suffix

    @property
    def thumbnail(self):
        if not self._thumbnail:
            path = os.path.join(self._parent.path,".thumbnail")
            file_name = "{}_{}.png".format(self._parent.name, self.version)
            self._thumbnail = os.path.join(path, file_name)

        return self._thumbnail

    @property
    def info(self):
        return {
            "version": self._version,
            "type": self._type,
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
    def version(self):
        return self._version

    @property
    def filepaths(self):
        return self._filepaths

    @property
    def local_filepaths(self):
        return [path.replace(self.path, self._local_path) for path in self._filepaths]

    @classmethod
    def get_version_instance(cls, parent, version_type, version):
        parent_ins = cls._instances.get(parent)
        if parent_ins and version in parent_ins.keys():
            return parent_ins[version]
        else:
            return cls(parent, version_type, version)


class FootageVersion(object):
    _instances = {}
    _pattern = re.compile(VERSION_PATTERN)

    def __init__(self, parent, version=None, ext=None, version_type=VersionType.IMAGESEQ):
        super(FootageVersion, self).__init__()
        self._parent = parent or None
        if not version:
            version = self.new()
        if not bool(self._pattern.match(str(version))) and not bool(re.match("^([0-9]+)$", str(version))):
            raise ValueError("Version should be either v%02d or number")
        if not bool(self._pattern.match(str(version))):
            version = "v%02d" % int(version)
        self._version = version
        self._path = os.path.join(self._parent.path, self._version)
        self._local_path = self._path.replace(
            configs.UserConfig.central_project_path, configs.UserConfig.local_project_path)
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
        return utility.find_available_location(file_path, file_path.replace(self._path, self._local_path))

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
        exists = utility.find_available_location(self._path, self._local_path)
        if exists == Location.BOTH:
            return self

        if not self._parent.exists():
            self._parent.create()

        if exists != Location.CENTRAL:
            os.makedirs(self._path)
            self._created_by = current_auth().user.name
            self._created_at = datetime.datetime.now()

        if local and exists != Location.LOCAL:
            os.makedirs(self._local_path)

        self.update_info(**self.info)
        return self

    def delete(self):
        if not os.path.exists(self._path) or not os.listdir(self._path):
            return None
        if utility.is_sym_link(self._path):
            os.remove(self._path)
            # TODO test it in linux and mac
        else:
            for seq in self._seq:
                utility.TaskThreader.add_to_queue([(os.remove, seq.frame(frame)) for frame in seq.frameSet()])

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
            utility.create_symlink(src, self.path)
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
                    utility.TaskThreader.add_to_queue(copy_tasks)

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
            utility.logger.warning("Version already exists in central")
            return None

        if not os.listdir(self._local_path):
            raise Exception("Local version is not available")

        src_seqs = findSequencesOnDisk(self._local_path)
        for seq in src_seqs:
            central_copy = seq.copy()
            central_copy.setDirname(self._path)
            copy_tasks = [(shutil.copy, seq.frame(frame), central_copy.frame(frame))
                          for frame in central_copy.frameSet()]
            utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

    def localise(self):
        if self.exists() in (Location.LOCAL, Location.BOTH):
            utility.logger.warning("Version already exists in local")
            return None
        if self.exists() is not Location.CENTRAL:
            raise Exception("Central version is not available")

        self.create(local=True)
        for seq in self._seq:
            local_copy = seq.copy()
            local_copy.setDirname(self._local_path)
            copy_tasks = [(shutil.copy, seq.frame(frame), local_copy.frame(frame)) for frame in local_copy.frameSet()]
            utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

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
            if self._type in (VersionType.SINGLEFILE, VersionType.QUICKTIME):
                seq_path = os.path.join(
                    self._path,
                    "{}_{}{}".format(self._parent.name, self._version, self._ext)
                )
            else:
                seq_path = os.path.join(
                    self._path,
                    "{}_{}.####{}".format(self._parent.name, self._version, self._ext)
                )

            # TODO need to work for multiseq

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
            path = os.path.join(self._parent.path, ".thumbnail") # os.path.dirname(BaseFold.thumbnail.fget(self._parent))
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


class TaskVersion(object):
    _instances = {}
    _pattern = "[vV]([0-9]+).([0-9]+)$"
    _version_format = "v{:02d}.{:03d}"
    _filename_format = ""

    def __init__(self, parent, version=None, suffix=None, version_type=VersionType.SINGLEFILE, ext=None):
        super(TaskVersion, self).__init__()
        self._parent = parent or None
        self._suffix = suffix or ""
        if not version:
            version = self.new()
        if not bool(self.match_pattern(version)) and not bool(re.match("^([0-9]+)$", str(version))):
            raise ValueError("Version should be either {} or number".format(self._version_format))
        if not bool(self.match_pattern(version)):
            version = self.formatted_version(version)
        self._version = version

        # TODO make prop

        if version_type in (VersionType.IMAGESEQ, VersionType.MULTISEQ):
            self._path = os.path.join(self._parent.path, self._version)
        else:
            self._path = self._parent.path
        self._local_path = self._path.replace(
            configs.UserConfig.central_project_path, configs.UserConfig.local_project_path)
        if not ext:
            if hasattr(parent, "extension"):
                ext = getattr(parent, "extension")
            else:
                ext = DEFAULT_EXTENSIONS[version_type]
        if not ext.startswith("."):
            ext = "." + ext

        self._type = version_type
        self._created_by = None
        self._created_at = None
        self._filepaths = []
        self._ext = ext
        self._thumbnail = None

        parent_info = self._parent.get_info("versions")
        self._info = parent_info.get(version) if parent_info else None

        if self._info:
            for key, item in self._info.items():
                if hasattr(self, "_{}".format(key)):
                    setattr(self, "_{}".format(key), item)

        # self.find_files()

        if not self._filepaths:
            self.__set_filepaths()

        if parent not in self.__class__._instances.keys():
            self.__class__._instances[parent] = {version: self}
        if version not in self.__class__._instances[parent].keys():
            self.__class__._instances[parent][version] = self

    def __int__(self):
        return int(self.__float_version_from_str())

    def __float__(self):
        self.__float_version_from_str()

    def __str__(self):
        return self.version

    def create(self, local=False):
        """Created version folder if required, updates current info to info file"""
        exists = utility.find_available_location(self._path, self._local_path)
        if exists == Location.BOTH:
            return self

        if not self._parent.exists() and self._path != self._parent.path:
            self._parent.create(local=local)

        if exists != Location.CENTRAL:
            os.makedirs(self._path)
            self._created_by = current_auth().user.name
            self._created_at = datetime.datetime.now()

        if local and exists != Location.LOCAL:
            os.makedirs(self._local_path)

        self.update_info(**self.info)
        return self

    def new(self):
        try:
            versions = self.get_all_versions()
            if versions:
                return self.formatted_version(int(max(versions)) + 1)
            else:
                return self.formatted_version(1)
        except FileNotFoundError:
            return self.formatted_version(1)

    def latest(self):
        try:
            versions = self.get_all_versions()
            if versions:
                return self.formatted_version(version=int(max(versions)))
            else:
                return self.formatted_version(version=1)
        except FileNotFoundError:
            return self.formatted_version(1)

    def update_info(self, **kwargs):
        info = self._parent.info.get("versions", {})
        info.update({self._version: kwargs})
        self._parent.update_info(versions=info)

    def get_info(self, attr):
        return self._info.get(attr)

    def exists(self):
        # TODO might not work on local file as findseq is running on central
        seq = FileSequence(self.filepaths[0])
        file_path = seq[0].frame(seq[0].start())
        return utility.find_available_location(file_path, file_path.replace(self._path, self._local_path))

    def delete(self):
        ## TODO CHECK
        if not os.path.exists(self._path) or not os.listdir(self._path):
            return None
        if utility.is_sym_link(self._path):
            if self._parent.path != self.path:
                os.remove(self._path)
            # TODO test it in linux and mac
        else:
            for filepath in self._filepaths:
                seq = fileseq.findSequenceOnDisk(filepath)
                if seq:
                    utility.TaskThreader.add_to_queue([(os.remove, seq.frame(frame)) for frame in seq.frameSet()])
            if self._parent.path != self.path:
                os.rmdir(self._path)

        info = self._parent.info.get("versions", {})
        info.update({"_del_{}".format(self._version): {
            "deleted": datetime.datetime.now()
        }})
        # TODO save more data on delete
        del info[self._version]
        self._parent.update_info(versions=info)

    def centralise(self):
        if self.exists() in (Location.CENTRAL, Location.BOTH):
            utility.logger.warning("Version already exists in central")
            return None

        if not os.listdir(self._local_path):
            raise Exception("Local version is not available")

        # src_seqs = findSequencesOnDisk(self._local_path)
        for path in self.local_filepaths:
            seq = FileSequence(path)
            central_copy = seq.copy()
            central_copy.setDirname(self._path)
            copy_tasks = [(shutil.copy, seq.frame(frame), central_copy.frame(frame))
                          for frame in central_copy.frameSet()]
            utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

    def localise(self):
        if self.exists() in (Location.LOCAL, Location.BOTH):
            utility.logger.warning("Version already exists in local")
            return None
        if self.exists() is not Location.CENTRAL:
            raise Exception("Central version is not available")

        self.create(local=True)
        for path in self.filepaths:
            seq = FileSequence(path)
            local_copy = seq.copy()
            local_copy.setDirname(self._local_path)
            copy_tasks = [(shutil.copy, seq.frame(frame), local_copy.frame(frame)) for frame in local_copy.frameSet()]
            utility.TaskThreader.add_to_queue(copy_tasks, wait=False)

    # def create_link(self, path, link_to=Location.CENTRAL):
    #     # only link to central
    #     # TODO if signle file then link file or fail
    #     src = None
    #     for parent, dirs, files in os.walk(path):
    #         if files:
    #             src = parent
    #             break
    #     if src:
    #         utility.create_symlink(src, self.path)
    #         self.update_from_path()
    #         self._created_by = current_auth()
    #         self._created_at = datetime.datetime.now()
    #
    #         self.update_info(original_path=path, **self.info)

    # def copy_files_from(self, path, copy_to=Location.CENTRAL):
    #     # TODO test it in both local and central
    #     if self.exists() == copy_to:
    #         raise Exception("Files already exists")
    #
    #     if copy_to == Location.BOTH:
    #         paths = (self._path, self._local_path)
    #     elif copy_to == Location.LOCAL:
    #         paths = (self._local_path,)
    #     elif copy_to == Location.CENTRAL:
    #         paths = (self._path,)
    #     else:
    #         return None
    #
    #     src = None
    #     for parent, dirs, files in os.walk(path):
    #         if files:
    #             src = parent
    #             break
    #
    #     if src:
    #         src_seqs = findSequencesOnDisk(src)
    #         for path in paths:
    #             if not os.path.exists(path):
    #                 os.makedirs(path)
    #             for fs in src_seqs:
    #                 cp = fs.copy()
    #                 cp.setDirname(path)
    #                 if len(src_seqs) == 1:
    #                     cp.setBasename("{}.".format(self.formatted_file_name(with_extension=False)))
    #                 copy_tasks = [(shutil.copy, fs.frame(frame), cp.frame(frame)) for frame in cp.frameSet()]
    #                 utility.TaskThreader.add_to_queue(copy_tasks)
    #
    #         self.update_from_path()
    #         self._created_by = current_auth()
    #         self._created_at = datetime.datetime.now()
    #         self.update_info(copied_from=path, **self.info)

    def update_from_path(self):
        # TODO check path and update version info.
        versions = self.get_all_versions()
        if self._version in [self.formatted_version(v) for v in versions]:
            seq = []
            if os.path.isdir(self._path) and self._path != self._parent.path:
                seq = findSequencesOnDisk(self._path, pad_style=PAD_STYLE_HASH1)
            else:
                # if it path and parent path is same it means file is in same path and
                # we expect that to be in same name as its allowed

                file_name = self.formatted_file_name(with_extension=False) + ".*"  # TODO replace version with wild card
                pattern = os.path.join(self._path, file_name)
                seq = findSequencesOnDisk(pattern, pad_style=PAD_STYLE_HASH1)

                # file_name = [f for f in os.listdir(self._parent.path) if self.match_pattern(os.path.splitext(f)[0])]
                # self._filepaths = [os.path.join(self._parent.path, f) for f in file_name]

            if len(seq) > 1:
                self._type = VersionType.MULTISEQ
            elif seq:
                if seq[0].frameSet():
                    self._type = VersionType.IMAGESEQ
                else:
                    if seq[0].extension() == "mov":
                        self._type = VersionType.QUICKTIME
                    else:
                        self._type = VersionType.SINGLEFILE

            self._filepaths = [fs.format(SEQ_FORMAT) for fs in seq]  # TODO format test

            _, self._ext = os.path.splitext(self._filepaths[0])

        self.update_info(**self.info)

    def get_info_str(self, html=False):
        line = "<b>{}:</b>\t<b>{}</b>\n" if html else "{}:\t{}\n"
        str_info = ""
        for key, value in self.info.items():
            str_info += line.format(key, value)
        return str_info

    def __set_filepaths(self):
        if self._type in (VersionType.SINGLEFILE, VersionType.QUICKTIME):
            self._filepaths = [os.path.join(
                self._path,
                self.formatted_file_name()
            )]
        else:
            self._filepaths = [os.path.join(
                self._path,
                self.formatted_file_name(seq=True)
            )]

    def match_pattern(self, string):
        return re.match(self._regex, str(string))

    def __float_version_from_str(self, string=None):
        if string is None:
            string = self._version
        match = re.search(self._pattern, string)
        if match:
            return float((re.search("([0-9]+).([0-9]+)$", string)[0]))

    def __valid_filename_format(self, seq=False, with_extension=True):
        """Validated filename format, adds extensions if missing"""
        filename_format = self._filename_format
        if self._filename_format:
            if not self._filename_format.find("{extension}") == -1:
                filename_format += "{extension}"
        else:
            filename_format = "{parent_name}_{version}{extension}"

        if seq and "#" not in self._filename_format:
            splits = self._filename_format.split("{")
            splits.insert(-1, "####")
            filename_format = "{".join(splits)
        if with_extension:
            return filename_format
        else:
            return "{".join(filename_format.split("{")[:-1])

    def formatted_file_name(self, seq=False, with_extension=True):
        return self.__valid_filename_format(seq=seq, with_extension=with_extension).format(
            version=self._version,
            extension=self._ext,
            **self.__get_format_args()
        )

    @classmethod
    def formatted_version(cls, version):
        splits = str(version).split(".")
        major = splits.pop(0) if splits else 1
        minor = splits.pop(0) if splits else 0

        if major == 0:
            raise Exception("Zero version is not supported")

        return cls._version_format.format(int(major), int(minor))

    def get_all_versions(self):
        versions = []
        for v in os.listdir(self._parent.path):
            if bool(self.match_pattern(v)):
                versions.append(self.__float_version_from_str(v))
            else:
                if os.path.isfile(os.path.join(self._parent.path, v)):
                    file_name, ext = os.path.splitext(v)
                    if bool(self.match_pattern(file_name)):
                        versions.append(self.__float_version_from_str(file_name))
        return versions

    def __get_format_args(self):
        shot_inst = getattr(self._parent, "shot")
        if shot_inst.__class__.__name__ == "Shot":
            shot = shot_inst.name
            reel = shot_inst.reel.name
            project = shot_inst.project.name
        else:
            shot = reel = project = ""
        parent_type = getattr(self._parent, "type") or ""
        return {
            "shot": shot,
            "reel": reel,
            "project": project,
            "parent_type": parent_type,
            "parent_name": self._parent.name,
            "suffix": self.suffix
        }

    @property
    def _regex(self):
        version_regex = "^{}".format(self._pattern)

        filename_format = "^" + self.__valid_filename_format(with_extension=False)
        filename_regex = filename_format.format(
            version=self._pattern,
            **self.__get_format_args()
        )
        return "{}|{}".format(version_regex, filename_regex)

    @property
    def suffix(self):
        return self._suffix

    @property
    def thumbnail(self):
        if not self._thumbnail:
            path = os.path.join(self._parent.path,".thumbnail")
            file_name = "{}_{}.png".format(self._parent.name, self.version)
            self._thumbnail = os.path.join(path, file_name)

        return self._thumbnail

    @property
    def info(self):
        return {
            "version": self._version,
            "type": self._type,
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
    def version(self):
        return self._version

    @property
    def filepaths(self):
        return self._filepaths

    @property
    def local_filepaths(self):
        return [path.replace(self.path, self._local_path) for path in self._filepaths]

    @classmethod
    def get_version_instance(cls, parent, version):
        parent_ins = cls._instances.get(parent)
        if parent_ins and version in parent_ins.keys():
            return parent_ins[version]
        else:
            return cls(parent, version)



