#!/usr/bin/env python3
"""Fetch a URL and print its visible text (stdlib only). Usage: fetch_text.py URL [-o FILE]"""
import re, sys, ssl, urllib.request
from html.parser import HTMLParser

class T(HTMLParser):
    SKIP = {"script", "style", "noscript"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "table", "section"}
    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0
    def handle_starttag(self, t, a):
        if t in self.SKIP: self.skip += 1
        if t in self.BLOCK: self.out.append("\n")
    def handle_endtag(self, t):
        if t in self.SKIP and self.skip: self.skip -= 1
        if t in self.BLOCK: self.out.append("\n")
    def handle_data(self, d):
        if not self.skip: self.out.append(d)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40, context=ssl.create_default_context()) as r:
        raw = r.read(); ct = r.headers.get_content_charset() or "utf-8"
    html = raw.decode(ct, errors="replace")
    p = T(); p.feed(html)
    return re.sub(r"\n\s*\n+", "\n", "".join(p.out))

def norm(s):
    return re.sub(r"\s+", "", s)

if __name__ == "__main__":
    txt = fetch(sys.argv[1])
    if "-o" in sys.argv:
        open(sys.argv[sys.argv.index("-o") + 1], "w").write(txt)
    else:
        print(txt)
