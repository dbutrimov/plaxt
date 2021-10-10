from typing import List, Optional

from api.models import Media


class Adapter:
    def fetch(self) -> Optional[List[Media]]:
        pass

    def push(self, items: List[Media]):
        pass
