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
    return feed

def pred(since, entry):
    dt = datetime.datetime
    keys = ['published_parsed', 'updated_parsed', 'created_parsed']
    key = min((i, k) for i, k in enumerate(keys) if k in entry)[1]
    return (dt(*entry[key][:6]) > dt.fromtimestamp(since))

def showfeed(feed, pred):
    if not feed.bozo:
        for e in feed.entries:
            showentry(e, p)
    return feed.get('modified', ''), feed.get('etag', '')

def showentry(entry, pred):
    if not pred(entry):
        return
    curr = os.path.expanduser('~/.tinyrss/curr')
    with open(curr, 'w') as f:
        print('<html><head><title></title></head><body>', file=f)
        showfield(entry, 'title', f, 'h1')
        showfield(entry, 'author', f, 'h2')
        showfield(entry, 'link', f, 'p')
        if entry.has_key('content'):
            print('\n'.join(x.value for x in entry.content), file=f)
        else:
            showfield(entry, 'description', f)
        print('</body></html>', file=f)
    p = subprocess.Popen(['w3m', '-T', 'text/html', curr])
    p.wait()

def showfield(entry, k, f, tag=''):
    if entry.has_key(k):
        if tag:
            print('<{}>{}</{}>'.format(tag, entry.get(k), tag), file=f)
        else:
            print(entry.get(k), file=f)

if __name__ == '__main__':
    zip = itertools.zip_longest
    with open(os.path.expanduser('~/.tinyrss/urls')) as f:
        data = list(csv.reader(f))
        while len(data[0]) < 3:
            data[0].append(None)
        urls, ms, etags = zip(*data)
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
