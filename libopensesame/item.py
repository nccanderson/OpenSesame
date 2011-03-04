"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

import openexp.trial
from libopensesame import exceptions
import shlex
import sys

class item(openexp.trial.trial):

	"""
	item is an abstract base class which provides basic
	functionality to be used in derived classes, such
	as sketchpad, keyboard_response, etc.
	"""

	def __init__(self, name, experiment, string = None):
	
		"""
		Generic item initialization
		"""
	
		self.name = name
		self.experiment = experiment
		self.debug = "--debug" in sys.argv
		self.count = 0
		
		if not hasattr(self, "item_type"):		
			self.item_type = "item"
		if not hasattr(self, "description"):
			self.description = "Default description"
		if not hasattr(self, "round_decimals"):
			self.round_decimals = 2
		self.variables = {}
		self.comments = []
		
		if string != None:
			self.from_string(string)

	def prepare(self):
	
		"""
		Derived classes should use this function
		to prepare the item for speedy execution
		during the run phase.
		"""
		
		self.experiment.set("count_%s" % self.name, self.count)
		self.count += 1
	
		return True

	def run(self):
	
		"""
		Derived classes should use this function
		to perform the item specific function.
		"""
	
		return True		
		
	def parse_variable(self, line):
	
		"""
		Reads a single variable from a single line
		"""
		
		# It is a little ugly to call parse_comment() here, but otherwise
		# all from_string() derivatives need to be modified
		if self.parse_comment(line):
			return True
	
		try:
			l = shlex.split(line.strip())
		except Exception as e:
			raise exceptions.script_error("Error parsing '%s' in item '%s': %s" % (line, self.name, e))
			
		if len(l) > 0 and l[0] == "set":			
			if len(l) != 3:			
				raise exceptions.script_error("Error parsing variable definition: '%s'" % line)				
			else:						
				self.set(l[1], l[2])
				return True
				
		return False
				
	def parse_comment(self, line):
	
		"""
		Parses comments, indicated by # // or '
		"""
		
		if len(line) > 0 and line[0] == "#":
			self.comments.append(line[1:])
			return True
		elif len(line) > 1 and line[0:2] == "//":
			self.comments.append(line[2:])
			return True
		return False
			
	def variable_to_string(self, var):
	
		"""
		Translates the variables back into a string
		"""
		
		return "set %s \"%s\"\n" % (var, self.variables[var])
		
	def from_string(self, string):
	
		"""
		Reads variables from the string
		"""
		
		self.variables = {}
		for line in string.split("\n"):
			self.parse_variable(line)			
		
	def to_string(self, item_type = None):
	
		"""
		Translates the item back into a string
		"""
		
		if item_type == None:
			item_type = self.item_type
	
		s = "define %s %s\n" % (item_type, self.name)
		for comment in self.comments:
			s += "\t# %s\n" % comment.strip()
		for var in self.variables:
			s += "\t" + self.variable_to_string(var)
		return s		
		
	def set(self, var, val):
	
		"""
		Set a variable
		"""
	
		val = self.auto_type(val)		
		if type(val) == float:
			exec("self.%s = %f" % (var, val))
		elif type(val) == int:
			exec("self.%s = %d" % (var, val))
		else:
			val = val.replace("\"", "'")
			exec("self.%s = \"%s\"" % (var, val))
		
		self.variables[var] = val			
		
	def unset(self, var):
	
		"""
		Unset a variable
		"""
		
		if var in self.variables:
			del self.variables[var]
			
		try:				
			exec("del self.%s" % var)
		except:
			pass		
						
	def get(self, var):
	
		"""
		Retrieve a variable. First check the item, and
		fall back to the experiment.
		"""
	
		if hasattr(self, var):		
			val = eval("self.%s" % var)
		else:
			try:
				val = eval("self.experiment.%s" % var)
			except:						
				raise exceptions.runtime_error("Variable '%s' is not set in item '%s'.<br /><br />Make sure that you have spelled and capitalized the variable name correctly. You may wish to use the variable inspector (Control + I) to find the intended variable." % (var, self.name))
				
		# Process variables, indicated like [varname]
		if self.experiment.running and type(val) == str and len(val) > 3 and val[0] == "[" and val[-1] == "]":
			if val[1:-1] == var:
				raise exceptions.runtime_error("Variable '%s' is defined in terms of itself (e.g., 'var = [var]') in item '%s'" % (var, self.name))
			val = self.get(val[1:-1])
		
		return val
		
	def has(self, var):
	
		"""
		Check if the variable exists
		"""
		return hasattr(self, var) or hasattr(self.experiment, var)
				
	def auto_type(self, val):
	
		"""
		Automatically convert a string to
		the appropriate type
		"""	
		
		try:
			if int(float(val)) == float(val):
				return int(float(val))
			else:
				return float(val)
		except:
			return str(val)
			
	def set_item_onset(self, time = None):
	
		"""
		Used to record the time at which an item appears
		"""
		
		if time == None:
			time = self.time()	
		exec("self.experiment.time_%s = %d" % (self.name, time))
		
	def prepare_duration(self):
	
		"""
		Sets the _duration_func based on the
		duration and compensation variables
		"""
		
		# Prepare the duration function
		if self.has("compensation"):
			try:
				self._compensation = int(self.get("compensation"))
			except:
				raise exceptions.runtime_error("Variable 'compensation' should be numeric and not '%s' in %s item'%s'" % (self.get("compensation"), self.item_type, self.name))
		else:
			self._compensation = 0
			
		dur = self.get("duration")
		if dur == "keypress":
			if self.experiment.auto_response:
				self._duration_func = self.sleep_for_duration
				self._duration = 500
			else:
				self._duration_func = self.experiment.wait
		elif dur == "mouseclick":
			if self.experiment.auto_response:
				self._duration_func = self.sleep_for_duration
				self._duration = 500
			else:		
				self._duration_func = openexp.response.get_mouse
		else:
			try:				
				self._duration = int(self.get("duration"))			
			except:
				raise exceptions.runtime_error("Invalid duration '%s' in sketchpad '%s'. Expecting a positive number or 'keypress'." % (self.get("duration"), self.name))					
			if self._duration == 0:
				self._duration_func = self.dummy
			else:
				if self._compensation != 0:
					self._duration_func = self.sleep_for_comp_duration
				else:
					self._duration_func = self.sleep_for_duration		

	def sleep_for_duration(self):
	
		"""
		Sleep for a specified time
		"""
		
		self.sleep(self._duration)	
		
	def sleep_for_comp_duration(self):
	
		"""
		Sleep for a specified time
		"""
		
		self.sleep(self._duration - self._compensation)					
		
	def dummy(self):
	
		pass
		

	def eval_text(self, text, round_float = False):
	
		"""
		Replace variables in the text by the actual values
		"""
		
		# If the text is not a string, there cannot be any variables,
		# so return right away
		if type(text) != str:
			return self.auto_type(text)
			
		# Prepare a template for rounding floats
		if round_float:
			float_template = "%%.%sf" % self.get("round_decimals")
			
		s = ""
		while True:
		
			# Find the start and end of a variable definition
			start = text.find("[")
			if start < 0:
				break				
			end = text.find("]")
			if end < 0:
				raise exceptions.runtime_error("Missing closing bracket ']' in item '%s'" % self.name)			
			var = text[start+1:end]
			
			# Get the variable
			val = self.get(var)
				
			# Round floats
			if round_float and type(val) == float:
				val = float_template % val
			
			# Replace the variable name with the value
			text = text[:start] + str(val) + text[1+end:]
		
		# Return the result
		return self.auto_type(text)
		
	def match(self, s):
	
		"""
		Evaluate conditional statements, e.g.,
		[test] = 1 or [test] = 2
		[response_time] > 512
		"""
		
		if s == "always":
			return True

		l = s.split(" and ")
		if len(l) > 1:
			return self.match(l[0]) and self.match(l[1])
		
		l = l[0].split(" or ")
		if len(l) > 1:
			return self.match(l[0]) or self.match(l[1])
		
		l = l[0].split()
	
		if len(l) != 3:
		
			raise exceptions.runtime_error("Failed to evaluate '%s' in item '%s'" % (s, self.name))
		
		else:
		
			a = l[0]
			# For backward compatibility, brackets around the first variable
			# are not required
			if a[0] == "[":
				a = self.get(a[1:-1])
			elif self.has(a):			
				a = self.get(a)
				
			c = l[2]
			if c[0] == "[":
				c = self.get(c[1:-1])
	
			if l[1] == "=":
				b = "=="
			else:
				b = l[1]
		
			try:		
				return eval("\"%s\" %s \"%s\"" % (a, b, c))
			except:
				raise exceptions.runtime_error("Failed to evaluate '%s' in sequence item '%s'" % (s, self.name))
	
		return True				
		
	def var_info(self):
	
		"""
		Give a list of dictionaries with variable descriptions
		"""
		
		return [ ("time_%s" % self.name, "<i>Determined at runtime</i>"), ("count_%s" % self.name, "<i>Determined at runtime</i>") ]
		