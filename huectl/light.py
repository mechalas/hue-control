from huectl.ro import read_only_properties as read_only
import huectl.bridge
from huectl.exception import InvalidOperation
from huectl.color import HueColor, HueColorxyY, HueColorHSB, HueColorPointxy, HueColorPointHS, HueColorGamut, HueColorTemp, kelvin_to_mired, map_range, mired_to_kelvin
import json

class HueAlertEffect:
	NoAlert= "none"
	Select= "select"
	LSelect= "lselect"

	_supported_alerts= (NoAlert, Select, LSelect)

	@staticmethod
	def supported(alert):
		return alert in HueAlertEffect._supported_alerts

class HueDynamicEffect:
	NoEffect= "none"
	ColorLoop= "colorloop"

	_supported_effects= (NoEffect, ColorLoop)

	@staticmethod
	def supported(effect):
		return effect in HueDynamicEffect._supported_effects

class HueColorMode:
	HSB= 'hs'
	xyY= 'xy'
	CT= 'ct'
	# Dummy modes that aren't reported in the 'colormode' of a light
	# but which we need internally to separate color lights from
	# dimmable white lights to on/off devices like the Hue outlet.
	Dimmable= 'bri'

class HueLightClass:
	# On/off only (e.g. Hue Smart Plug"
	OnOff= "On/Off"

	# Dimmable light (e.g. Hue White)
	Dimmable= "Dimmable"

	# Color temperature (e.g. Hue White Ambiance)
	ColorTemperature= "Color Temperature"

	# Color but no color temperature (e.g. Hue Bloom, Hue Light Strip)
	Color= "Color"

	# Color and color temperature (e.g. Hue Light Strip Plus, Hue White
	# and Color Ambiance)
	ExtendedColor= "Extended Color"

	_supported= {
		OnOff: [],
		Dimmable: [ HueColorMode.Dimmable ],
		ColorTemperature: [ HueColorMode.Dimmable, HueColorMode.CT ],
		Color: [ HueColorMode.Dimmable, HueColorMode.HSB, HueColorMode.xyY ],
		ExtendedColor: [ HueColorMode.Dimmable, HueColorMode.CT,
			HueColorMode.HSB, HueColorMode.xyY ]
	}

	@staticmethod
	def supported(lightclass):
		return set(HueLightClass._supported[lightclass])

#============================================================================
# Defines a light's capabilities.
#============================================================================

class HueLightCapabilities:
	@staticmethod
	def parse_definition(obj):
		if isinstance(obj, str):
			d= json.loads(obj)
		elif isinstance(obj, dict):
			d= obj
		else:
			raise TypeError('obj: Expected str or dict, not '+str(type(obj)))

		cap= HueLightCapabilities()

		# What kind of light is it?

		ctl= d['control']
		if 'ct' in ctl:
			if 'colorgamut' in ctl:
				cap.lightclass= HueLightClass.ExtendedColor
			else:
				cap.lightclass= HueLightClass.ColorTemperature
		elif 'colorgamut' in ctl:
			cap.lightclass= HueLightClass.Color
		elif 'maxlumen' in ctl:
			cap.lightclass= HueLightClass.Dimmable
		else:
			cap.lightclass= HueLightClass.OnOff

		cap.colormodes= HueLightClass.supported(cap.lightclass)

		# Flatten the control structure for ease of use

		if 'colorgamut' in ctl:
			cap.colorgamut= HueColorGamut(ctl['colorgamut'])

		if 'maxlumen' in ctl:
			cap.maxlumen= ctl['maxlumen']
			cap.mindimlevel= ctl['mindimlevel']

		# Flatten the streaming structure for ease of use

		if 'streaming' in d:
			cap.renderer= d['streaming']['renderer']
			cap.proxy= d['streaming']['proxy']

		cap.certified= d['certified']

		return cap

	def __init__(self):
		self.colormodes= None
		self.ct= None
		self.colorgamut= None
		self.maxlumen= None
		self.mindimlevel= None
		self.certified= None
		self.proxy= None
		self.renderer= None

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
			self.colormodes.add(HueColorMode.Dimmable)
			self.maxlumen= ctl['maxlumen']
			self.mindimlevel= ctl['mindimlevel']

