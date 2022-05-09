from datetime import datetime
from typing import List, Optional, Any

from api.models import Media


class Adapter:
    def fetch(self, min_date: datetime = None, items_limit: int = 1000) -> Optional[List[Media]]:
        pass

    def push(self, items: List[Media]) -> Optional[Any]:
        pass
