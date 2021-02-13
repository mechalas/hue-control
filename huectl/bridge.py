import urllib3
import requests
import json
import ssdp
import asyncio
import huectl.exception
import socket
import ssl
import xml.etree.ElementTree as ET
from huectl.light import HueLight
from huectl.group import HueGroup
from huectl.scene import HueScene
from huectl.sensor import HueSensor
from huectl.schedule import HueSchedule
from huectl.time import HueDateTime
from huectl.version import HueApiVersion
from huectl.rule import HueRule

class HueBridgeConfiguration:
	def __init__(self, data):
		# First, get the API version
		self.apiversion= HueApiVersion(data['apiversion'])
		self.name= data['name']

		# Data that's returned for all/unknown users

		self.modelid= data['modelid']
		self.mac= data['mac']
		self.factorynew= data['factorynew']
		self.bridgeid= data['bridgeid']
		self.replacesbridgeid= data['replacesbridgeid']
		self.swversion= data['swversion']

		# If we are an unknown user, we won't be shown the
		# whitelist. This is our cue not to not look for
		# additional config items.

		if 'whitelist' in data:
			self.userlist= HueBridgeUserlist(data['whitelist'])
		else:
			return
			
		# Data that's only returned for whitelisted users

		if self.apiversion < HueApiVersion('1.20'):
			if 'swupdate' in data:
				self.swupdate= data['swupdate']
		else:
			if 'swupdate2' in data:
				self.swupdate= data['swupdate2']


		self.portalstate= data['portalstate']

		if self.apiversion < HueApiVersion('1.21'):
			self.proxyaddress= data['proxyaddress']
			self.proxyport= data['proxyport']

		self.linkbutton= data['linkbutton']
		self.ipaddress= data['ipaddress']
		self.netmask= data['netmask']
		self.gateway= data['gateway']
		self.dhcp= data['dhcp']
		try:
			self.UTC= HueDateTime(data['UTC'])
		except:
			pass
		if data['localtime'] != 'none':
			self.localtime= HueDateTime(data['localtime'])
		else:
			self.localtime= None
		self.timezone= data['timezone']
		if 'datastoreversion' in data:
			self.datastoreversion= data['datastoreversion']
		self.zigbeechannel= data['zigbeechannel']

		for attr in ('portalservices', 'portalconnection', 'starterkitid', 'internetservices'):
			if attr in data:
				self.__dict__[attr]= data[attr]

class HueBridgeUser:
	def __init__(self, user_id, data):
		self.user_id= user_id
		self.name= None
		self.accessed= None
		self.created= HueDateTime(data['create date'])

		if 'name' in data:
			self.name= data['name']

		if 'last use date' in data:
			self.accessed= HueDateTime(data['last use date'])

	def __str__(self):
		s= f'<HueBridgeUser> {self.user_id} created '
		if self.name is not None:
			s+= f'by {self.name} '
		s+= f'on {self.created}'

		return s

	def info(self):
		return {
			'user_id': self.user_id,
			'name': self.name,
			'last_access': self.accessed,
			'created_on': self.created
		}

# The Hue API calls this a whitelist but let's use a name without 
# a lot of gross history attached to it.

class HueBridgeUserlist:
	def __init__(self, data):
		self._users= dict()

		for user_id,info in data.items():
			self._users[user_id]= HueBridgeUser(user_id, info)

	def __str__(self):
		n= len(self._users)
		return f'<HueUserlist> {n} user_ids'

	def users(self):
		for user in self._users.values():
			yield user

class HueDeviceScanResults():
	def __init__(self, bridge):
		self.bridge= bridge
		self.active= False
		self.lastscan= None
		self._found= dict()

	def __str__(self):
		s= '<HueDeviceScanResults> '
		if self.active:
			s+= 'active'
		else:
			s+= 'inactive'

		if len(self._found):
			s+= ', {:d} lights'

		if not self.active:
			if self.lastscan is None:
				s+= ', no scans'
			else:
				s+= f', lastscan {self.lastscan}'

		return s

	def __getattr__(self, key):
		if key == 'found':
			return self._found
		else:
			return self.__dict__[key]

	def scan_active(self):
		return self.active

	def add_item(self, itemid, name):
		if itemid not in self._found:
			self._found[itemid]= name

	def scan_time(self):
		return self.lastscan

