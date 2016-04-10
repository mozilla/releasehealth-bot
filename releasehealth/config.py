import os

# Mandatory config.

# Space-separated list of channels the bot should join.  Specify password-
# protected channels with <channel>:<key>.
IRC_CHANNELS = os.environ['IRC_CHANNELS'].split()

# IRC server address.  This is a mandatory option.
IRC_SERVER = os.environ['IRC_SERVER']


# Optional config.

# URL to bzconfig.json file containing versions, queries, etc.
BZCONFIG_JSON_URL = os.environ.get(
    'BZCONFIG_JSON_URL',
    'http://mozilla.github.io/releasehealth/js/bzconfig.json'
)

# How often, in seconds, to check for an updated bzconfig.json.
BZCONFIG_REFRESH_PERIOD = int(os.environ.get('BZCONFIG_REFRESH_PERIOD', 10*60))

# 1 to enable DEBUG-level logs; 0 to enable only INFO and above.
DEBUG = bool(int(os.environ.get('DEBUG', 0)))

# Nickname for the bot to use.
IRC_NICKNAME = os.environ.get('IRC_NICKNAME', 'releasehealth')

# IRC server port.
IRC_PORT = int(os.environ.get('IRC_PORT', 6667))

# 1 to enable SSL; 0 to disable SSL.
IRC_SSL = bool(int(os.environ.get('IRC_SSL', 0)))

# URL for Redis server, used to store stats.
REDIS_URL = os.environ.get('REDIS_URL', 'http://localhost:6379')

# How often, in seconds, to query Bugzilla.
STATS_REFRESH_PERIOD = int(os.environ.get('STATS_REFRESH_PERIOD', 5*60))

# Password to send to NickServ upon connection.
NICKSERV_PASSWORD = os.environ.get('NICKSERV_PASSWORD')
