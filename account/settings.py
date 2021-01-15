import os

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()

env_file = env.str('ENV_FILE', default=os.path.join(BASE_DIR, '.env'))
environ.Env.read_env(env_file=env_file)

TRAKT_CLIENT = env.str('TRAKT_CLIENT')
TRAKT_SECRET = env.str('TRAKT_SECRET')
