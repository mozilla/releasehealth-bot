There are unfortunately no automated tests for releasehealth-bot, but
there is a very simple test server that acts like a Bugzilla
instance.  It requires flask (`pip install flask`) and a local
JSON-encoded file, `query_values.json`, that contains fake data.  The
file is loaded fresh on every query, so you can change the values to
prompt a test releasehealth-bot to issue updates.  An example file,
`query_values.json.example`, is included, though the versions will have
to be updated to match what is in the releasehealth dashboard's
`bzconfig.json`.

It may be useful to run a local version of the releasehealth dashboard
as well.
