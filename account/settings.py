import os

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()

env_path = env.str('ENV_PATH', default=os.path.join(BASE_DIR, '.env'))
environ.Env.read_env(env_file=env_path)

TRAKT_CLIENT = env.str('TRAKT_CLIENT')
TRAKT_SECRET = env.str('TRAKT_SECRET')
