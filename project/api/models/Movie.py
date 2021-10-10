from datetime import datetime

from . import Media


class Movie(Media):
    TYPE = 'movie'

    def __init__(self,
                 ids: dict = None,
                 title: str = None,
                 year: int = None,
                 watched_at: datetime = None):
        super().__init__(Movie.TYPE)

        self.ids = ids
        self.title = title
        self.year = year
        self.watched_at = watched_at

    def to_dict(self):
        return {
            'type': self.type,
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
            'watched_at': self.watched_at,
        }

    __dict__ = to_dict
