import re
from typing import Optional, Tuple

GUID_RE = re.compile(r'^(?:[^.]+\.)?([^.]*)://([^\\?]*).*$', re.IGNORECASE | re.MULTILINE)


def parse_media_guid(guid: str) -> Optional[Tuple[str, str]]:
    match = GUID_RE.match(guid)
    if not match:
        return None

    media_key = match.group(1)
    media_id = match.group(2)
    return media_key, media_id
