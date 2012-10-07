#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import itertools
import random
import mimetypes
import BaseHTTPServer
import SocketServer
import posixpath
import shutil
import atexit
import upnp

try:
	filename = sys.argv[1]
except IndexError:
	print >>sys.stderr, 'Usage: %s FILE [PORT]' % sys.argv[0]
	sys.exit(1)

print '---> searching for UPnP router/wifi...',
sys.stdout.flush()
device = upnp.discover()
if not device:
	print "---> I could not find a usable router/wifi device."
	print "---> Maybe it is not UPnP capable or UPnP support is disabled."
	print "---> Please check your device's config and try againg"
	sys.exit(1)

print '%s (%s)' % (device.url, device.type)
try:
	mapping = device.map()
	atexit.register(device.unmap, mapping)
except Exception, ex:
	print '---> Ops, something went wrong. This is the error message:'
	print '%s: %s' % (ex.__class__.__name__, ex)
	sys.exit(1)

if not mimetypes.inited:
	mimetypes.init()

class SingleFileHTTPServer(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_HEAD(self):
		with self.send_head():
			pass

	def do_GET(self):
		with self.send_head() as f:
			shutil.copyfileobj(f, self.wfile)

	def send_head(self):
		try:
	 		f = open(filename, 'rb')
		except IOError, ex:
			if ex.errno == errno.EACCES:
				self.send_response(403)
			elif ex.errno == errno.ENOENT:
				self.send_response(404)
			else:
				self.send_response(500)
			self.send_header("Content-Length", '0')
			self.end_headers()
			return None

		base, ext = posixpath.splitext(filename)
		ctype = mimetypes.types_map.get(ext, mimetypes.types_map.get(ext.lower(), 'application/octet-stream'))
		self.send_response(200)
		self.send_header("Content-type", ctype)
		fs = os.fstat(f.fileno())
		self.send_header("Content-Length", str(fs[6]))
		#self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
	 	self.end_headers()
	 	return f

server = BaseHTTPServer.HTTPServer((mapping.internal.addr, mapping.internal.port), SingleFileHTTPServer)
print '---> serving file: %s' % os.path.abspath(filename)
print '---> public url: http://%s:%s/%s' % (device.external.addr, mapping.external.port, os.path.basename(filename))
server.handle_request()
print '---> file sent'
