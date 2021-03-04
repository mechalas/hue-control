from isodate import parse_datetime, parse_time
import re
import calendar
import itertools

ymd= '[0-9]{4}-[0-9]{2}-[0-9]{2}'
hms= '[0-9]{2}:[0-9]{2}:[0-9]{2}'
bbb= '[01]?[0-9][0-9]'
nn= '[0-9][0-9]?'

patterns_datetime= (
	re.compile(f'^({ymd}T{hms}Z?)$'),
	re.compile(f'^({ymd}T{hms}Z?)A({hms})$')
)

patterns_recurringtime= (
	re.compile(f'^W({bbb})/T({hms})$'),
	re.compile(f'^W({bbb})/T({hms})A({hms})')
)

patterns_intervals= (
	re.compile(f'^T({hms})/T({hms})$'),
	re.compile(f'^W({bbb})/T({hms})/T({hms})$')
)

patterns_timers= (
	re.compile(f'^PT({hms})$'),
	re.compile(f'^PT({hms})A({hms})$')
)

patterns_recurringtimers= (
	re.compile(f'^R({nn})?/PT({hms})$'),
	re.compile(f'^R({nn})?/PT({hms})A({hms})$')
)

#============================================================================
# Take a Hue time spec, match it against the possible time patterns, and
# return an object that's associated with the pattern (HueDateTime, 
# HueRecurringTime, etc.)
#============================================================================

def parse_timespec(s):
	for regex in patterns_datetime:
		matches= regex.match(s)
		if matches:
			groups= list(matches.groups())
			return HueDateTime(*groups)

	for regex in patterns_recurringtime:
		matches= regex.match(s)
		if matches:
			groups= list(matches.groups())
			return HueRecurringTime(*groups)

	for regex in patterns_intervals:
		matches= regex.match(s)
		if matches:
			groups= list(matches.groups())
			return HueTimeInterval(*groups)

	for regex in patterns_timers:
		matches= regex.match(s)
		if matches:
			groups= list(matches.groups())
			return HueTimer(*groups)

	for regex in patterns_recurringtimers:
		matches= regex.match(s)
		if matches:
			groups= list(matches.groups())
			return HueRecurringTimer(*groups)


# Convert the bbb spec, which is effectively a bitmask of days 0-7, to a
# list of day numbers (0-7)

def dayspec_to_list(spec):
	days= list()
	dayspec= int(spec)
	if dayspec < 1 or dayspec > 0b1111111:
		raise ValueError(dayspec)

	for i in range(0,7):
		if (0b1 << i) & dayspec:
			days.append(i)

	return days

# Turn a list of numbers e.g. 1,2,3,5,6 into a list of ranges (1-3, 5-6)

def day_ranges(days):
	groupings= list()
	keys= dict()
	for i, x in enumerate(days):
		keys[x]= i-x

	for k, g in itertools.groupby(days, lambda x: keys[x]):
		lg= list(g)
		groupings.append((lg[0], lg[-1]))

	return groupings

#============================================================================
# HueDateTime: Representing an alarm for a specific day and time.
#============================================================================

class HueDateTime:
	def __init__(self, *args, **kwargs):
		self.time= None
		self.random= None

		if len(args) < 1 or len(args) > 2:
			raise(ValueError)

		self.time= parse_datetime(args[0])

		if len(args) == 2:
			self.random= parse_time(args[1])

	def __str__(self):
		s= '<HueDateTime> '+self.time.strftime('%a %b %d %Y at %H:%M:%S')
		if self.random:
			s+= ' randomized by '+self.random.strftime('%H:%M:%S')
		return s

	def __eq__(self, arg):
		if arg is None:
			return False

		return self.time == arg.time

	def __lt__(self, arg):
		if arg is None:
			return False
		return self.time < arg.time

	def __gt__(self, arg):
		if arg is None:
			return True
		return self.time > arg.time

	def __le__(self, arg):
		if arg is None:
			return False
		return self.time <= arg.time

	def __ge__(self, arg):
		if arg is None:
			return True
		return self.time >= arg.time

	# NOTE: This ignores the randomized time

	def strftime(self, fmt):
		return self.time.strftime(fmt)

#============================================================================
# HueRecurringTime: An alarm the triggers on given days at the specified
# time.
#============================================================================

class HueRecurringTime:
	def __init__(self, *args, **kwargs):
		self.days= list()
		self.time= None
		self.random= None

		if len(args) < 2 or len(args) > 3:
			raise(ValueError)

		self.days= dayspec_to_list(args[0])

		self.time= parse_time(args[1])

		if len(args) == 3:
			self.random= parse_time(args[2])

	def __str__(self):
		s= '<HueRecurringTime> Every '
		if len(self.days) == 7:
			s+= 'day'
		else:
			ranges= list()
			for r in day_ranges(self.days):
				if r[0] == r[1]:
					ranges.append(calendar.day_abbr[r[0]])
				else:
					ranges.append('-'.join(
						list(map(lambda x: calendar.day_abbr[x], r))
					))
			s+= ','.join(ranges)

		s+= ' at '+self.time.strftime('%H:%M:%S')
		if self.random:
			s+= ' randomized by ' + self.random.strftime('%H:%M:%S')

		return s

#============================================================================
# HueDateTime: Time intervals, which can include specific days of the week.
#============================================================================

class HueTimeInterval:
	def __init__(self, *args, **kwargs):
		self.start= None
		self.end= None
		self.days= None
		i= 0

		if len(args) < 2 or len(args) > 3:
			raise(ValueError)

		if len(args) == 3:
			self.days= dayspec_to_list(args[i])
			i+= 1

		self.start= parse_time(args[i])
		self.end= parse_time(args[i+1])

	def __str__(self):
		s= '<HueTimeInterval> '

		if self.days is not None:
			s+= 'Every '
			if len(self.days) == 7:
				s+= 'day'
			else:
				ranges= list()
				for r in day_ranges(self.days):
					if r[0] == r[1]:
						ranges.append(calendar.day_abbr[r[0]])
					else:
						ranges.append('-'.join(
							list(map(lambda x: calendar.day_abbr[x], r))
						))
				s+= ','.join(ranges)
			s+= ' between'
		else:
			s+= 'Between'

		s+= ' {:s} and {:s}'.format(self.start.strftime('%H:%M:%S'),
			self.end.strftime('%H:%M:%S'))

		return s

#============================================================================
# HueTimer: A timer that expires after the given span 
#============================================================================


class HueTimer:
	def __init__(self, *args, **kwargs):
		self.duration= None
		self.random= None

		if len(args) < 1 or len(args) > 2:
			raise ValueError

		self.duration= parse_time(args[0])

		if len(args) == 2:
			self.random= parse_time(args[1])

	def __str__(self):
		s= '<HueTimer> Duration '+self.duration.strftime('%H:%M:%S')
		if self.random:
			s+= ' randomized by '+self.random.strftime('%H:%M:%S')

		return s

#============================================================================
# HueRecurringTimer: A recurring timer that repeats N times
#============================================================================

class HueRecurringTimer(HueTimer):
	def __init__(self, *args, **kwargs):
		self.repeat= None
		
		if len(args) < 1 or len(args) > 3:
			raise ValueError

		super().__init__(*args[1:])

		if args[0] is not None:
			self.repeat= int(args[0])

	def __str__(self):
		s= '<HueRecurringTimer> Duration '+self.duration.strftime('%H:%M:%S')
		if self.random:
			s+= ' randomized by '+self.random.strftime('%H:%M:%S')
		if self.repeat is None:
			s+= ' repeating indefinitely'
		else:
			s+= f' repeating {self.repeat} times'

		return s

