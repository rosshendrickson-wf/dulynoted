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
import time

import webapp2

from dulynoted import Log


class SimpleWritesHandler(webapp2.RequestHandler):
    """Demonstrate writing the a simple log using Furious Async tasks."""
    def get(self):

        count = int(self.request.get('tasks', 5))

        #test_run = [10, 10, 10, 100, 100, 100, 300, 300, 300, 600, 600, 600, 1200, 1200, 1200, 2400, 2400]
        test_run = [10, 10, 10]

        log = Log()
        log.put()
        log_id = log.key.id()

        run(count, test_run, log_id)
        # When the Context is exited, the tasks are inserted (if there are no
        # errors).
        logging.info('Async jobs for context batch inserted.')
        message = "Inserted a benchmark of {} Async jobs. log_id {}".format(
            str(test_run), log_id)
        self.response.out.write(message)


def run(count, test_run, test_id):
    from furious.async import Async
    from furious import context

    # Create a new furious Context.
    with context.new() as ctx:

        # Set a completion event handler.
        log = Log()
        log.put()
        log_id = log.key.id()

        handler = Async(context_complete,
                        args=[ctx.id, log_id, time.time(), test_run, test_id, count])

        ctx.set_event_handler('complete', handler)

        # Insert some Asyncs.
        for i in xrange(count):
            queue = 'a-worker-1'

            ctx.add(
                target=async_worker, queue=queue,
                args=[ctx.id, i, log_id])

    logging.info('Added %d jobs to context.', count)


def async_worker(*args, **kwargs):
    log_id = args[2]
    log = Log.get_by_id(log_id)
    log.new_commit(args[1])
    return args


def calculate_rate(log):

    delta = log.created - log.updated
    logging.info("Total LOG test run took {} seconds".format(
        abs(delta.total_seconds())))

    if log.latest_revision == 0:
        return 0

    return abs(delta.total_seconds()) / log.latest_revision


def calculate_commit_rate(log):

    delta = log.created - log.updated

    if log.latest_revision == 0:
        return 0

    return abs(delta.total_seconds()) / len(log.commits)


def context_complete(context_id, log_id, start_time, test_run, test_id, count):
    """Log out that the context is complete."""
    logging.info('Context %s is.......... DONE.', context_id)
    complete_time = time.time()

    analysis = {}

    if len(test_run) > 0:
        count = test_run[0]
        test_run = test_run[1:]
        logging.info("Starting run for %s", count)
        run(count, test_run, test_id)

    # Current Run
    log = Log.get_by_id(log_id)
    delta = log.created - log.updated

    logging.info('Log Revision %s', log.latest_revision)
    logging.info('Total Task time: %s', start_time - complete_time)
    len_commits = len(log.commits)
    logging.info('%s commits in the log', len_commits)

    analysis['complete_time'] = complete_time - start_time
    analysis['count'] = count

    test_log = Log.get_by_id(test_id)
    if not test_log:
        logging.info("No test log for %s", test_id)
        return context_id

    test_log.new_commit(analysis)

    # Final case
    if not test_run:
        delta = test_log.created - test_log.updated
        logging.info("FINAL CALLBACK")
        logging.info("Benchmark took {} seconds".format(
            abs(delta.total_seconds())))
        for commit in test_log.commits:
            logging.info(commit.data)

    return context_id
