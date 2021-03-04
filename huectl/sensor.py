import huectl.exception
from huectl.time import parse_timespec
import json

class HueSensorType:
	CLIPGenericFlag= 'CLIPGenericFlag'
	CLIPGenericStatus= 'CLIPGenericStatus'
	CLIPHumidity= 'CLIPHumidity'
	CLIPLightlevel= 'CLIPLightlevel'
	CLIPOpenClose= 'CLIPOpenClose'
	CLIPPresence= 'CLIPPresence'
	CLIPSwitch= 'CLIPSwitch'
	CLIPTemperature= 'CLIPTemperature'

	Daylight= 'Daylight'

	ZGPSwitch= 'ZGPSwitch'
	ZLLLightlevel= 'ZLLLightlevel'
	ZLLPresence= 'ZLLPresence'
	ZLLRelativeRotary= 'ZLLRelativeRotary'
	ZLLSwitch= 'ZLLSwitch'
	ZLLTemperature= 'ZLLTemperature'

#============================================================================
# Hue sensors. ZLL and ZGP sensors are created when hardware devices are
# added to the bridge. CLIP sensors are typically user-created, and store
# status information which can be set and queried by rules.
#
# Sensors can have a "primary" attribute in their capabilities structure.
# If set to "false", then this sensor is a child of a primary sensor with
# the same MAC address (the first part of the uniqueid).
#============================================================================

class HueSensor():
	@staticmethod
	def parse_definition(obj, bridge=None, sensorid=None):
		if isinstance(obj, str):
			data= json.loads(obj)
		elif isinstance(obj, dict):
			data= obj
		else:
			raise TypeError

		sensor= HueSensor(bridge)

		sensor.id= sensorid
		sensor.name= data['name']
		sensor.type= data['type']
		sensor.modelid= data['modelid']
		sensor.manufacturername= data['manufacturername']

		for attr in ( 'swversion', 'uniqueid', 'recycle', 'config', 'capabilities', 'productname', 'diversityid' ):
			if attr in data:
				sensor.__dict__[attr]= data[attr]

		if 'state' in data:
			sensor._state= data['state']

		return sensor


	def __init__(self, bridge):
		self.bridge= bridge
		self.id= None
		self.name= None
		self.type= None
		self.modelid= None
		self.manufacturername= None
		self.productname= None
		self.swversion= None
		self.uniqueid= None
		self.diversityid= None
		self.recycle= False
		self._state= {}
		self.config= {}
		self.capabilities= {}
		self.children= list()
		self.parent= None
		self._has_children= None

	def __str__(self):
		return f'<HueSensor> {self.id} {self.name} ({self.type})'

	def address(self):
		if self.uniqueid is None:
			return None

		return self.uniqueid[0:23]

	def state(self):
		if self._state is None:
			return None

		st= dict(self._state)
		if 'lastupdated' in st:
			del st['lastupdated']

		return st

	def state_updated(self):
		st= self._state
		if 'lastupdated' in self._state:
			return parse_timespec(self._state['lastupdated']+'Z')

		return None
	
	def is_primary(self):
		if 'primary' in capabilities:
			return self.capabilities['primary']

		return False

	def has_children(self):
		return self._has_children

