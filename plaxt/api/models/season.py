from .media import Media
from .episode import Episode


class Season(Media):
    TYPE = 'season'

    number: int
    episodes: list[Episode] = None

    def __init__(self, **kwargs):
        super().__init__(Season.TYPE, **kwargs)
        if not self.episodes:
            self.episodes = list()

    def __str__(self):
        return f's{self.number:02}'

    def to_dict(self):
        return {
            'type': self.type,
            'number': self.number,
            'episodes': [episode.to_dict() for episode in self.episodes],
        }

    __dict__ = to_dict
