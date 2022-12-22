from feuze.core.attachment import Attachment

class BaseValidator(object):

    def __init__(self, **kwargs):
        super(BaseValidator, self).__init__()


    def __call__(self, *args, **kwargs):
        NotImplementedError("Not implemented")

    def __bool__(self):
        return True if self.__call__() else False


class HasMediaAttached(BaseValidator):

    def __int__(self,obj,media_type, **kwargs):
        super(MediaValidator, self).__int__(**kwargs)
        self.obj = obj
        self.media_type = media_type

    def __call__(self, *args, **kwargs):
        attatchment = Attachment(self.obj)
        # TODO WAS WORKING HERE


