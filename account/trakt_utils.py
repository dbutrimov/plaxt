import re


def parse_media_id(guid: str):
    match = re.match(r'^.*\.([^.]*)://([^\\?]*).*$', guid, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None

    media_key = match.group(1)
    if media_key.startswith('the'):
        media_key = media_key[3:]

    media_id = match.group(2)

    return media_key, media_id


def find_ids(metadata, key='guid'):
    guid = metadata.get(key)
    if not guid:
        return None

    media_key, media_id = parse_media_id(guid)
    if not media_key or not media_id:
        return None

    return {
        media_key: media_id,
    }


def find_movie(metadata):
    media_type = metadata.get('type')
    if media_type != 'movie':
        return None

    return {
        'title': metadata['title'],
        'year': metadata['year'],
        'ids': find_ids(metadata),
    }


def find_show(metadata):
    media_type = metadata.get('type')

    if media_type == 'show':
        return {
            'title': metadata['title'],
            'year': metadata['year'],
            'ids': find_ids(metadata),
        }

    if media_type == 'season':
        return {
            'title': metadata['parentTitle'],
            'ids': find_ids(metadata, key='parentGuid'),
        }

    if media_type == 'episode':
        return {
            'title': metadata['grandparentTitle'],
            'ids': find_ids(metadata, key='grandparentGuid'),
        }

    return None


def find_season(metadata):
    media_type = metadata.get('type')

    if media_type == 'season':
        return {
            'title': metadata['title'],
            'season': metadata['index'],
            'ids': find_ids(metadata),
        }

    if media_type == 'episode':
        return {
            'title': metadata['parentTitle'],
            'season': metadata['parentIndex'],
            'ids': find_ids(metadata, key='parentGuid'),
        }

    return None


def find_episode(metadata):
    media_type = metadata.get('type')
    if media_type != 'episode':
        return None

    return {
        'season': metadata['parentIndex'],
        'number': metadata['index'],
        'title': metadata['title'],
        'year': metadata['year'],
        'ids': find_ids(metadata),
    }
