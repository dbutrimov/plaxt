from typing import List

from .TraktHistoryEpisode import TraktHistoryEpisode


class TraktHistorySeason(object):
    def __init__(self, number: int = None):
        self.number = number
        self.episodes: List[TraktHistoryEpisode] = list()

    def to_dict(self):
        return {
            'number': self.number,
            'episodes': [episode.to_dict() for episode in self.episodes],
        }

    __dict__ = to_dict

    def to_json(self):
        return {
            'number': self.number,
            'episodes': [episode.to_json() for episode in self.episodes],
        }
