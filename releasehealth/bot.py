# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import ssl
import threading
import time

import irc.client

from . import config
from .stats import Stats


class Bot(irc.client.SimpleIRCClient):

    def __init__(self):
        irc.client.SimpleIRCClient.__init__(self)
        # TODO: Monitor changes to version definition (we do this in a limited
        # way in stats_changed(), but only if we have never had data for
        # a particular version.  This won't catch when a version is promoted,
        # e.g. from Nightly to Developer Edition).
        self.stats = Stats(stats_callback=self.stats_callback)
        self.stats_thread = None
        self.last_bzconfig_refresh = None

    def connect(self):
        logging.info('Joining %s:%s with nick %s%s.' % (
            config.IRC_SERVER,
            config.IRC_PORT,
            config.IRC_NICKNAME,
            ' (SSL)' if config.IRC_SSL else ''
        ))

        if config.IRC_SSL:
            factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        else:
            factory = irc.connection.Factory()

        irc.client.SimpleIRCClient.connect(
            self,
            config.IRC_SERVER,
            config.IRC_PORT,
            config.IRC_NICKNAME,
            connect_factory=factory
        )

    def stats_changed(self, vernum, vername, query, old_value, new_value):
        if old_value is None:
            msg = 'New metric: %s %s %s: %d' % (vername, vernum, query,
                                                new_value)
        else:
            action = 'increased' if old_value < new_value else 'decreased'
            msg = '%s %s %s %s from %d to %d.' % (
                vername, vernum, query, action, old_value, new_value)
        for channel in config.IRC_CHANNELS:
            channel_name = channel.split(':')[0]
            self.connection.privmsg(channel_name, msg)

    def poll_stats_loop(self):
        while True:
            now = time.time()
            if (not self.last_bzconfig_refresh or
                (now - self.last_bzconfig_refresh >=
                 config.BZCONFIG_REFRESH_PERIOD)):
                logging.info('Refreshing bzconfig.')
                self.stats.refresh_bzconfig()
                logging.info('bzconfig refresh complete.')
                self.last_bzconfig_refresh = now

            self.stats.refresh_stats()
            time.sleep(config.STATS_REFRESH_PERIOD)

    def on_welcome(self, connection, event):
        # TODO: Log errors when joining channels.
        logging.info('Connected!')

        if config.NICKSERV_PASSWORD:
            self.connection.privmsg('NickServ',
                                    'identify %s' % config.NICKSERV_PASSWORD)

        for channel in config.IRC_CHANNELS:
            channel_name, _, key = channel.partition(':')
            connection.join(channel_name, key)

        self.stats_thread = threading.Thread(target=self.poll_stats_loop)
        self.stats_thread.daemon = True
        self.stats_thread.start()

    def on_disconnect(self, connection, event):
        # TODO: Retry, with an exponential backoff timer.
        logging.warn('Disconnected! %s' % event)
        raise SystemExit()

    def stats_callback(self, *args):
        self.reactor.execute_delayed(0, self.stats_changed, args)
