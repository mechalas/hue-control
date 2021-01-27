from huectl.container import HueContainer
from huectl.light import HueLight, HueLightPreset
from huectl.version import HueApiVersion
from huectl.time import HueDateTime

class HueSceneType:
	LightScene= "LightScene"
	GroupScene= "GroupScene"

class HueScene(HueContainer):
	def __init__(self, sceneid=None, bridge=None):
		super().__init__()

		if bridge is None:
			raise ValueError('bridge cannot be None')
		self.bridge= bridge

		self.name= None
		self.id= sceneid
		self.transitiontime= 0

		apiver= self.bridge.api_version()

		if apiver >= '1.11':
			self.owner= None
			self.recycle= False
			self.locked= False
			self.appdata= {}
			self.picture= None
			self.lastupdated= None
			self.version= None

		if apiver >= '1.28':
			self.group= None
			self.type= HueSceneType.LightScene

		if apiver >= '1.36':
			self.image= None

		# Scenes support lights but not sensors
		self.add_collection('lights', HueLight)
		self.add_collection('lightstates', HueLightPreset)


	def __str__(self):
		slights= 'None'
		light_ids= str(self.collections['lights'].keys(unresolved=True))
		if len(light_ids):
			slights= str(light_ids)

		group=''
		if hasattr(self, 'group'):
			if self.group is not None:
				group= f' group {self.group}'

		return f'<HueScene> {self.id} {self.name}, {self.type},{group} lights {slights}'

	def __getattr__(self, attr):
		return super().__getattr__(attr)

		if attr in self.__dict__:
			return self.__dict__[attr]

		if attr in ('owner', 'recycle', 'locked', 'appdata', 'picture',
			'lastupdated', 'version'):
			raise APIVersion(apiver, '1.11')

		if attr in ('group', 'type'):
			raise APIVersion(apiver, '1.28')

		if attr in ('image'):
			raise APIVersion(apiver, '1.36')

		raise KeyError

	def load(self, obj, lights=None):
		apiver= self.bridge.api_version()

		if isinstance(obj, str):
			d= json.loads(obj)
		elif isinstance(obj, dict):
			d= obj
		else:
			raise TypeError

		self.name= d['name']
		self.owner= d['owner']

		if 'type' in d:
			self.type= d['type']

		if 'group' in d:
			self.group= d['group']

		self.recycle= d['recycle']
		self.locked= d['locked']
		self.appdata= d['appdata']
		if 'picture' in d:
			self.picture= d['picture']
		if 'lastupdated' in d:
			if d['lastupdated'] is not None:
				self.lastupdated= HueDateTime(d['lastupdated'])
		self.version= d['version']

		if 'image' in d:
			self.image= d['image']

		self.lights.update_fromkeys(d['lights'])

		# Cross reference light id's with our cache (if provided)

		if self.lights.unresolved_items() and lights is not None:
			self.lights.resolve_items(lights)

		# Load the light states for the scene. We have to do this
		# AFTER we merge the light info, above, so we can overwrite
		# the light's last state with the scene state.

		if 'lightstates' in d:
			lstates= dict()
			for lightid, sdata in d['lightstates'].items():
				lstates[lightid]= HueLightPreset(sdata)

			self.lightstates.update(lstates)

	def light(self, lightid):
		return self.lights.item(lightid)

	def preset(self, lightid):
		try:
			return self.lightstates.item(lightid)
		except KeyError:
			return None
