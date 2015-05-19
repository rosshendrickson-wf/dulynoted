# dulynoted
A Google App Engine commit log implementation

# Use case

This is pre-alpha code. Should it pan out I may use it in production at some
point in time

# Motivation

There are several highly distributed systems on Appengine that make use of
hundreds, thousands, even hundreds of thousands or millions of tasks. Trying to
create a reasonable time line or process graph with some type of programatic
log system is pretty much not a good idea to do on app engine. That said, I was
interested in looking at building a simple Write Ahead Log that would help ease
some of contention during bursts of writes. Also, I'm looking at using it in a
sharded manner so that different parts of the system can track certain things
into a very specific timeline manner.

# How to use?

You can write you own code or you can push the repo using app cfg and run the
example by simply navigating to root. That will insert some tasks that all try
to write to a specific module. This uses indexes and those need to be updated on
the appspot.


```python
log = Log()
log.put()
log.new_commit(data)

for commit in log.commits():
    process_commit(commit)

```


# Performance

I plan on having it work in two modes, every write must have a transaction on
the revision counter and slightly less correct mode that when transaction
collisions occur it just writes out the commit, ties it to the revision and the
consumer can decide how to process that

Transaction mode is  30/50 commits/second

Less contentious mode with incrementing ids as fast as possible is ~800 commits/second

# General TODO

There are also things that can be done to ensure that bigtable doesn't scream
under the load. Commits need unique distributed key ids vs auto would be a good
first step.

Non Object method ways of updating, you don't want to have to get the log to put
in a commit when you're going to get it in the transaction, you don't need it, 
you only need the key.

I looked at switching to using a pull queue but the write characteristics are
not that appealing when you lose the querability of key properties.

Need to tighten up the queries and ensure the timestamps are being sorted
correctly on the sharded versions.


