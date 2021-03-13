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
# Hue sensor state, representing various states from standard hue sensors.
#============================================================================

class HueSensorState():
	def __init__(self, data):
		self.last_update= None
		self._state= dict()

		for attr,value in data.items():
			if attr == 'lastupdated':
				# Sensors use UTC
				self.last_update= parse_timespec(value+'Z')
			elif attr == 'lightlevel':
				self._state[attr]= HueSensorLightLevel(value)
			elif attr == 'temperature':
				self._state[attr]= HueSensorTemperature(value)
			elif attr == 'humidity':
				self._state[attr]= HueSensorHumidity(value)
			else:
				self._state[attr]= HueSensorValue(value)

	def updated(self):
		return self.last_update

	def state(self, attr):
		return self._state[attr]

	def items(self):
		return self._state.items()

class HueSensorValue():
	def __init__(self, value):
		self.value= value

# Light level stored in 10000 log10(lux+1) (note that the Hue API doc lists
# this formula incorrectly).

class HueSensorLightLevel(HueSensorValue):
	def lux(self):
		return round(pow(10, self.value/10000)-1)

# Temperature in Celsius*100

class HueSensorTemperature(HueSensorValue):
	def celsius(self):
		return float(self.value)/100

	def farenheit(self):
		return self.celsius()*9/5+32

# Humdity in val*1000

class HueSensorHumidity(HueSensorValue):
	def humidity(self):
		return float(self.value/1000)

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
			sensor.state= HueSensorState(data['state'])

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
		self.state= {}
		self.config= {}
		self.capabilities= {}
		self.children= list()
		self.parent= None

	def __str__(self):
		return f'<HueSensor> {self.id} {self.name} ({self.type})'

	def address(self):
		if self.uniqueid is None:
			return None

		return self.uniqueid[0:23]

	def is_primary(self):
		if 'primary' in self.capabilities:
			return self.capabilities['primary']

		return False