#============================================================================
# A Hue Bridge object. This defines the various low-level bridge API calls
# as well as high-level operations for user applications.
#============================================================================

class HueBridge:
	SearchTime= 40	# The length of time the bridge spends searching for
					# new lights, in seconds. This is defined by the 
					# bridge API.

	def __init__(self, address, **kwargs):
		self.user_id= None
		self.address= address
		self.config= None
		self.proto= None
		self.request_defaults= dict()

		if 'user_id' in kwargs:
			self.set_user_id(kwargs['user_id'])

		self._load_config()

	def set_user_id(self, user_id):
		self.user_id= user_id

	def api_version(self):
		return self.config.apiversion

	def name(self):
		return self.config.name

	#------------------------------------------------------------
	# High level functions
	#------------------------------------------------------------

	# Return the serial number
	def serial_number(self):
		self._load_config()
		return self.config.mac.replace(':', '')

	# Return the whitelist
	def userlist(self):
		self._load_config()
		return self.config.userlist

	# Return supported timezones
	def timezones(self):
		if self.api_version() > '1.15':
			return self.call(f'info/timezones')
		else:
			return self.call(f'capabilities/timezones')

	# Name/rename the bridge
	def rename(self, newname):
		self.modify_configuration(name=newname)

	def recall_scene(self, sceneid):
		# Recalling a scene is done via the "set group state"
		# using the group associated with the scene.

		scene= self.get_scene(sceneid)
		try:
			groupid= scene.group
		except APIVersion:
			# We don't have a group id, so we have to apply
			# the light state to each light individually.
			groupid= None

		if groupid is None:
			lstates= scene.lightstates.dict()
			if not len(lstates):
				raise huectl.exception.InvalidObject('HueScene', sceneid)

			for lightid, state in lstates.items():
				self.set_light_state(lightid, state)

			return True

		data= {
			'scene': sceneid
		}

		rv= self.call(f'groups/{groupid}/action', method='PUT', data=data)
		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(rv)

		if len(rv) != 1:
			raise huectl.exception.BadResponse(rv)

		if 'success' not in rv:
			raise huectl.exception.BadResponse(rv)

		return True

	#------------------------------------------------------------
	# Bridge API
	#------------------------------------------------------------

	def _load_config(self):
		if self.config is None:
			self.config= self.get_configuration()

	# Groups
	#--------------------

	def get_group(self, groupid, raw=False, lights=None, sensors=None):
		data= self.call(f'groups/{groupid}', raw=raw)
		if raw:
			return data 

		group= HueGroup.parse_definition(data, groupid=groupid, bridge=self)
		if lights:
			group.lights.resolve_items(lights)
		if sensors:
			group.sensors.resolve_items(sensors)

		return group

	def get_all_groups(self, raw=False, lights=None, sensors=None):
		data= self.call('groups', raw=raw)
		if raw:
			return data 

		groups= dict()
		for groupid, groupdata in data.items():
			group= HueGroup.parse_definition(groupdata, groupid=groupid,
				bridge=self)

			if lights:
				group.lights.resolve_items(lights)
			if sensors:
				group.sensors.resolve_items(sensors)

			groups[groupid]= group


		return groups

	def set_group_attributes(self, groupid, **kwargs):
		if groupid == '0':
			raise huectl.exception.InvalidOperation('set_group_attribute', 'group 0')

		attrs= dict()

		for attr in ('name', 'class', 'lights'):
			if attr in kwargs:
				attrs[attr]= kwargs[attr]

		rv= self.call(f'groups/{groupid}', method='PUT', data=attrs)

		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(rv)

		if not len(rv):
			raise huectl.exception.BadResponse(rv)

		errors= []
		for elem in rv:
			if 'error' in elem:
				errors.append(elem[error].keys()[0])

		if len(errors):
			raise huectl.exception.AttrsNotSet(errors)

		return True

	# Lights
	#--------------------

	# Begin a search for new lights. The bridge will search for a
	# set number of seconds (defined by the API, and reflected in 
	# HueBridge.SearchTime)

	def init_light_search(self, serial):
		if not isinstance(serial, list):
			raise TypeError('serial: expected list not '+str(type(serial)))

		if len(serial) > 10:
			raise ValueError('serial: maximum of 10 serial numbers per search')
		elif len(serial):
			searchdata= { 'deviceid': serial }
		else:
			searchdata= None

		rv= self.call('lights', method='POST', data=searchdata)

		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(rv)

		if not len(rv):
			raise huectl.exception.BadResponse(rv)

		if 'success' not in rv[0]:
			raise huectl.exception.BadResponse(rv)

		return HueDeviceScanResults(self)

	# Get lights that were discovered during the last search (see
	# init_light_search). 

	def get_new_lights(self, scanresults):
		data= self.call('lights/new')

		if not isinstance(scanresults, HueDeviceScanResults):
			raise TypeError('scanresults: expected HueDeviceScanResults not '+str(type(scanresults)))

		if 'lastscan' in data:
			if data['lastscan'] == 'none':
				scanresults.active= False
			elif data['lastscan'] == 'active':
				scanresults.active= True
			else:
				scanresults.active= False
				scanresults.lastscan= HueDateTime(data['lastscan'])

	# Get a specific light by its id

	def get_light(self, lightid, raw=False):
		data= self.call(f'lights/{lightid}', raw=raw)
		if raw:
			return data

		return HueLight.parse_definition(data, lightid=lightid, bridge=self)
		
	def get_all_lights(self, raw=False):
		data= self.call('lights', raw=raw)
		if raw:
			return data 

		lights= dict()
		for lightid, lightdata in data.items():
			lights[lightid]= HueLight.parse_definition(lightdata,
				lightid=lightid, bridge=self)

		return lights

	def set_light_attributes(self, lightid, **kwargs):
		attrs= dict()
		if 'name' in kwargs:
			attrs['name']= kwargs['name']

		rv= self.call(f'lights/{lightid}', method='PUT', data=attrs)

		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(rv)

		if not len(rv):
			raise huectl.exception.BadResponse(rv)

		errors= []
		for elem in rv:
			if 'error' in elem:
				errors.append(elem[error].keys()[0])

		if len(errors):
			raise huectl.exception.AttrsNotSet(errors)

		return True

	def set_light_state(self, lightid, state):
		rv= self.call(f'lights/{lightid}/state', method='PUT', data=state)

		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(rv)

		if not len(rv):
			raise huectl.exception.BadResponse(rv)

		errors= []
		for elem in rv:
			if 'error' in elem:
				errors.append(elem[error].keys()[0])

		if len(errors):
			raise huectl.exception.AttrsNotSet(errors)
				
		return True


	# Scenes
	#--------------------

	def get_all_scenes(self, raw=False, lights=None):
		if self.api_version() < HueApiVersion('1.1'):
			raise huectl.exception.APIVersion(have=str(self.api_version()), need='1.1')

		data= self.call('scenes', raw=raw)
		if raw:
			return data

		scenes= dict()
		for sceneid, scenedata in data.items():
			scene= HueScene.parse_definition(scenedata, bridge=self, sceneid=sceneid)
			if lights is not None:
				scene.lights.resolve_items(lights)
			scenes[sceneid]= scene

		return scenes

	def get_scene(self, sceneid, raw=False, lights=None):
		data= self.call(f'scenes/{sceneid}', raw=raw)
		if raw:
			return data

		scene= HueScene.parse_definition(data, bridge=self, sceneid=sceneid)
		if lights is not None:
			scene.lights.resolve_items(lights)

		return scene

	def delete_scene(self, sceneid):
		rv= self.call(f'scenes/{sceneid}', method='DELETE')

		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(str(rv))
		if len(rv) != 1:
			raise huectl.exception.BadResponse(str(rv))

		if 'success' in rv[0]:
			return True

		raise huectl.exception.BadResponse(str(rv[0]))

	def modify_scene(self, scenedef, sceneid):
		if not isinstance(scenedef, dict):
			raise TypeError('scenedef: expected dict, not '+str(type(scenedef)))

		if not isinstance(sceneid, str):
			raise TypeError('sceneid: expected str, not '+str(type(scenedef)))

		uri= f'/scenes/{sceneid}'

		self._scene_api_version_check(scenedef)

		rv= self.call(uri, method='PUT', data=scenedef)

		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(rv)

		if len(rv) != 1:
			raise huectl.exception.BadResponse(rv)

		if 'success' not in rv:
			raise huectl.exception.BadResponse(rv)

	def create_scene(self, scenedef, sceneid=None):
		uri= '/scenes'

		if not isinstance(scenedef, dict):
			raise TypeError('scenedef: expected dict, not '+str(type(scenedef)))

		self._scene_api_version_check(scenedef)

		if sceneid is not None:
			uri= f'/scenes/{sceneid}'

		rv= self.call(uri, method='POST', data=scenedef)

		if not isinstance(rv, list):
			raise huectl.exception.BadResponse(rv)

		if len(rv) != 1:
			raise huectl.exception.BadResponse(rv)

		if 'success' not in rv:
			raise huectl.exception.BadResponse(rv)

	def _scene_api_version_check(self, scenedef):
		apiver= self.api_version()

		# Version 1 scenes are deprecated. We won't support API versions
		# < 1.11
		if apiver < '1.11':
			raise huectl.exception.InvalidOperation('bridge API '+apiver, 'create_scene')

		# Lightstats available in 1.29
		if 'lightstates' in scenedef and apiver < '1.29':
			raise huectl.exception.APIVersion(need='1.29', have=apiver)

	# Rules
	#--------------------

	def get_rule(self, ruleid, raw=False):
		data= self.call(f'rules/{ruleid}')
		if raw:
			return data

		return HueRule(ruleid=ruleid, bridge=self, obj=data)

	def get_all_rules(self, raw=False):
		data= self.call('rules', raw=raw)
		if raw:
			return data

		rules= dict()
		for ruleid, ruledata in data.items():
			rule= HueRule(ruleid=ruleid, bridge=self, obj=ruledata)
			rules[ruleid]= rule

		return rules

	# Schedules
	#--------------------

	def get_schedule(self, schedid, raw=False):
		data= self.call(f'schedules/{schedid}')
		if raw:
			return data

		return HueSchedule(schedid=schedid, bridge=self, obj=data)

	def get_all_schedules(self, raw=False):
		data= self.call('schedules', raw=raw)
		if raw:
			return data

		schedules= dict()
		for schedid, scheduledata in data.items():
			sched= HueSchedule(schedid=schedid, bridge=self, obj=scheduledata)
			schedules[schedid]= sched

		return schedules

	# Sensors
	#--------------------

	def get_sensor(self, sensorid, raw=False):
		data= self.call(f'sensors/{sensorid}', raw=raw)
		if raw:
			return data

		return HueSensor(data, sensorid=sensorid, bridge=self)

	def get_all_sensors (self, raw=False):
		data= self.call('sensors', raw=raw)
		if raw:
			return data

		sensors= dict()
		for sensorid, sensordata in data.items():
			sensors[sensorid]= HueSensor(sensordata, sensorid=sensorid, bridge=self)

		return sensors

	# Configuration
	#--------------------

	def get_configuration(self, raw=False):
		data= self.call('config', raw=raw)
		if raw:
			return data

		self.config= HueBridgeConfiguration(data)

		return self.config

	def modify_configuration(self, **kwargs):
		attrs= dict(**kwargs)
		apiver= self.api_version()

		data= dict()

		for k,v in attrs.items():
			if k == 'proxyport':
				if not isinstance(v, int):
					raise TypeError(f'{k}: expected int not '+str(type(v)))
				if v < 0 or v > 65535:
					raise ValueError(f'{k}: must be between 0 and 65535')

			elif k == 'name':
				if not isinstance(v, str):
					raise TypeError(f'{k}: expected str not '+str(type(v)))
				if len(v) < 4 or len(v) > 16:
					raise ValueError(f'{k}: must be between 4 and 16 characters')

			elif k == 'swupdate':
				raise NotImplemented(k)

			elif k == 'proxyaddress':
				if not isinstance(v, str):
					raise TypeError(f'{k}: expected str not '+str(type(v)))
				if len(v) < 0 or len(v) > 40:
					raise ValueError(f'{k}: must be between 0 and 40 characters')
			elif k == 'linkbutton':
				raise NotImplemented

			elif k in('dhcp', 'touchlink'):
				if not isinstance(v, (bool, int)):
					raise TypeError(f'{k}: expected bool or int not '+str(type(v)))
				v= bool(v)

			elif k == 'timezone':
				if not isinstance(v, str):
					raise TypeError(f'{k}: expected str not '+str(type(v)))

				if v not in self.timezones():
					raise ValueError('{k}: not a known timezone')

			elif k in ('ipaddress', 'netmask', 'gateway', 'UTC'):
				if not isinstance(v, str):
					raise TypeError(f'{k}: expected str not '+str(type(v)))

			elif k == 'zigbeechannel':
				if not isinstance(v, int):
					raise TypeError(f'{k}: expected int not '+str(type(v)))
				if v not in (11,15,20,25):
					raise ValueError(f'{k}: must be one of: 11, 15, 20, 25')

			data[k]= v

		rv= self.call('config', method='PUT', data=data)

	def create_user(self, appname='Python', device='CLI', client_key=None):
		data= { 
			'devicetype': '#'.join([appname, device])
		}
		if client_key is not None:
			data['generate clientkey']= client_key
		rv= self.call(None, registration=True, data=data)

		item= rv[0]
		if 'success' in item:
			if 'username' in item['success']:
				return item['success']['username']

		raise huectl.exception.BadResponse(json.dumps(rv))

	def get_datastore(self):
		return self.call(None, raw=True)

	# Resourcelinks
	#--------------------

	def get_all_resourcelinks(self, raw=False):
		data= self.call('resourcelinks', raw=raw)
		if raw:
			return data

		raise NotImplementedError

	def get_resourcelink(self, reslinkid, raw=False):
		data= self.call(f'resourcelinks/{reslinkid}', raw=raw)
		if raw:
			return data

		raise NotImplementedError

	# Internal calls
	#--------------------

	def determine_protocol(self):
		urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

		try:
			response= requests.request('HEAD', f'https://{self.address}/',
				verify=False)
			self.proto= 'https'
			self.request_defaults['verify']= False
			return
		except:
			pass

		self.proto= 'http'

	# Raw HTTP calls
	#--------------------

	def call(self, endpoint, registration=False, method='GET', data=None, raw=False):
		# First, see if the bridge will do TLS. If so, remember that. If
		# not, fall back to HTTP.
		if self.proto is None:
			self.determine_protocol()

		defaults= self.request_defaults

		if registration:
			# It's a registration call
			url= f'{self.proto}://{self.address}/api'
			method= 'POST'
		else:
			if endpoint is None:
				url= f'{self.proto}://{self.address}/api/{self.user_id}'
			else:
				url= f'{self.proto}://{self.address}/api/{self.user_id}/{endpoint}'

		if data is None:
			response= requests.request(method, url, **defaults)
		else:
			response= requests.request(method, url, data=bytes(json.dumps(data), 'utf-8'), **defaults)

		if response.status_code != 200:
			raise huectl.exception.BadHTTPResponse(url)

		reply= response.text
		if raw:
			return reply

		obj= json.loads(reply)

		if isinstance(obj, list):
			for item in obj:
				# Raise an exception for each error we find, just in
				# case one is caught.

				if 'error' in item:
					self._error(item['error'])

		return obj


	def _error(self, item):
		code= item['type']
		msg= item['description']

		if code == 1:
			raise huectl.exception.UnauthorizedUser(msg)
		elif code == 2:
			raise huectl.exception.InvalidJSON(msg)
		elif code == 3:
			raise huectl.exception.ResourceUnavailable(msg)
		elif code == 4:
			raise huectl.exception.MethodNotAvailable(msg)
		elif code == 5:
			raise huectl.exception.MissingParameters(msg)
		elif code == 6:
			raise huectl.exception.ParameterUnavailable(msg)
		elif code == 7:
			raise huectl.exception.ParameterReadOnly(msg)
		elif code == 8:
			raise huectl.exception.TooMany(msg)
		elif code == 9:
			raise huectl.exception.PortalRequired(msg)
		elif code == 901:
			raise huectl.exception.InternalError(msg)
		else:
			raise huectl.exception.HueGenericException(f'{code} {msg}')


