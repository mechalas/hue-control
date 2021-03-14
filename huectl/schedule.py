from huectl.time import parse_timespec
from isodate import parse_datetime
from huectl.action import HueAction

class HueScheduleStatus:
	Enabled= 'enabled'
	Disabled= 'disabled'

#----------------------------------------------------------------------------
# A Hue Schedule
#----------------------------------------------------------------------------

class HueSchedule:
	@staticmethod
	def parse_definition(obj, bridge=None, scheduleid=None):
		if isinstance(obj, str):
			data= json.loads(obj)
		elif isinstance(obj, dict):
			data= obj
		else:
			raise TypeError('obj: expected str or dict not '+str(type(obj)))

		if not isinstance(scheduleid, (int, str)):
			raise TypeError('scheduleid: Expected int or str, not '+str(type(scheduleid)))

		schedule= HueSchedule(bridge)

		schedule.id= scheduleid

		# Optional attrs

		if 'name' in data:
			schedule.name= data['name']
		if 'description' in data:
			schedule.description= data['description']
		if 'starttime' in data:
			schedule.starttime= parse_datetime(data['created'])
		if 'autodelete' in data:
			schedule.autodelete= data['autodelete']
		if 'status' in data:
			schedule.status= data['status']

		# Deprecated

		if 'time' in data:
			schedule.localtime= parse_timespec(data['time'])

		# Required

		if 'localtime' in data:
			schedule.localtime= parse_timespec(data['localtime'])

		schedule.created= parse_datetime(data['created'])
		schedule.command= HueAction.parse_definition(data['command'], parent=schedule)

		return schedule

	def __init__(self, bridge):
		self.bridge= bridge

		self.id= None
		self.name= None
		self.description= None
		self.localtime= None
		self.autodelete= True
		self.status= HueScheduleStatus.Enabled
		self.autodelete= False
		self.recycle= False
		self.start_time= None
		self.created= None
		self.command= None

	def __str__(self):
		return f'<HueSchedule> {self.id} {self.name}, {self.description}, {self.status} {self.localtime}'

