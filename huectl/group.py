from huectl.color import HueColorPointxy, HueColorPointHS, HueColorTemp
from huectl.container import HueContainer
from huectl.light import HueLight, HueLightState, HueLightStateChange
from huectl.sensor import HueSensor
from huectl.version import HueApiVersion

class HueGroupType:
	Luminaire= "Luminaire"
	Lightsource= "Lightsource"
	LightGroup= "LightGroup"
	Room= "Room"
	Entertainment= "Entertainment"
	Zone= "Zone"

	_supported= {
		Luminaire: HueApiVersion('1.4'),
		Lightsource: HueApiVersion('1.4'),
		LightGroup: HueApiVersion('1.4'),
		Room: HueApiVersion('1.11'),
		Entertainment: HueApiVersion('1.22'),
		Zone: HueApiVersion('1.30')
	}

	@classmethod
	def supported(cls, gtype, version):
		if HueGroupType._supported[gtype] <= version:
			return True

		return False

class HueRoom:
	LivingRoom= 'Living Room'
	Kitchen= 'Kitchen'
	Dining= 'Dining'
	Bedroom= 'Bedroom'
	KidsBedroom= 'Kids bedroom'
	Nursery= 'Nursery'
	Recreation= 'Recreation'
	Office= 'Office'
	Gym= 'Gym'
	Hallway= 'Hallway'
	Toilet= 'Toilet'
	FrontDoor= 'Front door'
	Garage= 'Garage'
	Terrace= 'Terrace'
	Garden= 'Garden'
	Driveway= 'Driveway'
	Carport= 'Carport'
	Other= 'Other'

	Home= 'Home'
	Downstairs= 'Downstairs'
	Upstairs= 'Upstairs'
	TopFloor= 'Top floor'
	Attic= 'Attic'
	GuestRoom= 'Guest room'
	Staircase= 'Staircase'
	Lounge= 'Lounge'
	ManCave= 'Man cave'
	Computer= 'Computer'
	Studio= 'Studio'
	Music= 'Music'
	TV= 'TV'
	Reading= 'Reading'
	Closet= 'Closet'
	Storage= 'Storage'
	LaundryRoom= 'Laundry room'
	Balcony= 'Balcony'
	Porch= 'Porch'
	Barbecue= 'Barbecue'
	Pool= 'Pool'

	_supported= {
		LivingRoom: HueApiVersion('1.11'),
		Kitchen: HueApiVersion('1.11'),
		Dining: HueApiVersion('1.11'),
		Bedroom: HueApiVersion('1.11'),
		KidsBedroom: HueApiVersion('1.11'),
		Nursery: HueApiVersion('1.11'),
		Recreation: HueApiVersion('1.11'),
		Office: HueApiVersion('1.11'),
		Gym: HueApiVersion('1.11'),
		Hallway: HueApiVersion('1.11'),
		Toilet: HueApiVersion('1.11'),
		FrontDoor: HueApiVersion('1.11'),
		Garage: HueApiVersion('1.11'),
		Terrace: HueApiVersion('1.11'),
		Garden: HueApiVersion('1.11'),
		Driveway: HueApiVersion('1.11'),
		Carport: HueApiVersion('1.11'),
		Other: HueApiVersion('1.11'),
		Home: HueApiVersion('1.30'),
		Downstairs: HueApiVersion('1.30'),
		Upstairs: HueApiVersion('1.30'),
		TopFloor: HueApiVersion('1.30'),
		Attic: HueApiVersion('1.30'),
		GuestRoom: HueApiVersion('1.30'),
		Staircase: HueApiVersion('1.30'),
		Lounge: HueApiVersion('1.30'),
		ManCave: HueApiVersion('1.30'),
		Computer: HueApiVersion('1.30'),
		Studio: HueApiVersion('1.30'),
		Music: HueApiVersion('1.30'),
		TV: HueApiVersion('1.30'),
		Reading: HueApiVersion('1.30'),
		Closet: HueApiVersion('1.30'),
		Storage: HueApiVersion('1.30'),
		LaundryRoom: HueApiVersion('1.30'),
		Balcony: HueApiVersion('1.30'),
		Porch: HueApiVersion('1.30'),
		Barbecue: HueApiVersion('1.30'),
		Pool: HueApiVersion('1.30')
	}

	@classmethod
	def supported(cls, room, version):
		if HueRoom._supported[room] <= version:
			return True

		return False

#============================================================================
# Hue Groups
#============================================================================

