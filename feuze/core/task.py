import datetime
import inspect
import os
import re

from feuze.core import configs
from feuze.core.fold import BaseFold, Shot
from feuze.core.user import User, current_auth
from feuze.core.version import TaskVersion
from feuze.core import validator

from feuze.core.constant import VERSION_PATTERN


"""
  - Task should be committed before setting status.
  - Some status can be set without commit
  - committing should be validated, or setting status should be validated
    - a task committing means a version locking. this can be done with validation example a comp task can be 
      committed if output path is attached with task.
    - above is conflicting when a task goes for review. now as task is already committed may be we can move
      for review as its but review might require dailies(or any other supporting files) so it wil better validation
      to run on setting status.
  - if validating on setting status, there are challenge some task types status may required different attachment.
  - validation can be ignored in that case, but atleast can keep for cmmiting of task.
  - only committed task can be set status.
    
"""

# TODO versions need commit option which is locking a version
#  while committing there should be one validation
#  the validation will validate if version has required attributes set as task type needed


class TaskTypes(object):
    __ALL_TYPES = configs.GlobalConfig.all_task_types

    def __init__(self, name):
        f_type = self.__ALL_TYPES.get(name)
        if not f_type:
            raise Exception("Task type is not configured")
        self.name = name
        self.short_name = f_type["short_name"]
        self.sub_dir = f_type["sub_dir"]
        self.task_names = f_type["task_names"]
        validators = {k: v for k, v in inspect.getmembers(validator, lambda x: callable(x) )}
        self.validators = [validators[v.get("name")](*v["args"], **v["kwargs"]) for v in f_type["validators"]]

    def __str__(self):
        return self.name


    @classmethod
    def get_all(cls):
        return [cls(t) for t in cls.__ALL_TYPES]


class Task(BaseFold):

    def __init__(self, shot: Shot, name, task_type):
        task_type = task_type if isinstance(task_type, TaskTypes) else TaskTypes(task_type)
        if name not in task_type.task_names:
            raise Exception("Name is not configured in task config")
        sub_dir = task_type.sub_dir
        path = os.path.join(shot.path, sub_dir, name)
        super(Task, self).__init__(name, path)
        self._type = task_type
        self._shot = shot

    def update_info(self, **kwargs):
        if kwargs.get("status"):
            latest = self.latest()
            if not latest.committed:
                raise Exception("Latest version({0}) is not committed".format(latest))
            status_dict = kwargs.get("status").pop()
            print(status_dict)
            status_dict["version"] = latest.version
            kwargs["status"].append(status_dict)
        super(Task, self).update_info(**kwargs)

    def assign(self, user, comment=None):  # TODO
        """assign the task to one use"""

        auth = current_auth()
        if not auth or "task_assign" not in auth.user.role.permissions:
            raise Exception("You are not authorized to assign")

        if isinstance(user, str):
            user = User(user)

        if not isinstance(user, User):
            raise Exception("Valid user is required")

        if not user.exists():
            raise Exception("User does not exists")

        if self.get_info("assignment"):
            raise Exception("Task is already assigned.")

        comment = comment or ""

        assignment = [
            {
                "date": datetime.datetime.now(),
                "user": user.name,
                "comment": comment
            }
        ]

        self.update_info(assignment=assignment)

    def reassign(self, user, comment=None): # TODO
        """reasign to another """

        auth = current_auth()
        if not auth or not auth.role.has("task_assign"):
            raise Exception("You are not authorized to assign")

        if isinstance(user, str):
            user = User(user)

        if not isinstance(user, User):
            raise Exception("Valid user is required")

        if not user.exists():
            raise Exception("User does not exists")

        comment = comment or ""
        assignment = self.get_info("assignment")

        # TODO check if latest assignment is on same user, if its same do nothing.


        assignment.append({
                "date": datetime.datetime.now(),
                "user": user.name,
                "comment": comment
            })

        self.update_info(assignment=assignment)

    def start(self): # TODO
        """Start the task"""
        # record date started
        # set info to stated or in progress
        pass

    def stop(self): # TODO
        """Start the task"""
        # record date started
        # set info to stated or in progress
        pass

    def hold(self): # TODO
        """hoold the task"""
        pass

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
        return self.version(None)

    def latest(self):
        return self.version("latest")

    def version(self, version):
        return Version(self, version)

    def get_assignments(self, latest=False, user=None):
        assignments = sorted(self.get_info("assignment"), key=lambda x: x["date"], reverse=True)

        if user:
            assignments = [asgn for asgn in assignments if asgn.get("user") == user]

        if not assignments:
            return None

        if latest:
            return assignments[0]
        else:
            return assignments

    def get_versions(self):
        for version in TaskVersion(self).get_all_versions():
            yield self.version(version)

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
    def get_all_tasks_in_shot(cls, shot):
        tasks = []
        for _type in TaskTypes.get_all():
            path = os.path.join(shot.path, _type.sub_dir)
            if os.path.exists(path):
                # TODO make utils method to get list of directories
                tasks += [cls(shot, name, _type.name) for name in os.listdir(path)
                             if os.path.isdir(os.path.join(path, name))]
        return tasks


