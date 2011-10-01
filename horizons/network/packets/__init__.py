# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA	02110-1301	USA
# ###################################################

import sys
import cPickle
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

import logging
from horizons.network import find_enet_module
enet = find_enet_module()

__version__ = '0.1'
__all__ = [
	'SafeUnpickler',
	'packet',
]

PICKLE_PROTOCOL = 2
PICKLE_RECIEVE_FROM = 'server'
PICKLE_SAFE = {
	'client' : {},
	'server' : {},
}

log = logging.getLogger("network")

class SafeUnpickler(object):
	@classmethod
	def add(self, origin, klass):
		global PICKLE_SAFE
		module = klass.__module__
		name  = klass.__name__
		types = ['client', 'server'] if origin == 'common' else [origin]
		for origin in types:
			if module not in PICKLE_SAFE[origin]:
				PICKLE_SAFE[origin][module] = set()
			if name not in PICKLE_SAFE[origin][module]:
				PICKLE_SAFE[origin][module].add(name)

	@classmethod
	def set_mode(self, client = True):
		global PICKLE_RECIEVE_FROM
		if client:
			PICKLE_RECIEVE_FROM = 'server'
		else:
			PICKLE_RECIEVE_FROM = 'client'

	@classmethod
	def find_class(self, module, name):
		global PICKLE_SAFE, PICKLE_RECIEVE_FROM
		if module not in PICKLE_SAFE[PICKLE_RECIEVE_FROM]:
			raise cPickle.UnpicklingError('Attempting to unpickle unsafe module "%s" (class="%s")' % (module, name))
		__import__(module)
		mod = sys.modules[module]
		if name not in PICKLE_SAFE[PICKLE_RECIEVE_FROM][module]:
			raise cPickle.UnpicklingError('Attempting to unpickle unsafe class "%s" (module="%s")' % (name, module))
		klass = getattr(mod, name)
		return klass

	@classmethod
	def loads(self, str):
		file = StringIO(str)
		obj = cPickle.Unpickler(file)
		obj.find_global = self.find_class
		return obj.load()

#-------------------------------------------------------------------------------

class packet:
	def __init__(self):
		self.sid = None

	def serialize(self):
		return cPickle.dumps(self, PICKLE_PROTOCOL)

	def send(self, peer, sid = None, channelid = 0):
		if sid is not None:
			self.sid = sid
		self._send(peer, self.serialize(), channelid)

	@staticmethod
	def _send(peer, data, channelid = 0):
		packet = enet.Packet(data, enet.PACKET_FLAG_RELIABLE)
		peer.send(channelid, packet)

#-------------------------------------------------------------------------------

class cmd_ok(packet):
	"""simple ok message"""

SafeUnpickler.add('common', cmd_ok)

#-------------------------------------------------------------------------------

class cmd_error(packet):
	def __init__(self, errorstr):
		self.errorstr = errorstr

SafeUnpickler.add('common', cmd_error)

#-------------------------------------------------------------------------------

class cmd_fatalerror(packet):
	def __init__(self, errorstr):
		self.errorstr = errorstr

SafeUnpickler.add('common', cmd_fatalerror)

#-------------------------------------------------------------------------------

def unserialize(data):
	packet = SafeUnpickler.loads(data)
	return packet

#-------------------------------------------------------------------------------

import horizons.network.packets.server
import horizons.network.packets.client

