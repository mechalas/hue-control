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

		for attr in ('name', 'owner', 'type', 'group', 'recycle', 'locked',
			'appdata', 'picture', 'version', 'image', 'transitiontime'):
			if attr in d:
				scene.__dict__[attr]= d[attr]

		if 'lastupdated' in d:
			if d['lastupdated'] is not None:
				scene.lastupdated= HueDateTime(d['lastupdated'])

		# Add a 'lights' container
		scene.lights.update_fromkeys(d['lights'])

		# Add a 'lightstates' container if we have light states
		if 'lightstates' in d:
			if len(d['lightstates']):
				lstates= dict()
				scene._has_lightstates= True
				for lightid, sdata in d['lightstates'].items():
					lstates[lightid]= HueLightPreset(sdata)

				scene.lightstates.update(lstates)

		return scene

	def __init__(self, bridge, groupid=None, name=None, recycle=False, scenetype=HueSceneType.LightScene):
		super().__init__()

		if not isinstance(bridge, huectl.bridge.HueBridge):
			raise ValueError('bridge: expected HueBridge, not '+str(type(bridge)))
		self.bridge= bridge

		self.name= name
		self.id= None
		self.transitiontime= None
		self._has_lightstates= False

		# API 1.11
		self.owner= None
		self.recycle= recycle
		self.locked= False
		self.appdata= {}
		self.picture= None
		self.lastupdated= None
		self.version= None

		# API 1.28
		self.group= groupid
		if groupid is None:
			self.type= scenetype
		else:
			if self.type != None and self.type != HueSceneType.GroupScene:
				raise ValueError("Scenes with group association must be type GroupScene")
			self.type= HueSceneType.GroupScene

		# API 1.36
		self.image= None

		# Scenes support lights but not sensors
		#self.add_collection('lights', HueLight)
		#self.add_collection('lightstates', HueLightPreset)
		self.add_collection('lights')
		self.add_collection('lightstates')


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

	#----------------------------------------
	# Return a scene definition as a dict that is sutiable for converting to 
	# JSON for creating or modifying a scene on the bridge.
	#----------------------------------------

	def definition(self, apiver=None, tobridge=False):
		if apiver is None:
			apiver= self.bridge.api_version()

		d= {
			'name': self.name
		}
		if self.id is not None:
			d['id']= self.id

		if self.transitiontime is not None:
			d['transitiontime']= self.transitiontime

		if apiver >= '1.11':
			if self.recycle is not None:
				d['recycle']= self.recycle

			appdata= self.application_data()
			if len(appdata):
				d['appdata']= self.application_data()

		if apiver > '1.28':
			if self.group is not None:
				d['group']= self.group
			d['type']= self.type

		lightlist= self.lights.keys(unresolved=True)
		if len(lightlist):
			d['lights']= lightlist
			if self.has_presets() and apiver >= '1.29':
				ls= d['lightstates']= dict()
				for lightid, lightstate in self.lightstates.items(unresolved=True):
					ls[lightid]= lightstate.definition()

		return d

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

		# If it's an existing scene, change it on the bridge, too
		if self.id is not None:
			self.bridge.modify_scene(self.id, appdata=self.appdata)

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

		# If it's an existing scene, rename it on the bridge, too
		if self.id is not None:
			self.bridge.modify_scene(self.id, name=name)

	#----------------------------------------
	# Save the scene to the bridge. If we have a sceneid, we are doing an
	# update so send it along. Otherwise, we are asking for a new scene.
	#----------------------------------------

	def save(self):
		kwargs= dict()
		newscene= True

		if self.id is not None:
			# We have a sceneid, but it could have been supplied by the
			# user, so we need to check if we're doing a new scene or
			# replacing an existing one.

			try:
				s= self.bridge.get_scene(self.id)
				newscene= False
			except huectl.exception.ResourceUnavailable:
				# This scene id doesn't exist
				pass

		d= self.definition()

		if newscene:
			self.bridge.create_scene(d, sceneid=self.id)
		else:
			for param in ('id', 'recycle', 'type'):
				if param in d:
					del d[param]
			self.bridge.modify_scene(d, self.id)

