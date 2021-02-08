import os

from environ import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Read environment variables
ENV = environ.Env()

env_file = ENV.str('ENV_FILE', default=os.path.join(BASE_DIR, '.env'))
environ.Env.read_env(env_file=env_file)
