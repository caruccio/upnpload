import sys
import collections
import itertools
import random
import miniupnpc

Host = collections.namedtuple('Host', 'addr port')
Mapping = collections.namedtuple('Mapping', 'name external internal proto')
MiniMapping = collections.namedtuple('MiniMapping', 'external_port proto internal name enabled external_addr duration')

class Device:
	def __init__(self, client):
		self.client = client
		self.map_prefix = 'upnpload'
		self.url = client.selectigd()
		self.type = client.connectiontype()
		self.status = client.statusinfo()
		self.external = Host(self.client.externalipaddress(), 0)
		self.mappings, self.used_internal_ports, self.used_external_ports = self._mappings()

	def __str__(self):
		return 'Device(url=%s, type=%s, status=%s)' % (self.url, self.type, self.status)

	def _mappings(self):
		def _iter_mappings(cli):
			for i in xrange(65535):
				m = cli.getgenericportmapping(i)
				if not m:
					break
				m = MiniMapping(*m)
				yield Mapping(name=m.name, external=Host(m.external_addr, m.external_port), internal=Host(*m.internal), proto=m.proto)
		mappings = list(itertools.takewhile(lambda x: x, _iter_mappings(self.client)))
		used_local_ports = set([ x[0] for x in mappings ])
		used_remote_ports = set([ x[2][1] for x in mappings ])
		return mappings, used_local_ports, used_remote_ports

	def _available_port(self, exclude):
		i = random.randint(1025, 65535)
		while i in exclude:
			i = random.randint(1025, 65535)
		return i

	def map(self, external_ip='', external_port=0, internal_ip='', internal_port=0, proto='TCP'):
		ext_ip   = external_ip # or self.client.externalipaddress()
		int_ip   = internal_ip or self.client.lanaddr
		ext_port = external_port or self._available_port(exclude=self.used_external_ports)
		int_port = internal_port or self._available_port(exclude=self.used_internal_ports)
		name_components = map(str, (ext_port, int_ip, int_port))
		name = '%s-%s' % (self.map_prefix, '.'.join(name_components))
		if not self.client.addportmapping(ext_port, proto.upper(), int_ip, int_port, name, ext_ip):
			return False

		self.mappings.append(Mapping(name=name, external=Host(ext_ip, ext_port), internal=Host(int_ip, int_port), proto=proto.upper()))
		self.used_internal_ports.add(int_port)
		self.used_external_ports.add(ext_port)

		return self.mappings[-1]

	def unmap(self, mapping, proto='TCP'):
		try:
			addr = mapping.external.addr
			port = mapping.external.port
			proto = mapping.proto
		except:
			addr = ''
			port = mapping
		self.client.deleteportmapping(port, proto, addr)

def discover():
	upnp = miniupnpc.UPnP()
	upnp.discoverdelay = 2000

	if not upnp.discover():
		return None

	return Device(upnp)

if __name__ == '__main__':
	dev = discover()
	if not dev:
		sys.exit(1)

	print dev
	for i, m in enumerate(dev.mappings):
		print m