class Version(object):
    _instances = {}
    _format = "v{version:0>2}"

    def __init__(self, task: Task, version=None):
        super(Version, self).__init__()
        self._task = task
        self._created_at = None
        self._created_by = None
        self._thumbnail = None  # TODO need to work
        self._modified_at = None
        self._committed = None
        self._comment = None
        if version not in (None, "latest"):
            self._version = self.get_version_int(version)
        else:
            self._version = version
        versions_info = self._task.info.get("versions", {})
        info = versions_info.get(self.version)
        if info:
            self.set_attributes_from_info(info)
        else:
            if versions_info:
                latest = max([self.get_version_int(k) for k in versions_info.keys()])
                if self._version is None:
                    self._version = latest + 1
                    self.set_attributes()
                elif self._version == "latest":
                    self._version = latest
                    self.set_attributes_from_info(versions_info.get(self.version))
            else:
                self._version = 1
                self.set_attributes()



    def set_attributes(self):
        self._committed = False
        pass #TODO set attribute

    def set_attributes_from_info(self, info):
        self._committed = info.get("committed", False)
        self._created_by = info.get("created_by")
        self._created_at = info.get("created_at")
        self._modified_at = info.get("modified_at")
        self._comment = info.get("comment", "")
        pass #TODO set attribute

    def get_version_int(self, version=None):
        if version is None:
            version = self.version
        if version:
            if isinstance(version, int):
                return version
            if isinstance(version, float):
                if version.is_integer():
                    return int(version)
                else:
                    splits = str(version).split(".")
                    return int(splits[0])
            if version.isdigit():
                return int(version)

            match = self.version_pattern.match(version)
            if bool(match):
                return int(match.group("version"))

        return None

    def create(self, **kwargs):
        # TODO who can created task
        exists = self.exists()
        if exists:
            return None

        self.task.create()

        self._created_at = datetime.datetime.now()
        self._created_by = current_auth().user.name

        self.update_info(**kwargs)

    def new(self):
        versions_info = self._task.get_info("versions")
        latest = max([self.get_version_int(k) for k in versions_info.keys()])
        return latest + 1

    def exists(self):
        versions_info = self._task.get_info("versions")
        if versions_info:
            return versions_info.get(self.version) is not None
        return False

    def update_info(self, **kwargs):

        self_info = {
            "created_by": self._created_by,
            "created_at": self._created_at,
            "modified_at": datetime.datetime.now(),
        }

        self_info.update(kwargs)
        versions_info = self.task.info.get("versions", {})
        versions_info.update({self.version: self_info})
        self.task.update_info(versions=versions_info)

    def get_info(self, key):
        return self.info.get(key)

    def commit(self, comment):
        """commit this version
        """
        if not self.exists():
            raise Exception("Task version does not exits, Please create version first.")

        if self.committed:
            raise Exception("Task version is already committed!")

        for validator in self.task.type.validators:
            validator(self)

        self.update_info(committed=True, comment=comment)

        return True
        # TODO commit this version
        # - validate before commit
        # config validation
        # more to plan


    @property
    def info(self):
        return self.task.info.get("versions", {}).get(self.version, {})

    @property
    def crumbs(self):
        return self.task.crumbs + "/{}".format(self.version)

    @property
    def committed(self):
        return self._committed

    @property
    def version(self):
        return self._format.format(version=self._version)

    @property
    def version_pattern(self):
        pattern = self._format.format(version="])?(?P<version>[0-9]+)")
        pattern = "^([" + pattern + "$"
        c_pattern = re.compile(pattern)
        return c_pattern

    @property
    def thumbnail(self):
        if not self._thumbnail:
            path = os.path.join(self.task.path, ".thumbnail")
            file_name = "{}_{}.png".format(self.task.name, self.version)
            self._thumbnail = os.path.join(path, file_name)

        return self._thumbnail

    @property
    def task(self):
        return self._task


def get_all_tasks(shot, filters=None):
    """returns all users
    :arg
        filter(dict|callable): dict of props to filter. or callable filter method.
    """

    for task in Task.get_all_tasks_in_shot(shot):

        if isinstance(filters, dict):
            if all([task.get_info(k) == v for k, v in filters.items()]):
                yield task
        elif callable(filters):
            if filters(task):
                yield task
        else:
            yield task


