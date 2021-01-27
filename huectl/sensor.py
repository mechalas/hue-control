import huectl.exception
import json

#============================================================================
# Hue sensors. These are generally not created directly by the user
# application and are instead read from the bridge.
#============================================================================

class HueSensor:
	def __init__(self, obj, sensorid=None, bridge=None):
		self.bridge= bridge
		self.id= sensorid
		self.name= None
		self.type= None
		self.modelid= None
		self.manufacturername= None
		self.swversion= None
		self.uniqueid= None
		self.recycle= False
		self.state= {}
		self.config= {}
		self.capabilities= {}

		if isinstance(obj, str):
			data= json.loads(obj)
			self._load(data)
		elif isinstance(obj, dict):
			self._load(obj)
		else:
			raise TypeError

	def __str__(self):
		return f'<HueSensor> {self.id} {self.name}, {self.type}'
	
	def _load(self, data):
		self.name= data['name']
		self.type= data['type']
		self.modelid= data['modelid']
		self.manufacturername= data['manufacturername']

		if 'swversion' in data:
			self.swversion= data['swversion']

		if 'uniqueid' in data:
			self.uniqueid= data['uniqueid']

		if 'recycle' in data:
			self.recycle= data['recycle']

		if 'config' in data:
			self.config= data['config']

		if 'state' in data:
			self.state= data['state']

		if 'capabilities' in data:
			self.capabilities= data['capabilities']

