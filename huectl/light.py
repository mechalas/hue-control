import huectl.exception
from huectl.color import HueColorxyY, HueColorHSB, HueColorPointxy, HueColorPointHS, HueColorGamut, HueColorTemp
import json

class HueAlertEffect:
	NoAlert= "none"
	Select= "select"
	LSelect= "lselect"

class HueDynamicEffect:
	NoEffect= "none"
	ColorLoop= "colorloop"

class HueColorMode:
	HSB= 'hsb'
	xyY= 'xy'
	CT= 'ct'
	# A dummy mode that doesn't exist but we need something to separate
	# white lights from the Hue Outlet.
	Light= '__brightness_only__'

#============================================================================
# Defines a light's capabilities.
#============================================================================

class HueLightCapabilities:
	def __init__(self, obj):
		self.colormodes= set()
		self.ct= None
		self.colorgamut= None
		self.maxlumen= None
		self.mindimlevel= None

		if isinstance(obj, str):
			d= json.loads(obj)
			self._load(d)
		elif isinstance(obj, dict):
			self._load(obj)
		else:
			raise TypeError

	def __str__(self):
		cmodes= str(self.colormodes)
		return f'<HueLightCapabilities> {cmodes}'

	def _load(self, data):
		ctl= data['control']

		# Bulb supports color temperature (e.g. White Ambiance)
		if 'ct' in ctl:
			d= ctl['ct']
			self.ct= (d['min'], d['max'])
			self.colormodes.add(HueColorMode.CT)

		# Bulb supports color
		if 'colorgamut' in ctl:
			self.colormodes.add(HueColorMode.xyY)
			self.colormodes.add(HueColorMode.HSB)
			self.colorgamut= HueColorGamut(ctl['colorgamut'])

		# It's a bulb (and not, say, an outlet switch) and can 
		# emit light.
		if 'maxlumen' in ctl:
			self.colormodes.add(HueColorMode.Light)
			self.maxlumen= ctl['maxlumen']
			self.mindimlevel= ctl['mindimlevel']

class HueState:
	def __init__(self):
		self.on= False
		self.bri= None
		self.hs= None
		self.xy= None
		self.ct= None
		self.alert= HueAlertEffect.NoAlert
		self.effect= HueDynamicEffect.NoEffect
		self.colormode= None

	def colortemp(self):
		return self.ct

	def color(self):
		if self.colormode == HueColorMode.xyY:
			return HueColorxyY(self.xy, self.bri/254.0)
		else:
			return HueColorHSB(self.hs, self.bri/254.0)

class HueLightPreset(HueState):
	def __init__(self, obj):
		super().__init__()

		self.transitiontime= 0

		if not isinstance(obj, dict):
			raise TypeError

		self.colormode= HueColorMode.Light

		if 'on' in obj:
			self.on= obj['on']

		if 'effect' in obj:
			self.effect= obj['effect']

		if 'transitiontime' in obj:
			self.transitiontime= obj['transitiontime']

		if 'bri' in obj:
			self.bri= obj['bri']

		if 'ct' in obj:
			self.ct= HueColorTemp(obj['ct'])
			self.colormode= HueColorMode.CT
		elif 'xy' in obj:
			self.xy= HueColorPointxy(obj['xy'])
			self.colormode= HueColorMode.xyY
		elif 'hue' in obj:
			self.colormode= HueColorMode.HSB
			self.hs= HueColorPointHS(obj['hue']*360.0/65535.0,
				obj['sat']/254.0)

	def __str__(self):
		on= 'Off'
		if self.on:
			on= 'On'

		s= f'<HueLightState> {on}'
		if not self.on:
			return s

		s+= f' bri={self.bri}'

		if self.colormode == HueColorMode.CT:
			ct= self.colortemp()
			s+= f' {ct}'
		elif self.colormode in (HueColorMode.xyY, HueColorMode.HSB):
			color= self.color()
			s+= f' {color}'

		return s

