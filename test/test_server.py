# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import re

from flask import Flask, jsonify, request
from flask.ext.cors import CORS

logging.basicConfig(level=logging.DEBUG)

cache_filename = 'query_values.json'
app = Flask(__name__)
CORS(app)


@app.route('/rest/bug')
def search():
    flag = request.args.get('f1')
    flag_re = re.match('cf_tracking_firefox(.*)', flag)

    if flag_re:
        version = flag_re.group(1)
        query = 'blocking'
    else:
        version = re.match('cf_status_firefox(.*)', flag).group(1)
        n2 = request.args.get('n2', None, type=int)
        if n2 is None:
            query = 'new'
        else:
            query = 'known'

    query_values = json.loads(file('query_values.json').read())

    return jsonify({'bug_count': query_values[version][query]})


if __name__ == '__main__':
    app.run()
