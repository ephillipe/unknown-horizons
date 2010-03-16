# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

from horizons.world.player import Player
from horizons.ext.enum import Enum
from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import Callback

class AIPlayer(Player):
	"""Class for AI players implementing generic stuff."""
	
	shipStates = Enum('idle', 'moving_random', 'moving_to_branch', 'reached_branch')
	
	def __init__(self, *args, **kwargs):
		super(AIPlayer, self).__init__(*args, **kwargs)
		self.__init()

	def __init(self):
		self.ships = {} # {ship : state}. used as list of ships and structure to know their state

	def _load(self, db, worldid):
		super(AIPlayer, self)._load(db, worldid)
		self.__init()

	def send_ship_random(self, ship):
		"""Sends a ship to a random position on the map.
		@param ship: Ship instance that is to be used."""
		self.log.debug("%s %s: moving to random location", self.__class__.__name__, self.getId())
		# find random position
		point = self.session.world.get_random_possible_ship_position()
		# move ship there:
		try:
			ship.move(point, Callback(self.ship_idle, ship))
		except MoveNotPossible:
			# select new target soon:
			self.notify_unit_path_blocked(ship)
			return
		self.ships[ship] = self.shipStates.moving_random
	
	def ship_idle(self, ship):
		"""Called if a ship is idle. Sends ship to a random place.
		@param ship: ship instance"""
		self.log.debug("%s %s: idle, moving to random location", self.__class__.__name__, self.getId())
		Scheduler().add_new_object(Callback(self.send_ship_random, ship), self)