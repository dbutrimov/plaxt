from datetime import datetime

from . import Media, Show


class Episode(Media):
    TYPE = 'episode'

    def __init__(self,
                 ids: dict = None,
                 title: str = None,
                 season: int = None,
                 number: int = None,
                 watched_at: datetime = None,
                 show: Show = None):
        super().__init__(Episode.TYPE)

        self.ids = ids
        self.title = title
        self.season = season
        self.number = number
        self.watched_at = watched_at
        self.show = show

    def to_dict(self):
        return {
            'type': self.type,
            'ids': self.ids,
            'title': self.title,
            'season': self.season,
            'number': self.number,
            'watched_at': self.watched_at,
            'show': self.show.to_dict(),
        }

    __dict__ = to_dict
