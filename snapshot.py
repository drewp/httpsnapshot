#!/usr/bin/python
"""
Released under MIT license. See bottom of file.

Run this with python, or with a wsgi server (the app object is called
snapshot.application).

When the user posts to /foo, we fetch http://othersite/bar and save it
to a new file. We may overwrite previous files if the template makes
the same name twice. We will make directories as needed. The cookie
header (so far) will be repeated on the inner request.

I use this to make the 'snapshot' feature of my webcam system, but it
is not at all specific to images.

The config is a json file of local resource paths, the remote
resources they get, and the filename templates they write to.
"""

import sys, web, restkit, json, logging, os, datetime, traceback

log = logging.getLogger()

class Config(object):
    def __init__(self, filename):
        self.filename = filename
        self.mtime = None
        self._reread()

    def _reread(self):
        current = os.path.getmtime(self.filename)
        if current > self.mtime:
            self.mtime = current
            log.info("reread %s", self.filename)
            conf = json.loads(open(self.filename).read())
            self.rec = {} # localPath : full record
            for r in conf['snapshots']:
                self.rec[r['localPath']] = r

    def getRecord(self, path):
        """look up by localPath"""
        self._reread()
        return self.rec[path]
    
class index(object):
    def GET(self):
        return "snapshot service. todo: show possible urls, status of last snapshots, etc"

class snapshot(object):
    def POST(self, path):
        rec = config.getRecord(path)
        outPath = self.interpolateOutputPath(rec)

        body = self.fetchResource(rec['getUrl'])
        
        self.writeOutput(outPath, body)
        
        raise web.SeeOther("file://%s" % outPath)

    def fetchResource(self, url):
        response = restkit.request(url=url,
                                   headers=self.proxyHeaders())
        if not response.status.startswith('2'):
            raise ValueError("request failed with %r" % response.status)
        body = response.body_string()

        log.info("got %s byte response, content-type %s", len(body),
                 response['headers'].get('content-type', None))
        return body

    def writeOutput(self, outPath, body):
        dirName = os.path.dirname(outPath)
        if not os.path.isdir(dirName):
            os.makedirs(dirName)
        with open(outPath, "w") as f:
            f.write(body)
        log.info("wrote %s", outPath)

    def interpolateOutputPath(self, rec):
        now = datetime.datetime.now()
        try:
            return rec['saveTemplate'].format(
                localTime=now.strftime("%Y-%m-%dT%H:%M:%S"),
                timeToTheMinute=now.strftime("%Y-%m-%dT%H:%M"),
                # ...
                )
        except Exception, e:
            raise ValueError(
                "while interpolating template %r, this error occurred: %s" %
                (rec['saveTemplate'],
                 traceback.format_exception_only(type(e), e)[-1]))

    def proxyHeaders(self):
        heads = {'user-agent' : 'snapshot'}
        for repeatedHeader in ['cookie']:
            try:
                heads[repeatedHeader] = web.ctx.environ['HTTP_%s' %
                                                        repeatedHeader.upper()]
            except KeyError:
                pass
        return heads
        
logging.basicConfig(level=logging.INFO)
config = Config("snapshot.json")

urls = (r'/', "index",       
        r'(/.*)', 'snapshot',
        )

app = web.application(urls, globals(), autoreload=True)
application = app.wsgifunc()

if __name__ == '__main__':
    sys.argv.append("9057") 
    app.run()

"""
The MIT License

Copyright (c) 2010 Drew Perttula

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
