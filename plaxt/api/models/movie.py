from datetime import datetime

from .media import Media


class Movie(Media):
    TYPE = 'movie'

    ids: dict[str, str]
    title: str
    year: int
    watched_at: datetime

    def __init__(self, **kwargs):
        super().__init__(Movie.TYPE, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.year})"

    def to_dict(self):
        return {
            'type': self.type,
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
            'watched_at': self.watched_at,
        }

    __dict__ = to_dict
