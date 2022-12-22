"""A Badge is extra tag added to any item, which has info stored, Basic I dea here is this can be used
to Read/Add a particular piece of info from info file ad any items. For example a Media version can
have tag called approved, which can be used as approved version of media.
>>> from feuze.core.fold import Shot
>>> from feuze.core.media import MediaFactory
>>> shot = Shot(project="PROJ1", reel="REEL01", name="SHOT001")
>>> plate_media = MediaFactory(shot, "FinalRender", "Render")
>>> plate_media_version = plate_media.version("latest")
>>> badge_manager = BadgeManager(plate_media_version)
>>> badge_manager.add("approved", "user")
>>> badge_manager.fetch()
"""
from datetime import datetime

from feuze.core.user import Auth


class Badge(object):
    """Badge class"""

    def __init__(self, name, date, user, removed_date=None):
        super(Badge, self).__init__()
        self._name = name
        if not isinstance(date, datetime):
            raise Exception("Date has to be {}".format(datetime))
        if removed_date and not isinstance(removed_date, datetime):
            raise Exception("Removed has to be {}".format(datetime))

        self._date = date
        self._user = user
        self._removed_date = removed_date

    @property
    def name(self):
        return self._name

    @property
    def date(self):
        return self._date

    @property
    def user(self):
        return self._user

    @property
    def state(self):
        return int(not self._removed_date)

    @property
    def removed_date(self):
        return self._removed_date

    def to_dict(self):
        return {
            "name": self.name,
            "date": self.date,
            "user": self.user,
            "removed_date": self.removed_date
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data.get("name"),
            datetime.fromisoformat(data.get("date")) if isinstance(data.get("date"), str) else data.get("date"),
            data.get("user"),
            datetime.fromisoformat(data.get("removed_date")) if data.get("removed_date") else ""
        )


class BadgeManager(object):
    _badge_key = "badge"

    def __init__(self, recipient):
        super(BadgeManager, self).__init__()
        if not hasattr(recipient, "update_info") or not hasattr(recipient, "get_info"):
            raise Exception("Recipient is not valid")

        self.__recipient = recipient

    def fetch(self, removed=False):
        badges_data = self.recipient.get_info(BadgeManager._badge_key)
        if badges_data:
            return [Badge.from_dict(data) for data in badges_data if not data.get("removed_date") or removed]
        else:
            return []

    def add(self, name, user):
        if self.has_badge(name):
            raise Exception("Badge is already awarded")

        current = self.__recipient.get_info(BadgeManager._badge_key) or []
        current.append({
            "name": name,
            "date": datetime.now(),
            "user": user,
            "removed_date": ""
        })
        _kwarg = {BadgeManager._badge_key: current}
        self.__recipient.update_info(**_kwarg)

    def remove(self, name):
        if not self.has_badge(name):
            return None
        current = self.__recipient.get_info(BadgeManager._badge_key) or []
        for i in range(len(current), 0, -1):
            index = i - 1
            if current[index]["name"] == name and not current[index]["removed_date"]:
                current[index]["removed_date"] = datetime.now()
                break

        _kwarg = {BadgeManager._badge_key: current}
        self.__recipient.update_info(**_kwarg)

    def has_badge(self, name):
        return any([b.name == name for b in self.fetch()])

    @property
    def recipient(self):
        return self.__recipient
