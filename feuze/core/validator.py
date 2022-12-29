from feuze.core.attachment import Attachment, AttachmentManager
from feuze.core.media import MediaFactory


class BaseValidator(object):

    def __init__(self, **kwargs):
        super(BaseValidator, self).__init__()


    def __call__(self, *args, **kwargs):
        NotImplementedError("Not implemented")

    def __bool__(self):
        return True if self.__call__() else False


class HasMediaAttached(BaseValidator):

    def __init__(self, media_type, name=None, **kwargs):
        super(HasMediaAttached, self).__init__(**kwargs)
        if MediaFactory.is_media(media_type):
            self.media_type = media_type
        else:
            self.media_type = MediaFactory.get_type(media_type)

        if name:
            self.name = name

    def __call__(self, fold):
        attachment = AttachmentManager(fold)
        # TODO need this validator running
        for att in attachment.fetch():
            pass
        return True


