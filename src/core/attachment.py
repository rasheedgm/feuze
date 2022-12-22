

class Attachment(object):
    """Attachment is anything attached with shot or media. either dependencies or anything such"""
    _base_name = "attachment"

    def __init__(self, recipient):
        super(Attachment, self).__init__()

        if not hasattr(recipient, "update_info") or not hasattr(recipient, "get_info"):
            raise Exception("Recipient is not valid")

        self.__recipient = recipient

    def attach(self, attachment):
        pass
        # TODO working here

    def fetch(self):
        return []