#============================================================================
# HueState is the base class for a light state, but it can apply to
# a group, scene/preset, or light.
#============================================================================

class HueState:
	def __init__(self):
		self.on= False
		self.bri= None
		self.hs= None
		self.xy= None
		self.ct= None
		self.alert= None
		self.effect= None
		self.colormode= None

	def brightness(self, torange=None):
		if torange is None:
			return self.bri
		
		return map_range(self.bri, HueColor.range_bri, torange)

	def colortemp(self):
		return self.ct
	
	def kelvin(self):
		if self.colormode != HueColorMode.CT:
			raise huectl.exception.InvalidOperation('color temperature not support by light')
		return self.ct.kelvin()

	def color(self):
		if self.colormode == HueColorMode.xyY:
			return HueColorxyY(self.xy.x, self.xy.y, self.bri)
		elif self.colormode == HueColorMode.HSB:
			return HueColorHSB(self.hs.h, self.hs.s, self.bri)
		else:
			return None

#============================================================================
# HueLightPreset is a state that is stored in a scene. It is really just a
# state plus a transition time.
#============================================================================

class HueLightPreset(HueState):
	def __init__(self, obj):
		super().__init__()

		self.transitiontime= None

		if not isinstance(obj, dict):
			raise TypeError

		if 'on' in obj:
			self.on= obj['on']

		if 'effect' in obj:
			self.effect= obj['effect']

		if 'transitiontime' in obj:
			self.transitiontime= obj['transitiontime']

		if 'bri' in obj:
			# If there's a color or ct this will get overwritten.
			# If not, we're just a dimmable bulb.
			if self.color is None:
				self.colormode= HueColorMode.Dimmable
			self.bri= obj['bri']

		if 'ct' in obj:
			self.ct= HueColorTemp(obj['ct'])
			self.colormode= HueColorMode.CT
		elif 'xy' in obj:
			self.xy= HueColorPointxy(obj['xy'])
			self.colormode= HueColorMode.xyY
		elif 'hue' in obj:
			self.colormode= HueColorMode.HSB
			self.hs= HueColorPointHS(obj['hue'], obj['sat'])

	def __str__(self):
		on= 'Off'
		if self.on:
			on= 'On'

		s= f'<HueLightState> {on}'
		if not self.on:
			return s

		if self.bri is not None:
			s+= ' bri={:.4f}'.format(map_range(self.bri, HueColor.range_bri, (0,1)))

		if self.colormode == HueColorMode.CT:
			ct= self.colortemp()
			s+= f' {ct}'
		elif self.colormode in (HueColorMode.xyY, HueColorMode.HSB):
			color= self.color()
			s+= f' {color}'

		return s

	def asdict(self):
		d= dict()

		if self.on is not None:
			d['on']= self.on
		
		if self.effect is not None:
			d['effect']= self.effect
		if self.transitiontime is not None:
			d['transitiontime']= self.transitiontime

		if self.bri is not None:
			d['bri']= self.bri

		if self.hs is not None:
			d['hue']= round(self.hs.hue,4)
			d['sat']= round(self.hs.sat,4)
		elif self.ct is not None:
			d['ct']= self.ct.ct
		elif self.xy is not None:
			d['x']= round(self.xy.x,4)
			d['y']= round(self.xy.y,4)

		return d

#============================================================================
# HueLightState defines a light's current state, which includes some
# additional information such as its reachability and active mode.
#============================================================================

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
			self.hs= HueColorPointHS(obj['hue'], obj['sat'])
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

		if not self.on:
			return '<HueLightState> off'

		if self.colormode in (HueColorMode.xyY, HueColorMode.HSB):
			c= self.color()
			return f'<HueLightState> on {c}'
		elif self.colormode == HueColorMode.CT:
			ct= self.colortemp()
			return f'<HueLightState> on {ct}'

		return f'<HueLightState> on {self.colormode}'


