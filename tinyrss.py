#!/usr/bin/env python3
import csv
import concurrent.futures
import datetime
import functools
import itertools
import os
import subprocess
import sys
import time

import feedparser

def parse(kwargs):
    feed = feedparser.parse(**kwargs)
    if feed.bozo:
        print('{}: {}'.format(kwargs['url_file_stream_or_string'],
              feed.bozo_exception), file=sys.stderr)
        return '', [], '', ''
    else:
        return (feed.feed.title, feed.entries, feed.get('modified', ''),
                feed.get('etag', ''))

def pred(since, entry):
    dt = datetime.datetime
    keys = ['published_parsed', 'updated_parsed', 'created_parsed']
    key = min((i, k) for i, k in enumerate(keys) if k in entry)[1]
    return (dt(*entry[key][:6]) > dt.utcfromtimestamp(since))

def showfeed(feed, pred):
    title, entries, modified, etag = feed
    if title and entries:
        new = ['{}\n{}'.format(e.get('title', 'Untitled'), e.get('link', ''))
               for e in itertools.takewhile(pred, entries)]
        if new:
            print('* {}'.format(title))
            print('\n\n'.join(new), end='\n\n')
    return modified, etag

def main():
    zip = itertools.zip_longest
    with open(os.path.expanduser('~/.tinyrss/urls')) as f:
        data = list(csv.reader(f))
        while len(data[0]) < 3:
            data[0].append(None)
        urls, ms, etags = zip(*data)
    if not os.path.exists(os.path.expanduser('~/.tinyrss/since')):
        since = 0
    else:
        with open(os.path.expanduser('~/.tinyrss/since')) as f:
            since = float(f.read())
    with open(os.path.expanduser('~/.tinyrss/since'), 'w') as f:
        print(time.time(), file=f)
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as e:
        feeds = e.map(parse, ({'url_file_stream_or_string': u,
                               'etag': e,
                               'modified': m} for u, e, m in
                               zip(urls, ms, etags)))
        p = functools.partial(pred, since)
        ms, etags = zip(*[showfeed(f, p) for f in feeds])
    with open(os.path.expanduser('~/.tinyrss/urls'), 'w') as f:
        csv.writer(f).writerows(zip(urls, ms, etags))

if __name__ == '__main__':
    main()
