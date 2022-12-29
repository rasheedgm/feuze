# TODO attachment class should be stuctured, current it only has name prop.
# at present we cannot structure it bcz I cant think of use cases


class Attachment(dict):
    """Attachment is dictionary with one key name. name is primary key here
    validation comparison and attachment done based on the name. This class is just to structure the data
    saved to recipient data,
    {"name": "workfile", "path: "/path/to/workfile.ext" }
    """

    def __init__(self, name, **kwargs):
        super(Attachment, self).__init__(**kwargs)
        self.__name = name
        self["name"] = name
        for key, value in kwargs.items():
            self[key] = value

    def __setitem__(self, key, value):
        if key == "name" and value != self.name:
            raise Exception("Name cannot be changed")
        super(Attachment, self).__setitem__(key, value)

    @property
    def name(self):
        return self.__name

    @classmethod
    def from_dict(cls, _dict):
        obj = cls(name=_dict["name"])
        for key, value in _dict.items():
            obj[key] = value

        return obj

    def to_dict(self):
        return dict(self)


class AttachmentManager(object):
    """Attachment is anything attached with shot or media. either dependencies or anything such"""
    _base_name = "attachment"

    def __init__(self, recipient):
        super(AttachmentManager, self).__init__()

        if not hasattr(recipient, "update_info") or not hasattr(recipient, "get_info"):
            raise Exception("Recipient is not valid")

        self.__recipient = recipient

    def attach(self, attachment):
        if not isinstance(attachment, Attachment):
            raise Exception("Expecting Attachment type as attachment")

        if self.has_attachment(attachment):
            raise Exception("Attachment {0} already exist, use update method to update".format(attachment.name) )

        current = self.fetch()
        current[attachment.name] = attachment

        to_update = {
            self._base_name: [a.to_dict() for a in current.values()]
        }
        self.__recipient.update_info(**to_update)

    def update(self, attachment):
        if not isinstance(attachment, Attachment):
            raise Exception("Expecting Attachment type as attachment")

        current = self.fetch()
        current_att = current.get(attachment.name)
        if current_att is None:
            return Exception("attachment not found to update")
        else:
            current[attachment.name] = attachment

        to_update = {
            self._base_name: [a.to_dict() for a in current.values()]
        }
        self.__recipient.update_info(**to_update)

    def has_attachment(self, att=None):

        if att:
            if isinstance(att, Attachment):
                name = att.name
            else:
                name = att
            return True if self.fetch().get(name) is not None else False
        else:
            return len(self.fetch()) > 0

    def fetch(self):
        attachments = self.__recipient.get_info(self._base_name)
        return {att["name"]: Attachment.from_dict(att) for att in attachments} if attachments is not None else {}

    def find_one(self, attachment_name):
        return self.fetch().get(attachment_name)

