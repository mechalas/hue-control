from huectl.time import parse_timespec
from isodate import parse_datetime

# HueAction: Actions taken as a result of a HueSchedule or HueRule

class HueAction:
	@staticmethod
	def parse_definition(obj, parent=None):
		if isinstance(obj, str):
			data= json.loads(obj)
		elif isinstance(obj, dict):
			data= obj
		else:
			raise TypeError('obj: expected dict or str, not '+str(type(obj)))
		
		act= HueAction(parent)

		act.address= data['address']
		act.method= data['method']
		act.body= data['body']

		path= act.address.split('/')
		if path[1] == 'api':
			act.user= path[2]
			idx= 3
		else:
			idx= 1

		act.short_address= '/'.join(path[idx:])
		act._target_type= path[idx]
		act._target_id= path[idx+1]

		return act

	# Constructor
	#----------------------------------------

	def __init__(self, parent, obj=None):
		self.parent= parent

		self.user= None
		self.address= None
		self.short_address= None
		self.method= None
		self.body= None
		self._target_type= None
		self._target_id= None

	def __str__(self):
		return f'<HueAction> {self.short_address} {self.body}'

	def target_type(self):
		return self._target_type

	def target_id(self):
		return self._target_id

