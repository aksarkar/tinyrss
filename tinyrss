#!/usr/bin/env python3
import concurrent.futures
import datetime
import functools
import html.parser
import itertools
import os
import subprocess
import sys
import time
import textwrap

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
        show = ShowContent(f)
        showfield(entry, 'title', f)
        showfield(entry, 'author', f)
        showfield(entry, 'link', f)
        for t in entry.get('content', []):
            show.feed(t.value)
            show.close()
    p = subprocess.Popen(['less', curr])
    p.wait()

def showfield(entry, k, f):
    if entry.has_key(k):
        print(entry.get(k), file=f)

class ShowContent(html.parser.HTMLParser):
    def __init__(self, f):
        super(ShowContent, self).__init__()
        self.f = f
        self.links = []
        self.par = []
        self.addlink = False

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.par = []
        elif tag == 'a':
            self.links.append(dict(attrs)['href'])
            self.addlink = True

    def handle_endtag(self, tag):
        if tag == 'p':
            print('\n'.join(textwrap.wrap(''.join(self.par), width=80)),
                  file=self.f, end='\n\n')
        elif tag == 'a':
            self.addlink = False

    def handle_data(self, data):
        self.par.append(data)
        if self.addlink:
            self.par.append('[{}]'.format(len(self.links)))


    def close(self):
        for i, l in enumerate(self.links):
            print('[{}] {}'.format(i + 1, l), file=self.f)
        super().close()

if __name__ == '__main__':
    with open(os.path.expanduser('~/.tinyrss/urls')) as f:
        urls = [line.strip() for line in f]
    with open(os.path.expanduser('~/.tinyrss/modified')) as f:
        ms = [line.strip() for line in f]
    with open(os.path.expanduser('~/.tinyrss/etags')) as f:
        etags = [line.strip() for line in f]
    with open(os.path.expanduser('~/.tinyrss/since')) as f:
        since = float(f.read())
    with open(os.path.expanduser('~/.tinyrss/since'), 'w') as f:
        print(time.time(), file=f)

    zip = itertools.zip_longest
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as e:
        feeds = e.map(parse, ({'url_file_stream_or_string': u,
                                'etag': e,
                                'modified': m} for u, e, m in
                                zip(urls, ms, etags)))
        p = functools.partial(pred, since)
        ms, etags = zip(*(showfeed(f, p) for f in feeds))

    with open(os.path.expanduser('~/.tinyrss/modified'), 'w') as f:
        print('\n'.join(ms), file=f)
    with open(os.path.expanduser('~/.tinyrss/etags'), 'w') as f:
        print('\n'.join(etags), file=f)
