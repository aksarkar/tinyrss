#!/usr/bin/env python3
import hashlib
import os
import sys
import tempfile

import feedparser

def guid(entry):
    if 'id' in entry:
        return entry.id
    else:
        return entry.link

def handle_feed(url, etag, modified, seen):
    feed = feedparser.parse(url, etag=etag, modified=modified)
    if feed.bozo:
        print('{}: {}'.format(url, feed.bozo_exception), file=sys.stderr)
        return etag, modified, seen
    else:
        s = set(seen)
        new = [e for e in feed.entries if guid(e) not in s]
        if new:
            print('* {}'.format(feed.feed.title))
        for e in new:
            print('  {}\n  {}'.format(e.get('title', 'Untitled'),
                                      e.get('link', '')),
                  end='\n\n')
        return (feed.get('etag', ''), feed.get('modified', ''),
                seen + [guid(e) for e in new])

def main():
    url = sys.argv[1]
    h = hashlib.sha1(url.encode('utf-8')).hexdigest()
    db_path = os.path.join(os.getenv('XDG_CONFIG_HOME',
                                 os.path.expanduser('~/.config')),
                                 'tinyrss', h)
    if os.path.exists(db_path):
        with open(db_path) as f:
            etag, modified, *seen = [line.strip() for line in f]
    else:
        etag, modified, seen = '', '', []
    etag, modified, seen = handle_feed(url, etag, modified, seen)
    out = '{}.1'.format(db_path)
    with open(out, 'w') as f:
        print(etag, modified, '\n'.join(seen), sep='\n', file=f)
    os.replace(out, db_path)

if __name__ == '__main__':
    main()
