from datetime import datetime

from .media import Media


class Episode(Media):
    TYPE = 'episode'

    ids: dict[str, str]
    title: str
    number: int
    watched_at: datetime

    def __init__(self, **kwargs):
        super().__init__(Episode.TYPE, **kwargs)

    def __str__(self):
        return f'e{self.number:02}'

    def to_dict(self):
        return {
            'type': self.type,
            'ids': self.ids,
            'title': self.title,
            'number': self.number,
            'watched_at': self.watched_at,
        }

    __dict__ = to_dict
