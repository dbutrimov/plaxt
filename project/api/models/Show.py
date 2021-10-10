from . import Media


class Show(Media):
    TYPE = 'show'

    def __init__(self,
                 ids: dict = None,
                 title: str = None,
                 year: int = None):
        super().__init__(Show.TYPE)

        self.ids = ids
        self.title = title
        self.year = year

    def to_dict(self):
        return {
            'type': self.type,
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
        }

    __dict__ = to_dict
