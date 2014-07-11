#-*- coding:utf-8 -*-

"""
This file is part of openexp.

openexp is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

openexp is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with openexp.  If not, see <http://www.gnu.org/licenses/>.
"""

from libopensesame import debug
from libopensesame.exceptions import osexception

class base_element(object):

	"""
	desc:
		A base class from which all sketchpad elements are derived.
	"""


	def __init__(self, sketchpad, string, defaults=[]):

		"""
		desc:
			Constructor.

		arguments:
			sketchpad:		A sketchpad object.
			string:			A definition string.

		keywords:
			defaults:		A list with (name, default_value) tuples for all
							keywords.
		"""

		self._type = self.__class__.__name__
		debug.msg(self._type)
		self.defaults = defaults + [
			(u'z_index', 0),
			(u'show_if', u'always')
			]
		self.sketchpad = sketchpad
		self.from_string(string)
		self.eval_properties()
		self.topleft_coordinates() # TODO: To be deprecated

	@property
	def canvas(self): return self.sketchpad.canvas

	@property
	def get(self): return self.sketchpad.get

	@property
	def get_file(self): return self.sketchpad.experiment.get_file

	@property
	def name(self): return self.sketchpad.name

	@property
	def split(self): return self.sketchpad.split

	@property
	def z_index(self):

		"""
		desc:
			Determines the drawing order of the elements. Elements with a
			higher z-index are drawn first, so they are at the bottom of the
			stack.
		returns:
			A z-index.
		"""

		return self.properties[u'z_index']

	def draw(self):

		"""
		desc:
			Draws the element to the canvas of the sketchpad.
		"""

		pass

	def from_string(self, string):

		"""
		desc:
			Parse a definition string for the element.

		arguments:
			string:		A definition string.
		"""

		l  = self.split(string)
		if l < 2 or l[0] != u'draw' or l[1] != self._type:
			raise osexception(u'Invalid sketchpad-element definition: \'%s\'' \
				% string)
		# First load the default values
		self.properties = {}
		for var, val in self.defaults:
			self.properties[var] = val
		# Parse the specified values
		keyword_nr = 0
		vars_parsed = []
		for keyword in l[2:]:
			i = keyword.find(u'=')
			if i >= 0:
				var = keyword[:i]
				val = keyword[i+1:]
			else:
				var = self.defaults[keyword_nr][0]
				val = keyword
			if var in vars_parsed:
				raise osexception(
					(u'The keyword \'%s\' has been specified multiple times in '
					u'sketchpad element \'%s\' in item \'%s\'') % (var,
					self._type, self.name))
			vars_parsed.append(var)
			self.properties[var] = val
			keyword_nr += 1
		# Check if all values that need to be specified have indeed been
		# specified.
		for var, val in self.properties.items():
			if val == None:
				raise osexception(
					(u'The keyword \'%s\' has not been specified in '
					u'sketchpad element \'%s\' in item \'%s\'') % (var,
					self._type, self.name))
		# Check if no non-existing keywords have been specified
		for var in self.properties.keys():
			valid = False
			for _var, _val in self.defaults:
				if _var == var:
					valid = True
					break
			if not valid:
				raise osexception(
					(u'The keyword \'%s\' is not applicable to '
					u'sketchpad element \'%s\' in item \'%s\'') % (var,
					self._type, self.name))

	def to_string(self):

		"""
		desc:
			Generates a string representation of the element.

		returns:
			A string representation.
		"""

		s = u'draw %s' % self._type
		for var, val in self.defaults:
			val = self.properties[var]
			if isinstance(val, basestring):
				s += u' %s="%s"' % (var, val)
			else:
				s += u' %s=%s' % (var, val)
		return s

	def topleft_coordinates(self):

		"""
		desc:
			Converts all coordinates to top-left. This function should be
			deprecated when center coordinates are used throughout.
		"""

		xc = self.get(u'width')/2
		yc = self.get(u'height')/2
		for var in self.properties:
			if var in [u'x', u'x1', u'x2']:
				self.properties[var] += xc
			if var in [u'y', u'y1', u'y2']:
				self.properties[var] += yc

	def eval_properties(self):

		"""
		desc:
			Evaluates all properties.
		"""

		for var, val in self.properties.items():
			if var == u'text':
				round_float = True
			else:
				round_float = False
			self.properties[var] = self.sketchpad.eval_text(val,
				round_float=round_float)
