from typing import List

from .TraktHistorySeason import TraktHistorySeason


class TraktHistoryShow(object):
    def __init__(self,
                 ids: dict = None,
                 title: str = None,
                 year: int = None):
        self.ids = ids
        self.title = title
        self.year = year
        self.seasons: List[TraktHistorySeason] = list()

    def to_dict(self):
        return {
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
            'seasons': [season.to_dict() for season in self.seasons],
        }

    __dict__ = to_dict

    def to_json(self):
        return {
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
            'seasons': [season.to_json() for season in self.seasons],
        }
