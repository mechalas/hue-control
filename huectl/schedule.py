from huectl.time import parse_timespec
from isodate import parse_datetime

class HueCommand:
	def __init__(self, schedule, obj=None):
		self.schedule= schedule

		self.address= None
		self.method= None
		self.body= None

		if obj is None:
			return

		if isinstance(obj, str):
			d= json.loads(obj)
			self._load(d)
		elif isinstance(obj, dict):
			self._load(obj)
		else:
			raise TypeError	

	def __str__(self):
		return '<HueCommand>'

	def _load(self, data):
		self.address= data['address']
		self.method= data['method']
		self.body= data['body']

	def target(self):
		comp= self.address.split('/')
		objtype= comp[3]
		objid= comp[4]
		bridge= self.schedule.bridge

		if objtype == 'groups':
			return bridge.get_group(objid)
		elif objtype == 'lights':
			return bridge.get_light(objid)
		elif objtype == 'sensors':
			return bridge.get_sensor(objid)
		elif objtype == 'schedules':
			return bridge.get_schedule(objid)

class HueScheduleStatus:
	Enabled= 'enabled'
	Disabled= 'disabled'

class HueSchedule:
	def __init__(self, schedid=None, bridge=None, obj=None):
		if bridge is None:
			raise ValueError('bridge cannot be None')

		self.bridge= bridge

		self.id= schedid
		self.name= 'unnamed schedule'
		self.description= None
		self.localtime= None
		self.autodelete= True
		self.status= HueScheduleStatus.Enabled
		self.autodelete= False
		self.recycle= False
		self.start_time= None
		self.created= None

		if obj is None:
			return

		if isinstance(obj, str):
			d= json.loads(obj)
			self.load(d)
		elif isinstance(obj, dict):
			self.load(obj)
		else:
			raise TypeError

	def __str__(self):
		return f'<HueSchedule> {self.id} {self.name} {self.status} {self.localtime}'

	def load(self, data):
		if not isinstance(data, dict):
			raise TypeError

		# Optional attrs

		if 'name' in data:
			self.name= data['name']
		if 'description' in data:
			self.description= data['description']
		if 'starttime' in data:
			self.starttime= parse_datetime(data['created'])
		if 'autodelete' in data:
			self.autodelete= data['autodelete']
		if 'status' in data:
			self.status= data['status']

		# Deprecated

		if 'time' in data:
			self.localtime= parse_timespec(data['time'])

		# Required

		if 'localtime' in data:
			self.localtime= parse_timespec(data['localtime'])

		self.created= parse_datetime(data['created'])
		self.command= HueCommand(self, data['command'])