class HueGroupAction:
	def __init__(self, obj):
		# Not all groups have all fields
		self.on= None
		self.bri= None
		self.hue= None
		self.sat= None
		self.effect= None
		self.xy= None
		self.ct= None
		self.alert= None
		self.colormode= None

		if not isinstance(obj, dict):
			raise TypeError

		if 'on' in obj:
			self.on= obj['on']
		if 'bri' in obj:
			self.bri= obj['bri']
		if 'hue' in obj:
			self.hs= HueColorPointHS(obj['hue']*360.0/65535.0, obj['sat']/254.0)
			self.xy= HueColorPointxy(obj['xy'])
		if 'effect' in obj:
			self.effect= obj['effect']
		if 'ct' in obj:
			self.ct= HueColorTemp(obj['ct'])
		if 'alert' in obj:
			self.alert= obj['alert']
		if 'colormode' in obj:
			self.colormode= obj['colormode']

class HueGroup(HueContainer):
	def __init__(self, groupid=None, bridge=None):
		super().__init__()

		if bridge is None:
			raise ValueError('bridge cannot be None')
		self.bridge= bridge

		self.id= groupid

		apiver= self.bridge.api_version()

		self.name= None
		if apiver >= '1.4':
			self.type= None
		self.action= None

		self.all_on= None
		self.any_on= None
		self.modelid= None
		self.uniqueid= None
		self.room_class= None
		self.add_collection('lights', HueLight)

		if apiver >= '1.12':
			self.state= None
			self.recycle= None

		if apiver >= '1.27':
			self.add_collection('sensors', HueSensor)
			self.presence= None

		if apiver >= '1.28':
			self.lightlevel= None

	def __str__(self):
		s= f'<HueGroup> {self.id} {self.name}, {self.type}'
		light_ids= self.lights.keys()
		if len(light_ids):
			slights= str(light_ids)
			s+= f', lights {slights}'

#		if self._allows_sensors:
#			ssensors= self._id_list(self.sensors, self.missing_sensors)
#			if len(ssesnsors):
#				s+= ', sensors {ssensors}'

		return s


	# Load from JSON or a dict. Optionally supply a cache of
	# light and sensor definitions to map light and sensor ID's
	# to the appropriate objects. 
	#
	# Unknown object id's will need to be fetched from the bridge
	# later.

	def load(self, obj, lights=None, sensors=None):
		if isinstance(obj, str):
			d= json.loads(obj)
		elif isinstance(obj, dict):
			d= obj
		else:
			raise TypeError

		self.name= d['name']
		self.recycle= d['recycle']

		self.type= d['type']

		self.lights.update_fromkeys(d['lights'])
		self.sensors.update_fromkeys(d['sensors'])
		if 'class' in d:
			self.room_class= d['class']
		self.all_on= d['state']['all_on']
		self.any_on= d['state']['any_on']

		if 'action' in d:
			self.action= HueLightState(d['action'])

		if self.lights.unresolved_items() and lights is not None:
			self.lights.resolve_items(lights)

		if self.sensors.unresolved_items() and sensors is not None:
			self.sensors.resolve_items(sensors)

	# Rename a group

	def rename(self, name):
		try:
			self.bridge.set_group_attributes(self.id, name=name)
			# Update our local name on success
			self.__dict__['name']= name
		except Exception as e:
			raise(e)

	# Add, remove, or set the lights in a group. Only do the update
	# on the bridge if something actually changes.

	def add_lights(self, lights):
		oldobj= self.lights.clone()

		if self.lights.update(dict(map(lambda x: (x.id, x), lights))):
			self._update_lights(oldobj)

	def add_lights_byid(self, lightids):
		oldobj= self.lights.clone()

		if self.lights.update_fromkeys(lightids):
			self._update_lights(oldobj)

	def set_lights(self, lights):
		oldobj= self.lights.clone()
	
		self.lights.clear()
		if self.lights.update(dict(map(lambda x: (x.id, x), lights))):
			self._update_lights(oldobj)

	def set_lights_byid(self, lightids):
		oldobj= self.lights.clone()

		self.lights.clear()
		if self.lights.update_fromkeys(lightids):
			self._update_lights(oldobj)

	def del_lights(self, lights):
		oldobj= self.lights.clone()

		if self.del_lights_byid(list(map(lambda x: x.id, lights))):
			self._update_lights(oldobj)

	def del_lights_byid(self, lightids):
		oldobj= self.lights.clone()

		status= False
		for lightid in lightids:
			if self.lights.remove(lightid):
				status= True
		
		if status:
			self._update_lights(oldobj)

	def _update_lights(self, oldlights):
		# Revert if there's a failure
		try:
			self.bridge.set_group_attributes(self.id,
				lights=self.lights.keys(unresolved=True))
		except Exception as e:
			self.lights= oldlights
			raise(e)

