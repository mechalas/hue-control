from huectl.exception import InvalidOperation
from huectl.color import HueColorxyY, HueColorHSB, HueColorPointxy, HueColorPointHS, HueColorGamut, HueColorTemp, kelvin_to_mired
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
	HSB= 'hsb'
	xyY= 'xy'
	CT= 'ct'
	# A dummy mode that doesn't exist but we need something to separate
	# white lights from the Hue Outlet.
	Brightness= '__brightness_only__'

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
			self.colormodes.add(HueColorMode.Brightness)
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

		self.colormode= HueColorMode.Brightness

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


#----------------------------------------------------------------------------
# HueLightStateChange: A light state change requested by the user
# 
# This object is auto-created when the user invokes methods on the parent
# light object to change its state.
#
# It can also be created directly for applying the same change to multiple
# lights, though you won't get error-checking on the lights' supported modes
# (though that is probably fine).
#----------------------------------------------------------------------------

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
		if bri < 1 or bri > 254:
			raise ValueError(f'Brightness {bri} out of range')

		self.change['bri']= bri
		if 'bri_inc' in self.change:
			del self.change['bri_inc']

	def inc_brightness(self, bri):
		if bri < -254 or bri > 254:
			raise ValueError(f'Brightness delta {bri} out of range')

		self.change['bri_inc']= bri
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
		if ct < -65534 or ct > 65534:
			raise ValueError(f'Mired color temperature delta {ct} out of range')

		self.change['ct_inc']= ct
		if 'ct' in self.change:
			del self.change['ct']

	def set_xy(self, xy):
		if not (isinstance(xy, list) or isinstance(xy, tuple)):
			raise TypeError(f'xy must be tuple or list')
		if len(xy) != 2:
			raise ValueError(f'xy must be coordinate pair')

		if x < 0 or x > 1:
			raise ValueError(f'x coordinate must be between 0 and 1')

		if y < 0 or y > 1:
			raise ValueError(f'y coordinate must be between 0 and 1')

		self.change['xy']= [ round(x,4), round(y,4) ]

	def inc_xy(self, xy):
		if not (isinstance(xy, list) or isinstance(xy, tuple)):
			raise TypeError(f'xy must be tuple or list')
		if len(xy) != 2:
			raise ValueError(f'xy must be increment pair')

		if x < -0.5 or x > 0.5:
			raise ValueError(f'x increment must be between -0.5 and 0.5')

		if y < -0.5 or y > 0.5:
			raise ValueError(f'y increment must be between -0.5 and 0.5')

		self.change['xy_inc']= [ round(x,4), round(y,4) ]

	def set_hue(self, hue):
		if hue < 0 or hue > 65535:
			raise ValueError(f'Hue {hue} out of range')

		self.change['hue']= hue
		if 'hue_inc' in self.change:
			del self.change['hue_inc']

	def inc_hue(self, hue):
		if hue < -65534 or hue > 65534:
			raise ValueError(f'Hue {hue} out of range')

		self.change['hue_inc']= hue
		if 'hue' in self.change:
			del self.change['hue']

	def set_alert(self, alert):
		if not HueAlertEffect.supported(alert):
			raise ValueError(f'Unknown alert mode {alert}')

		self.change['alert']= alert

	def set_dynamic_effect(self, effect):
		if not HueDynamicEffect.supported(effect):
			raise ValueError(f'Unknown dynamic effect {effect}')

		self.change['effect']= effect

	def data(self):
		return self.change

	def __str__(self):
		return json.dumps(self.change)

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
		self.statechange= None

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
		if HueColorMode.Brightness in self.capabilities.colormodes:
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

	def _init_state_change(self):
		if self.statechange is None:
			self.statechange= HueLightStateChange()

	# Reset pending state changes

	def reset_state(self):
		self.statechange= None

	# Apply any outstanding changes and set an optional 
	# transition time.

	def apply_pending_changes(self, ms=None):
		if self.statechange is None:
			return

		if ms is not None:
			self.statechange.set_transition_time(ms)

		return self.bridge.set_light_state(self.id, self.statechange.data())

	# Apply changes from an external HueLightStateChange object

	def apply_changes(self, obj):
		return self.bridge.set_light_state(self.id, obj.data())

	# On/Off
	#----------------------------------------

	def power_off(self):
		return self.power_on(state=False)

	def power_on(self, state=True):
		self._init_state_change()
		self.statechange.set_power(state)

	# Brightness
	#----------------------------------------

	# Set brightness level

	def set_brightness(self, bri):
		if not self.islight():
			raise InvalidOperation('brightness', f'Light {self.id}')

		self._init_state_change()
		self.statechange.set_brightness(round(bri))

	# Increment/decrement brightness

	def inc_brightness(self, bri):
		if not self.islight():
			raise InvalidOperation('brightness', f'Light {self.id}')

		self._init_state_change()
		self.statechange.inc_brightness(round(bri))

	# Color temperature
	#----------------------------------------

	# Set color temperature (in kelvin)

	def set_cct(self, kelvin):
		if not self.hascolortemp():
			raise InvalidOperation('color temperature', f'Light {self.id}')

		self._init_state_change()
		self.statechange.set_cct(round(kelvin))
		
	# Set color temperature (in mired)

	def set_ct(self, mired):
		if not self.hascolortemp():
			raise InvalidOperation('color temperature', f'Light {self.id}')

		self._init_state_change()
		self.statechange.set_ct(round(mired))
		
	# Increment/decrement color temperature (in kelvin)

	def inc_cct(self, kelvin):
		if not self.hascolortemp():
			raise InvalidOperation('color temperature', f'Light {self.id}')

		self._init_state_change()
		self.statechange.inc_cct(round(kelvin))

	# Increment/decrement color temperature (in mired)

	def inc_ct(self, mired):
		if not self.hascolortemp():
			raise InvalidOperation('color temperature', f'Light {self.id}')

		self._init_state_change()
		self.statechange.inc_ct(round(mired))


	# Hue (HSB mode)
	#----------------------------------------

	# Set hue value

	def set_hue(self, h):
		if not self.hascolor():
			raise InvalidOperation('hue', f'Light {self.id}')

		self._init_state_change()
		self.statechange.set_hue(round(h))

	def inc_hue(self, h):
		if not self.hascolor():
			raise InvalidOperation('hue', f'Light {self.id}')

		self._init_state_change()
		self.statechange.inc_hue(round(h))

	# Sat (HSB mode)
	#----------------------------------------

	# Set sat value

	def set_sat(self, sat):
		if not self.hascolor():
			raise InvalidOperation('sat', f'Light {self.id}')

		self._init_state_change()
		self.statechange.set_sat(round(sat))

	def inc_sat(self, sat):
		if not self.hascolor():
			raise InvalidOperation('sat', f'Light {self.id}')

		self._init_state_change()
		self.statechange.inc_sat(round(sat))

	# Alert
	#----------------------------------------

	def set_alert(self, alert):
		if not self.islight():
			raise InvalidOperation('alert', f'Light {self.id}')

		self._init_state_change()
		self.statechange.set_alert(alert)

	# Dynamic effects
	#----------------------------------------

	def set_alert(self, effect):
		if not self.hascolor():
			raise InvalidOperation('effect', f'Light {self.id}')

		self._init_state_change()
		self.statechange.set_effect(effect)

