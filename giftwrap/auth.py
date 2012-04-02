from .config import Config

# all use of exchanges will require a passing of an auth class -- this will likely be overridden in implementing any real wrapper
# TODO: add examples of overriding
class Auth(Config): pass