#===========================================================================
# Bridge discovery
#===========================================================================

class HueBridgeSearch(ssdp.SimpleServiceDiscoveryProtocol):
	locations= set()
	bridges= dict()
	PortalAddress= 'https://discovery.meethue.com/'

	def response_received(self, response: ssdp.SSDPResponse, addr: tuple):
		for header,value in response.headers:
			if header == 'LOCATION':
				if value in HueBridgeSearch.locations:
					return

				HueBridgeSearch.locations.add(value)

				# Make sure the discovery address matches the device address
				if addr[0] not in value:
					return

				try:
					response= requests.request('GET', value)
				except Exception as e:
					return

				if response.status_code != 200:
					return

				try:
					data= response.text
				except:
					return

				try:
					root= ET.fromstring(data)
				except Exception as e:
					return

				model= root.find('./{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}modelName')
				if model is None:
					return

				if model.text.startswith('Philips hue bridge'):
					serial= root.find('./{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}serialNumber')
					if serial is None:
						return

					HueBridgeSearch.bridges[serial.text]= {
						'serialNumber': serial.text,
						'modelName': model.text,
						'ipAddress': addr[0]
					}

	# N-UPnP Bridge Discovery, which calls the Hue Portal. Per the Philips
	# Hue API, bridges periodically poll this portal which stores each 
	# bridge's internal and external IP addresses, name, and ID.
	#
	# This method is fast, but it won't find new/unconfigured bridges.
	@staticmethod
	def quick_search():
		response= requests.request('GET', HueBridgeSearch.PortalAddress)
		if response.status_code != 200:
			raise BadHTTPResponse(code=response.status_code)

		results= json.loads(response.text)
		for bridge in results:
			bid= bridge['id']
			serial= bid[0:6]+bid[-6:]
			HueBridgeSearch.bridges[serial]= {
				'serialNumber': serial,
				'ipAddress': bridge['internalipaddress']
			}

		return HueBridgeSearch.bridges

	# UPnP Bridge Discovery, using the Simple Servicer Discovery Protocol
	# (SSDP)
	@staticmethod
	def search(search_time=30):
		loop= asyncio.get_event_loop()
		connect= loop.create_datagram_endpoint(HueBridgeSearch,
			family=socket.AF_INET)
		transport, protocol= loop.run_until_complete(connect)
	
		req= ssdp.SSDPRequest(
			'M-SEARCH',
			headers= {
				'HOST': '239.255.255.250:1900',
				'MAN': '"ssdp:discover"',
				'MX': '10',
				'ST': 'ssdp:all'
			}
		)
		req.sendto(transport, (HueBridgeSearch.MULTICAST_ADDRESS, 1900))
	
		try:
			loop.run_until_complete(asyncio.sleep(search_time))
		except KeyboardInterrupt:
			return None
	
		transport.close()
		loop.close()
	
		return(HueBridgeSearch.bridges)


