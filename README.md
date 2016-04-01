releasehealth-bot is an IRC bot that polls Bugzilla for changes in the
number of bugs returned for select queries.  These queries are fetched
from the [releasehealth dashboard][] to eliminate redundancy.

It uses Redis to store historical data.  That data could also
conceivably be used to plot trends.

releasehealth-bot is configured entirely via environment variables.
See `releasehealth/config.py` for a documented list of options.
Several are mandatory; others have more-or-less sensible defaults.

To install, preferably create and activate a virtualenv, then run
`pip install -r requirements.txt`.

To run, set your required environment variables, and then launch
`python releasehealth-bot.py`.

[releasehealth dashboard]: https://github.com/mozilla/releasehealth
