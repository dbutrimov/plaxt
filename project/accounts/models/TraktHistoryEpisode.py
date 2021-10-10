from datetime import datetime


class TraktHistoryEpisode(object):
    def __init__(self, number: int = None, watched_at: datetime = None):
        self.number = number
        self.watched_at = watched_at

    def to_dict(self):
        return {
            'number': self.number,
            'watched_at': self.watched_at,
        }

    __dict__ = to_dict

    def to_json(self):
        return {
            'number': self.number,
            'watched_at': self.watched_at.isoformat(),
        }
