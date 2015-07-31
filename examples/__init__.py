#
# Copyright 2015 Ross Hendrickson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Simple examples to show how the log functions in a distributed environment
using GAE task queues.
"""

import webapp2

from furious.handlers.webapp import AsyncJobHandler

from .simple_writes import SimpleWritesHandler

config = {
    'webapp2_extras.jinja2': {
        'template_path': 'example/templates'
    }
}

app = webapp2.WSGIApplication([
    ('/_queue/async.*', AsyncJobHandler),
    ('/', SimpleWritesHandler)
], config=config)