#============================================================================
# HueLightStateChange: A light state change requested by the user.
#                      Hue/Sat/Bri values are in user-convenient ranges
#                      rather than "bridge" units:
#                        0 <= Hue <= 360
#                        0 <= Sat <= 1
#                        0 <= Bri <= 1
#============================================================================

class HueLightStateChange:
	# Multiple color mode changes can be specified. The bridge will
	# change all of them, but the final color mode of the light is
	# set based on the bridge's internal priority (xy > ct > hs)

	def __init__(self):
		self.change= dict()

	def set_transition_time(self, ms):
		if ms < 0 or ms > 65535:
			raise ValueError(f'Transition time {ms} out of range')

		self.change['transitiontime']= round(ms)

	def set_power(self, state):
		self.change['on']= state
		
	def set_brightness(self, bri):
		if bri < 0 or bri > 1:
			raise ValueError(f'Brightness {bri} out of range')

		self.change['bri']= round(map_range(bri, (0,1), HueColor.range_bri))
		if 'bri_inc' in self.change:
			del self.change['bri_inc']

	def inc_brightness(self, bri):
		if bri < -1 or bri > 1:
			raise ValueError(f'Brightness delta {bri} out of range')

		bmax= HueColor.range_bri[1]
		self.change['bri_inc']= round(map_range(bri, (-1,1), (-bmax,bmax)))
		if 'bri' in self.change:
			del self.change['bri']

	def set_cct(self, cct):
		return self.set_ct(round(kelvin_to_mired(cct)))

	def inc_cct(self, cct):
		if cct == 0:
			return self.inc_ct(0)

		return self.inc_ct(round(kelvin_to_mired(cct)))

	def set_ct(self, ct):
		if ct < 153 or ct > 500:
			raise ValueError(f'Mired color temperature {ct} out of range')

		self.change['ct']= ct
		if 'ct_inc' in self.change:
			del self.change['ct_inc']

	def inc_ct(self, ct):
		if ct < -347 or ct > 347:
			raise ValueError(f'Mired color temperature delta {ct} out of range')

		self.change['ct_inc']= ct
		if 'ct' in self.change:
			del self.change['ct']

	def set_xy(self, xy):
		if not isinstance(xy, (list, tuple)):
			raise TypeError(f'xy must be tuple or list')
		if len(xy) != 2:
			raise ValueError(f'xy must be coordinate pair')

		x,y = xy

		if x < 0 or x > 1:
			raise ValueError(f'x coordinate must be between 0 and 1')

		if y < 0 or y > 1:
			raise ValueError(f'y coordinate must be between 0 and 1')

		self.change['xy']= [ round(x,4), round(y,4) ]

	def inc_xy(self, xy):
		if not isinstance(xy, (list, tuple)):
			raise TypeError(f'xy must be tuple or list')
		if len(xy) != 2:
			raise ValueError(f'xy must be increment pair')

		x,y = xy

		if x < -0.5 or x > 0.5:
			raise ValueError(f'x increment must be between -0.5 and 0.5')

		if y < -0.5 or y > 0.5:
			raise ValueError(f'y increment must be between -0.5 and 0.5')

		self.change['xy_inc']= [ round(x,4), round(y,4) ]

	def set_hue(self, hue):
		if hue < 0 or hue > 360:
			raise ValueError(f'Hue {hue} out of range')

		self.change['hue']= round(map_range(hue, (0,360), HueColorHSB.range_hue))
		if 'hue_inc' in self.change:
			del self.change['hue_inc']

	def inc_hue(self, hue):
		if hue < -360 or hue > 360:
			raise ValueError(f'Hue {hue} out of range')

		hmax= HueColorHSB.range_hue[1]
		self.change['hue_inc']= round(map_range(hue, (-360,360), (-hmax,hmax)))
		if 'hue' in self.change:
			del self.change['hue']

	def set_sat(self, sat):
		if sat < 0 or sat > 254:
			raise ValueError(f'Saturation {sat} out of range')

		self.change['sat']= round(map_range(sat, (0,1), HueColorHSB.range_sat))
		if 'sat_inc' in self.change:
			del self.change['sat_inc']

	def inc_sat(self, sat):
		if sat < -1 or sat > 1:
			raise ValueError(f'Saturation {sat} out of range')

		smax= HueColorHSB.range_sat[1]
		self.change['sat_inc']= round(map_range(sat, (-1,1), (-smax,smax)))
		if 'sat' in self.change:
			del self.change['sat']

	def set_alert(self, alert):
		if not HueAlertEffect.supported(alert):
			raise ValueError(f'Unknown alert mode {alert}')

		self.change['alert']= alert

	def set_dynamic_effect(self, effect):
		if not HueDynamicEffect.supported(effect):
			raise ValueError(f'Unknown dynamic effect {effect}')

		self.change['effect']= effect

	def asdict(self):
		return self.change

	def __str__(self):
		return json.dumps(self.change)

