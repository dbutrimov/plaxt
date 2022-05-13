from .media import Media
from .season import Season


class Show(Media):
    TYPE = 'show'

    ids: dict[str, str]
    title: str
    year: int
    seasons: list[Season] = None

    def __init__(self, **kwargs):
        super().__init__(Show.TYPE, **kwargs)
        if not self.seasons:
            self.seasons = list()

    def __str__(self):
        return f"{self.title} ({self.year})"

    def to_dict(self):
        return {
            'type': self.type,
            'ids': self.ids,
            'title': self.title,
            'year': self.year,
            'seasons': [season.to_dict() for season in self.seasons],
        }

    __dict__ = to_dict
