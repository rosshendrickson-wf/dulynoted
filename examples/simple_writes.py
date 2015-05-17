#
# Copyright 2014 Ross Hendrickson
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
    Example of using Logs to quickly create revisioned data.

    The whole goal of the log is to allow you to have a single process generate
    a series of writes to another entity that are linearized in the context of
    that original process. In async behavior this will end up with last man
    wins style behavior
"""


import logging

import webapp2

from dulynoted import Log

class SimpleWritesHandler(webapp2.RequestHandler):
    """Demonstrate writing the a simple log using Furious Async tasks."""
    def get(self):
        from furious.async import Async
        from furious import context

        count = int(self.request.get('tasks', 5))

        # Create a new furious Context.
        with context.new() as ctx:

            # Set a completion event handler.
            log = Log()
            log.put()
            ctx.set_event_handler('complete',
                                  Async(context_complete, args=[ctx.id, log.key.id()]))

            # Insert some Asyncs.
            for i in xrange(count):
                queue = 'a-worker-1'

                if i % 2 == 0:
                    queue = 'z-worker-2'

                ctx.add(
                    target=async_worker, queue=queue,
                    args=[ctx.id, i, log.key.id()])
                logging.info('Added job %d to context.', i)

        # When the Context is exited, the tasks are inserted (if there are no
        # errors).
        logging.info('Async jobs for context batch inserted.')
        message = "Successfully inserted a group of %s Async jobs." % str(count)
        self.response.out.write(message)


def async_worker(*args, **kwargs):
    log = Log.get_by_id(args[2])
    log.new_commit(args[1])
    return args

def calculate_rate(log):

    delta = log.created - log.updated

    if log.latest_revision == 0:
        return 0

    return delta.microseconds / log.latest_revision

def context_complete(context_id, log_id):
    """Log out that the context is complete."""
    logging.info('Context %s is.......... DONE.', context_id)
    log = Log.get_by_id(log_id)
    logging.info('Log Revision %s', log.latest_revision)
    rate = calculate_rate(log)
    logging.info('rate %s microseconds per revision', rate)
    if rate != 0:
        seconds = 1000000 / rate
        logging.info('%s revisions per second', seconds)
    commits = len(log.commits)
    logging.info('%s commits in the log', commits)
    for commit in log.commits:
        logging.info("commit revision %s:%s", commit.revision, commit.created)
    revisions = len(log.revisions)
    logging.info('revisions %s', revisions)
    revisions = log.commit_range(1, 3)

    shards = log.revision_shards
    logging.info("Had %s revision shards", len(shards))
    for shard in shards:
        logging.info("Shard for rev %s", shard.revision)
        for commit in shard.commits:
            logging.info("Sharded Commit %s:%s", commit.revision, commit.created)


    for commit in revisions:
        logging.info("commit revision %s:%s", commit.revision, commit.created)

    return context_id
