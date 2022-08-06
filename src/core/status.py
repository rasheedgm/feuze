from datetime import datetime

from feuze.core import configs
from enum import Enum, EnumMeta


class __EnumMeta(EnumMeta):

    def __contains__(self, item):
        try:
            self(item)
        except ValueError:
            return False
        else:
            return True


class __BaseStatus(Enum, metaclass=__EnumMeta):

    def __new__(cls, item, *args, **kwargs):
        status = object.__new__(cls)
        status._status = item["status"]
        status._color = item["color"]
        status._full_name = item["full_name"]
        status._short_name = item["short_name"]
        status._date = None
        return status

    def __str__(self):
        return self._full_name

    @property
    def status(self):
        return self._status

    @property
    def color(self):
        return self._color

    @property
    def short_name(self):
        return self._short_name

    @property
    def full_name(self):
        return self._full_name


TaskStatus = __BaseStatus("TaskStatus", [(i["status"], i) for i in configs.GlobalConfig.task_statuses])

ShotStatus = __BaseStatus("ShotStatus", [(i["status"], i) for i in configs.GlobalConfig.shot_statuses])


class StatusManager(object):

    def __init__(self, entity):
        super(StatusManager, self).__init__()

        if entity.__class__.__name__ == "Shot":
            self.status_class = ShotStatus
            self.status_config = configs.GlobalConfig.shot_statuses
        elif entity.__class__.__name__ == "Task":
            self.status_class = TaskStatus
            self.status_config = configs.GlobalConfig.task_statuses
        else:
            raise Exception("Status can only be updated on Task or Shot")

        self.__entity = entity

    @property
    def entity(self):
        return self.__entity

    def get_all_status(self):
        return [(self.from_string(s["status"]), s["date"]) for s in self.entity.get_info("status")]

    def get_current_status(self):
        status = self.entity.get_info("status")
        if status:
            recent_status = status[-1]
            return self.from_string(recent_status["status"])

    def set_status(self, status):
        current_status = self.entity.get_info("status") or []
        if status in (c["status"] for c in current_status):
            return None

        if status not in self.status_class:
            status = self.from_string(status)

        current_status.append({
            "status": status.status,
            "date": datetime.now()
        })

        self.entity.update_info(status=current_status)

    def exists(self, status):
        return str(status) in [s["status"] for s in self.entity.get_info("status")]

    def from_string(self, status):
        if not isinstance(status, str):
            raise ValueError("Status is not string")

        status_config = next((s for s in self.status_config
                              if status in (s["status"], s["full_name"], s["short_name"])), None)
        if status_config:
            return self.status_class(status_config)
        else:
            raise Exception("Status is not valid")


def get_shot_status(shot):
    manager = StatusManager(shot)
    return manager.get_current_status()


def get_task_status(task):
    manager = StatusManager(task)
    return manager.get_current_status()
