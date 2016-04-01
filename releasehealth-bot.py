# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from releasehealth import config
from releasehealth.bot import Bot


def main():
    # Requests is noisy.
    logging.getLogger("requests").setLevel(logging.WARNING)
    log_level = logging.DEBUG if config.DEBUG else logging.INFO
    logging.basicConfig(level=log_level)

    bot = Bot()

    try:
        bot.connect()
    except BaseException as e:
        print(e)
        raise SystemExit()

    bot.start()


if __name__ == '__main__':
    main()
