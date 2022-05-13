class Media(object):
    def __init__(self, media_type: str = None, **kwargs):
        self.type = media_type
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        pass
