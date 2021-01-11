import os

from environ import Env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Env()

env_file = env.str('ENV_FILE', default=os.path.join(BASE_DIR, '.env'))
if os.path.isfile(env_file):
    Env.read_env(env_file=env_file)  # reading .env file

TRAKT_CLIENT = env.str('TRAKT_CLIENT')
TRAKT_SECRET = env.str('TRAKT_SECRET')

PLEX_URL = env.str('PLEX_URL')
PLEX_TOKEN = env.str('PLEX_TOKEN')
