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
        return self._bzconfig

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
