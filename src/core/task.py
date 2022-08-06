from datetime import datetime
import os
import re

from feuze.core import configs
from feuze.core.fold import BaseFold, Shot
from feuze.core.user import User, current_auth
from feuze.core.version import TaskVersion


class TaskTypes(object):
    __ALL_TYPES = configs.GlobalConfig.all_task_types

    def __init__(self, name):
        f_type = self.__ALL_TYPES.get(name)
        if not f_type:
            raise Exception("Task type is not configured")
        self.name = f_type["name"]
        self.short_name = f_type["short_name"]
        self.sub_dir = f_type["sub_dir"]
        self.task_names = f_type["task_names"]

    def __str__(self):
        return self.name


    @classmethod
    def get_all(cls):
        return [cls(t) for t in cls.__ALL_TYPES]


class Task(BaseFold):

    def __init__(self, shot: Shot, name, task_type):
        task_type = task_type if isinstance(task_type, TaskTypes) else TaskTypes(task_type)
        sub_dir = task_type.sub_dir
        name = task_type.name
        path = os.path.join(shot.path, sub_dir, name)
        super(Task, self).__init__(name, path)
        self._type = task_type
        self._shot = shot

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
                "date": datetime.now(),
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
                "date": datetime.now(),
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
        return TaskVersion(self)

    def latest(self):
        version = TaskVersion(self, version=1.0)
        if os.path.exists(self.path):
            versions = version.get_all_versions()
            if versions:
                version = max(versions)

        return self.version(version)

    def version(self, version):
        version = TaskVersion.formatted_version(version)
        return TaskVersion.get_version_instance(self, version)

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


