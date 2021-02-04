from huectl.container import HueContainer
from huectl.light import HueLight, HueLightPreset
from huectl.version import HueApiVersion
from huectl.time import HueDateTime
import huectl.bridge

class HueSceneType:
	LightScene= "LightScene"
	GroupScene= "GroupScene"

class HueScene(HueContainer):
	@staticmethod
	def parse_definition(obj, bridge=None, sceneid=None):
		if isinstance(obj, str):
			d= json.loads(obj)
		elif isinstance(obj, dict):
			d= obj
		else:
			raise TypeError('obj: Expected str or dict, not '+str(type(obj)))


		scene= HueScene(bridge)

		# sceneid can be None

		if sceneid is not None:
			if not isinstance(sceneid, str):
				raise TypeError('sceneid: Expected str, not '+str(type(sceneid)))
			scene.id= sceneid

		scene.name= d['name']
		if 'owner' in d:
			scene.owner= d['owner']

		if 'type' in d:
			scene.type= d['type']

		if 'group' in d:
			scene.group= d['group']

		scene.recycle= d['recycle']
		scene.locked= d['locked']
		scene.appdata= d['appdata']
		if 'picture' in d:
			scene.picture= d['picture']
		if 'lastupdated' in d:
			if d['lastupdated'] is not None:
				scene.lastupdated= HueDateTime(d['lastupdated'])
		scene.version= d['version']

		if 'image' in d:
			scene.image= d['image']

		# Add a 'lights' container
		scene.lights.update_fromkeys(d['lights'])

		# Add a 'lightstates' container if we have light states
		if 'lightstates' in d:
			lstates= dict()
			scene._has_lightstates= True
			for lightid, sdata in d['lightstates'].items():
				lstates[lightid]= HueLightPreset(sdata)

			scene.lightstates.update(lstates)

		return scene

	def __init__(self, bridge):
		super().__init__()

		if not isinstance(bridge, huectl.bridge.HueBridge):
			raise ValueError('bridge: expected HueBridge, not '+str(type(bridge)))
		self.bridge= bridge

		self.name= None
		self.id= None
		self.transitiontime= None
		self._has_lightstates= False

		# API 1.11
		self.owner= None
		self.recycle= False
		self.locked= False
		self.appdata= {}
		self.picture= None
		self.lastupdated= None
		self.version= None

		# API 1.28
		self.group= None
		self.type= HueSceneType.LightScene

		# API 1.36
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

	def asdict(self, apiver=None):
		if apiver is None:
			apiver= self.bridge.api_version()

		d= {
			'id': self.id,
			'name': self.name
		}
		if self.transitiontime is not None:
			d['transitiontime']= self.transitiontime

		if apiver >= '1.11':
			d['recycle']= self.recycle
			d['appdata']= {
				self.app_data_version(),
				self.app_data_content()
			}

		if apiver > '1.28':
			if self.group is not None:
				d['group']= self.group
			d['type']= self.type

		if self.has_presets():
			ls= d['lightstates']= dict()
			for light in self.lights.values(unresolved=True):
				ls[light.id]= self.preset(light.id).asdict()
		else:
			d['lights']= self.lights.keys(unresolved=True)

	def light(self, lightid):
		return self.lights.item(lightid)

	def has_presets(self):
		return self._has_lightstates

	def preset(self, lightid):
		try:
			return self.lightstates.item(lightid)
		except KeyError:
			return None

	def application_data(self):
		return self.appdata

	def clear_application_data(self):
		self.appdata= {}

	def set_application_data(self, version=None, data=None):
		if version is None and data is None:
			return False

		if not isinstance(version, int):
			raise TypeError('version: expected int, got '+str(type(version)))

		if not isinstance(data, str):
			raise TypeError('data: expected str, got '+str(type(data)))

		if len(data) > 16:
			raise ValueError('data: max length is 16 characters')

		self.appdata= {
			'version': version,
			'data': data
		}

	def rename(self, name):
		if name is None:
			return False

		name= name.strip()

		if not len(name):
			return False

		apiver= self.bridge.api_version()

		if apiver >= '1.4':
			maxlen= 32
		else:
			maxlen= 16

		if len(name) > maxlen:
			raise ValueError(f'Max nane length is {maxlen} characters')

		self.bridge.modify_scene(self.id, name=name)

