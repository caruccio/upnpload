#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import collections
import itertools
import random
import mimetypes
import BaseHTTPServer
import SocketServer
import StringIO
import posixpath
import shutil
import atexit
import upnp

if not getattr(StringIO.StringIO, '__enter__', None):
	# py2.6 and older StringIO has no context management protocol: http://bugs.python.org/issue1286
	def __strio__enter__(self):
		if self.closed:
			raise ValueError("I/O operation on closed file")
		return self
	def __strio__exit__(self, exc, value, tb):
		self.close()
	setattr(StringIO.StringIO, '__enter__', __strio__enter__)
	setattr(StringIO.StringIO, '__exit__',  __strio__exit__)

parser = argparse.ArgumentParser(description='Dead simple file upload through UPnP routers')
parser.add_argument('FILE', default=sys.stdin, type=argparse.FileType('r'),
	help='File(s) to serve', nargs='*')
parser.add_argument('-e', '--ext-port', metavar='PORT', dest='ext_port', default=0, type=int,
	help='External port to listen for incoming connection')
parser.add_argument('-i', '--int-port', metavar='PORT', dest='int_port', default=0, type=int,
	help='Internal port to listen for incoming connection')
parser.add_argument('-p', '--port', metavar='PORT', dest='port', default=0, type=int,
	help='Both ports to listen for incoming connection')
parser.add_argument('-n', metavar='COUNT', dest='count', default=1, type=int,
	help='How many times to serve each file')
parser.add_argument('-c', metavar='CONTENT-TYPE', dest='ctype', default='application/octet-stream', type=str,
	help='Force content-type')
parser.add_argument('-l', dest='list_maps', action='store_true', default=False,
	help='List active mappings and exit')
args = parser.parse_args()

if args.port and (args.ext_port or args.int_port):
	print "---> error: can't use parameter -p with -e/-i"
	sys.exit(1)

print '---> searching for UPnP router/wifi...',
sys.stdout.flush()
try:
	device = upnp.discover()
except KeyboardInterrupt:
	sys.exit(0)

if not device:
	print "---> I could not find a usable router/wifi device."
	print "---> Maybe it is not UPnP capable or UPnP support is disabled."
	print "---> Please check your device's config and try againg"
	sys.exit(1)
print '%s (%s)' % (device.url, device.type)

if args.list_maps:
	for m in filter(lambda x: x.name.startswith(device.map_prefix), device.mappings):
		print '%s %s:%s -> %s:%s (%s)' % (m.proto,
			m.external.addr or device.external.addr, m.external.port,
			m.internal.addr, m.internal.port, m.name)
	sys.exit(0)

try:
	mapping = device.map(external_port=args.ext_port, internal_port=args.int_port)
	atexit.register(device.unmap, mapping)
except Exception, ex:
	print '---> Oops, something went wrong. This is the error message:'
	print '%s: %s' % (ex.__class__.__name__, ex)
	sys.exit(1)

if not mimetypes.inited:
	mimetypes.init()

class RestrictedHTTPServer(BaseHTTPServer.BaseHTTPRequestHandler):
	served = None

	def __init__(self, *vargs, **kvargs):
		BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *vargs, **kvargs)

	def do_HEAD(self):
		self.send_head()

	def do_GET(self):
		f = self.send_head()
		shutil.copyfileobj(f, self.wfile)

	def send_head(self):
		print '---> %s %s from %s:%s' % tuple((self.command, self.path) + self.client_address)
		if self.path in [ '', '/' ]:
			path = sys.stdin.name
			ctype = args.ctype
		else:
			path = self.path[1:]
		file = filter(lambda file: file.name == path, args.FILE)
		if not file:
			self.send_response(404)
			self.send_header("Content-Length", '0')
			self.end_headers()
			return StringIO.StringIO()
		file = file[0]
		file.seek(0)

		RestrictedHTTPServer.served[path] -= 1
		left = RestrictedHTTPServer.served[file.name]

		self.send_response(200)
		if file is not sys.stdin:
			base, ext = posixpath.splitext(self.path)
			ctype = mimetypes.types_map.get(ext, mimetypes.types_map.get(ext.lower(), args.ctype))
			fs = os.fstat(file.fileno())
			self.send_header("Content-Length", str(fs[6]))
			#self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
		self.send_header("Content-type", ctype)
		self.end_headers()
		print '---> file %s served, %i left' % (file.name, left)
		if not left:
			args.FILE.remove(file)
			RestrictedHTTPServer.served.pop(file.name, None)
		return file

server = BaseHTTPServer.HTTPServer((mapping.internal.addr, mapping.internal.port), RestrictedHTTPServer)

print '---> serving files:'
if args.FILE is sys.stdin:
	print 'http://%s:%s' % (device.external.addr, mapping.external.port)
else:
	for name in [ f.name for f in args.FILE ]:
		print 'http://%s:%s/%s' % (device.external.addr, mapping.external.port, name)

RestrictedHTTPServer.served = dict(itertools.izip([ f.name for f in args.FILE ],
											itertools.repeat(args.count)))
def serving():
	return RestrictedHTTPServer.served is None or len(RestrictedHTTPServer.served) > 0

while serving():
	try:
		server.handle_request()
	except KeyboardInterrupt:
		sys.exit(0)
print '---> all files upload'