class HueLightState(HueState):
	def __init__(self, obj):
		super().__init__()
		self.colormode= None
		self.mode= None
		self.reachable= False

		if not isinstance(obj, dict):
			raise TypeError

		self.on= obj['on']
		if 'bri' in obj:
			self.bri= obj['bri']

		if 'hue' in obj:
			self.hs= HueColorPointHS(obj['hue']*360.0/65535.0,
				obj['sat']/254.0)
		if 'xy' in obj:
			self.xy= HueColorPointxy(obj['xy'])

		if 'effect' in obj:
			self.effect= obj['effect']

		if 'ct' in obj:
			self.ct= HueColorTemp(obj['ct'])

		if 'colormode' in obj:
			self.colormode= obj['colormode']

		if 'alert' in obj:
			self.alert= obj['alert']

		if 'mode' in obj:
			self.mode= obj['mode']

		if 'reachable' in obj:
			self.reachable= obj['reachable']

	def __str__(self):
		if not self.reachable:
			return '<HueLightState> unreachable'

		if self.on:
			onoff= 'on'
		else:
			onoff= 'off'

		if self.colormode in (HueColorMode.xyY, HueColorMode.HSB):
			c= self.color()
			return f'<HueLightState> {onoff} {c}'
		elif self.colormode == HueColorMode.CT:
			ct= self.colortemp()
			return f'<HueLightState> {onoff} {ct}'

		return f'<HueLightState> {onoff}'


class HueLightStateChange(HueLightState):
	def __init__(self):
		super().__init__()
		self.transitiontime= None
		self.bri_inc= None
		self.sat_inc= None
		self.hue_inc= None
		self.ct_inc= None
		self.xy_inc= None

#----------------------------------------------------------------------------
# A Hue light
#
# These objects should not generally be created by user applications. The
# definitions come from the bridge. Note that a "light" can also include 
# items that are not specifically lights such as outlet adapters (e.g.
# the Hue Smart Plug)
#----------------------------------------------------------------------------

class HueLight:
	def __init__(self, obj, lightid=None, bridge=None):
		if bridge is None:
			raise ValueError('bridge cannot be None')

		self.bridge= bridge
		self.id= lightid
		self.name= None
		self.type= None
		self.modelid= None
		self.uniqueid= None
		self.manufacturername= None
		self.productname= None
		self.luminaireuniqueid= None
		self.swversion= None
		self.swconfigid= None
		self.productid= None
		self.capabilities= dict()
		self.config= dict()
		self.lightstate= None

		if isinstance(obj, str):
			data= json.loads(obj)
			self._load(data)
		elif isinstance(obj, dict):
			self._load(obj)
		elif isinstance(obj, HueLight):
			pass
		else:
			raise TypeError

	def __str__(self):
		return f'<HueLight> {self.id} {self.name}, {self.productname}, {self.lightstate}'

	def _load(self, data):
		self.name= data['name']
		self.type= data['type']
		self.modelid= data['modelid']
		self.uniqueid= data['uniqueid']
		self.manufacturername= data['manufacturername']
		self.productname= data['productname']
		self.swversion= data['swversion']
		if 'luminaireuniqueid' in data:
			self.self.luminaireuniqueid= data['luminaireuniqueid']

		self.config= data['config']

		# Load capabilities before state since the latter needs the former
		self.capabilities= HueLightCapabilities(data['capabilities'])
		self.lightstate= HueLightState(data['state'])
		
	def islight(self):
		if HueColorMode.Light in self.capabilities.colormodes:
			return True

		return False

	def hascolor(self):
		if HueColorMode.HSB in self.capabilities.colormodes:
			return True

		if HueColorMode.xyY in self.capabilities.colormodes:
			return True

		return False

	def hascolortemp(self):
		if HueColorMode.CT in self.capabilities.colormodes:
			return True

		return False

	def gamut(self):
		return self.capabilities.colorgamut()


