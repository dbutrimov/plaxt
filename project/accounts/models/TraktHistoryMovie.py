from datetime import datetime


class TraktHistoryMovie(object):
    def __init__(self,
                 ids: dict = None,
                 title: str = None,
                 year: int = None,
                 watched_at: datetime = None):
        self.ids = ids
        self.title = title
        self.year = year
        self.watched_at = watched_at

    def to_dict(self):
        return {
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
            'watched_at': self.watched_at,
        }

    __dict__ = to_dict

    def to_json(self):
        return {
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
            'watched_at': self.watched_at.isoformat(),
        }
