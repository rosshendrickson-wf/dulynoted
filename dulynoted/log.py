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
import logging

from google.appengine.ext import ndb
from google.appengine.ext.db import TransactionFailedError
from furious.batcher import Message


class Log(ndb.Model):
    """Simple model to help linearize writes to another possibly more heavy
    process using lighter weight NDB entities and avoiding cross group
    transactions on the write portion of the work.
    """

    parent = ndb.KeyProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    latest_revision = ndb.IntegerProperty(default=0)
    applied_revision = ndb.IntegerProperty()

    @property
    def name(self):
        """The keyname of the model"""
        return str(self.key.id())

    @property
    def commits(self):
        """Will get all the commits for the Log in ascending order"""
        query = Commit.query()
        query = query.filter(Commit.parent_key == self.key,
                             Commit.revision <= self.latest_revision)
        query.order(Commit.revision)
        query.order(Commit.created)
        return query.fetch()

    @property
    def revisions(self):
        query = Commit.query(Commit.parent_key == self.key, projection=[Commit.revision])
        query.order(Commit.revision)
        return query.fetch(10)

    @property
    def revision_shards(self):
        query = RevisionShard.query(RevisionShard.log_key == self.key)
        query.order(RevisionShard.revision)
        return query.fetch(10)

    def commit_range(self, bottom, top, applied=False):

        query = Commit.query(Commit.parent_key == self.key, Commit.revision >= bottom,
                           Commit.revision <= top, Commit.applied == applied)
        query.order(Commit.revision)
        return query.fetch(10)

    def load_commit(revision):
        return Commit.query(Commit.revision == revision).fetch()

    @property
    def uncommitted():
        query = Commit.query(Commit.revision >= self.applied_revision,
                             Commit.applied == False)
        return query.fetch(10)

    def new_commit(self, data):
        """Will transcationally increment this model's revision and then use
        that new revision for the commit.
        """
        data = str(data)
        new_revision = self.latest_revision

        #return self.new_shard_commit(new_revision, data)

        try:
            new_revision = get_new_revision(self.key)
        except TransactionFailedError:
            return self.new_shard_commit(new_revision, data)

        commit = self._new_commit(new_revision, data)
        commit.put()
        return commit

    def _new_commit(self, new_revision, data):
        commit = Commit()
        commit.revision = new_revision
        commit.data = data
        commit.parent = self.name
        commit.parent_key = self.key
        return commit

    def new_shard_commit(self, revision, data):
        """In the event there is transaction contention on the counter, push
        the commit down to a pull queue with the appropriate tag to be able to
        retrieve it when we pull out history"""

        commit = self._new_commit(revision, data)
        tag = "-".join((self.name, str(revision)))
        shard_commit(self.key, tag, revision, commit)
        return commit


@ndb.transactional(xg=True)
def shard_commit(log_key, tag, shard_revision, commit):

    # I don't like this because it will cause hot tables - need to do some
    # ancestor and entity group magic here
    revision = RevisionShard.get_by_id(tag)
    if not revision:
        revision = RevisionShard(id=tag)
        revision.revision = shard_revision
        revision.log_key = log_key

    revision.count += 1
    commit.put()
    revision.commit_keys.append(commit.key)
    revision.put()

class RevisionShard(ndb.Model):
    """Marks the relationship between the revision and messages in the pull
    queue for that revision"""
    revision = ndb.IntegerProperty(default=0, indexed=True)
    count = ndb.IntegerProperty(default=0, indexed = False)
    log_key = ndb.KeyProperty(indexed=True)
    commit_keys = ndb.KeyProperty(repeated=True)

    @property
    def commits(self):
        """Pull out the commits that were part of this shard"""
        #There are ways to make this more efficient
        for commit_key in self.commit_keys:
            yield commit_key.get()

# TODO - Spread out the ID creation so we're not relying on auto create
class Commit(ndb.Model):
    """Roughly designed to hold a unit of work to be done at another point of
    time or to store information for a specific revision of some process"""
    applied = ndb.BooleanProperty(default=False, indexed=True)
    revision = ndb.IntegerProperty(indexed=True)
    parent_key = ndb.KeyProperty(indexed=True)
    data = ndb.BlobProperty(indexed=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def get_parent(self):
        return Log.get_by_id(self.parent)


@ndb.transactional()
def get_new_revision(log_key):
    """Transactionally increments the revision of the counter"""
    log = log_key.get()

    if not log_key:
        raise Exception("No log!")

    if not log.latest_revision:
        log.latest_revision = 0

    log.latest_revision += 1
    log.put()

    return log.latest_revision
