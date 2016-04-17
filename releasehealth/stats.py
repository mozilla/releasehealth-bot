# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import time

import redis
import requests

from . import config


class Stats(object):

    def __init__(self, stats_callback=None, version_callback=None):
        self.stats_callback = stats_callback
        self.version_callback = version_callback
        self._redis_client = None
        self._bzconfig = None
        self._version_names = None
        self._query_names = None

    @property
    def redis_client(self):
        if not self._redis_client:
            self._redis_client = redis.from_url(config.REDIS_URL)
        return self._redis_client

    @property
    def bzconfig(self):
        # FIXME: Automatically refresh self._bzconfig every X minutes.
        if not self._bzconfig:
            if not self.redis_client.exists('bzconfig'):
                self.refresh_bzconfig()
            self._bzconfig = {
                k: json.loads(v) for k, v in
                self.redis_client.hgetall('bzconfig').iteritems()
            }
            self._version_names = None
            self._query_names = None
        return self._bzconfig

    @property
    def version_names(self):
        if not self._version_names:
            self._version_names = {
                v['version']: v['title'] for v
                in self._bzconfig['versions'].values()
            }
        return self._version_names

    @property
    def query_names(self):
        if not self._query_names:
            self._query_names = {
                q['id']: q['title'] for q in self._bzconfig['bugQueries']
            }
        return self._query_names

    def refresh_bzconfig(self):
        """Store the releasehealth dashboard's Bugzilla config.

        We store the top-level keys separately to make it easier to notify
        apps of changes.
        """
        try:
            r = requests.get(config.BZCONFIG_JSON_URL)
        except requests.exceptions.ConnectionError as e:
            logging.error('Error fetching bzconfig from %s: %s' %
                          (config.BZCONFIG_JSON_URL, e))
            return

        if r.status_code == 200:
            cfg = r.json()
            for key, value in cfg.iteritems():
                if self.version_callback and key == 'versions':
                    old_versions = json.loads(
                        self.redis_client.hget('bzconfig', key))
                    if old_versions != value:
                        self.version_callback(old_versions, value)
                self.redis_client.hset('bzconfig', key, json.dumps(value))
            self._bzconfig = None
        else:
            logging.error('Error fetching bzconfig from %s: status %s' %
                          (config.BZCONFIG_JSON_URL, r.status_code))

    def get_stats(self, version=None, query=None):
        if version and version != '*':
            try:
                versions = [int(version)]
            except ValueError:
                versions = [self.bzconfig['versions'][version]]
        else:
            versions = [x['version'] for x
                        in self.bzconfig['versions'].values()]

        if query and query != '*':
            query = query.lower()
            queries = [
                x['id'] for x in self.bzconfig['bugQueries']
                if x['title'].replace(' ', '').lower().startswith(query)
            ]
        else:
            queries = [x['id'] for x in self.bzconfig['bugQueries']]

        results = {}

        for v in versions:
            results[v] = {}
            for q in queries:
                key = '%s:%s' % (v, q)
                try:
                    results[v][q] = json.loads(
                        self.redis_client.lindex(key, 0))[0]
                except TypeError:
                    pass

        return results

    def refresh_stats(self):
        for ver in self.bzconfig['versions'].values():
            for query in self.bzconfig['bugQueries']:
                vernum = ver['version']

                logging.debug('Polling Bugzilla: %s %s %s' %
                              (ver['title'], vernum, query['title']))

                url = self.bzconfig['BUGZILLA_REST_URL']
                url += query['url'].replace('{RELEASE}', str(vernum)) \
                                   .replace('{OLDERRELEASE}', str(vernum - 1))
                url += '&count_only=1'

                try:
                    r = requests.get(url)
                except requests.exceptions.ConnectionError as e:
                    logging.error('Error querying Bugzilla URL %s: %s' %
                                  (url, e))
                    continue

                if r.status_code != 200:
                    logging.error('Error querying Bugzilla URL %s: status %s' %
                                  (url, r.status_code))
                    continue

                key = '%s:%s' % (vernum, query['id'])
                current_bug_num = int(r.json()['bug_count'])
                last_bug_num = (None if not self.redis_client.llen(key) else
                                json.loads(self.redis_client.lindex(key, 0))[0])

                logging.debug('Results: %s -> %s' %
                              (last_bug_num, current_bug_num))

                if current_bug_num != last_bug_num:
                    logging.info('%s has changed from %s to %s.' %
                                 (key, last_bug_num, current_bug_num))
                    self.redis_client.lpush(
                        key, json.dumps((current_bug_num, time.time()))
                    )
                    if self.stats_callback:
                        self.stats_callback(vernum, ver['title'],
                                            query['title'], last_bug_num,
                                            current_bug_num)