#============================================================================
# A Hue light
#
# These objects should not generally be created by user applications. The
# definitions come from the bridge. Note that a "light" can also include 
# items that are not specifically lights such as outlet adapters (e.g.
# the Hue Smart Plug)
#============================================================================

@read_only('id',
	'bridge',
	'name',
	'manufacturername',
	'modelid',
	'name',
	'productid',
	'productname',
	'swconfigid',
	'swversion',
	'type',
	'uniqueid',
	'luminaireuniqueid',
	'capabilities',
	'config'
)
class HueLight(object):
	top_attrs= (
		'manufacturername',
		'modelid',
		'name',
		'productid',
		'productname',
		'swconfigid',
		'swversion',
		'type',
		'uniqueid'
	)

	@staticmethod
	def parse_definition(obj, bridge=None, lightid=None):
		if isinstance(obj, str):
			d= json.loads(obj)
		elif isinstance(obj, dict):
			d= obj
		else:
			raise TypeError('obj: Expected str or dict, not '+str(type(obj)))

		if not isinstance(lightid, (int, str)):
			raise TypeError('lightid: Expected int or str, not '+str(type(lightid)))

		light= HueLight(bridge)

		# Make sure id is a string
		light.__dict__['id']= str(lightid)

		for attr in HueLight.top_attrs:
			if attr in d:
				light.__dict__[attr]= d[attr]

		if 'luminaireuniqueid' in d:
			light.__dict__['luminaireuniqueid']= d['luminaireuniqueid']

		light.__dict__['config']= d['config']

		# Load capabilities before state since the latter needs the former
		light.__dict__['capabilities']= HueLightCapabilities.parse_definition(d['capabilities'])
		light.lightstate= HueLightState(d['state'])
		
		return light

	def __init__(self, bridge):
		if not isinstance (bridge, huectl.bridge.HueBridge):
			raise TypeError('bridge: Expected HueBridge object, not NoneType')

		self.bridge= bridge
		self.id= None
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

	def __setattr__(self, prop, val):
		if prop == 'name':
			self.rename(val)
		else:
			super().__setattr__(prop, val)

	def __str__(self):
		return f'<HueLight> {self.id} {self.name}, {self.productname}, {self.lightstate}'

	def islight(self):
		if HueColorMode.Dimmable in self.capabilities.colormodes:
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

	def rename(self, name):
		if name is None:
			return False

		name= name.strip()

		if not len(name):
			return False

		if len(name) > 32:
			raise ValueError(f'Max name length is 32 characters')

		try:
			self.bridge.set_light_attributes(self.id, name=name)
			self.__dict__['name']= name
		except Exception as e:
			raise e

	def change_state(self, schange):
		return self.bridge.set_light_state(self.id, schange.asdict())

