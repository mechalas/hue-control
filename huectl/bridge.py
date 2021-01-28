import urllib.request
import json
import ssdp
import asyncio
import huectl.exception
import socket
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

		if self.apiversion < HueApiVersion('1.20'):
			if 'swupdate' in data:
				self.swupdate= data['swupdate']
		else:
			if 'swupdate2' in data:
				self.swupdate= data['swupdate2']

		self.userlist= HueBridgeUserlist(data['whitelist'])
		self.portalstate= data['portalstate']
		self.swversion= data['swversion']

		if self.apiversion < HueApiVersion('1.21'):
			self.proxyaddress= data['proxyaddress']
			self.proxyport= data['proxyport']

		self.linkbutton= data['linkbutton']
		self.ipaddress= data['ipaddress']
		self.mac= data['mac']
		self.netmask= data['netmask']
		self.gateway= data['gateway']
		self.dhcp= data['dhcp']
		self.UTC= HueDateTime(data['UTC'])
		self.localtime= HueDateTime(data['localtime'])
		self.timezone= data['timezone']
		self.modelid= data['modelid']
		self.datastoreversion= data['datastoreversion']
		self.zigbeechannel= data['zigbeechannel']
		self.portalservices= data['portalservices']
		self.portalconnection= data['portalconnection']
		self.bridgeid= data['bridgeid']
		self.replacesbridgeid= data['replacesbridgeid']
		self.factorynew= data['factorynew']
		self.starterkitid= data['starterkitid']
		self.internetservices= data['internetservices']

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

class HueBridge:
	def __init__(self, address, **kwargs):
		self.user_id= None
		self.address= address
		self.config= None

		if 'user_id' in kwargs:
			self.set_user_id(kwargs['user_id'])

	def set_user_id(self, user_id):
		self.user_id= user_id

	def api_version(self):
		self._load_config()
		return self.config.apiversion

	#------------------------------------------------------------
	# High level functions
	#------------------------------------------------------------

	def serial_number(self):
		self._load_config()
		return self.config.mac.replace(':', '')

	def userlist(self):
		self._load_config()
		return self.config.userlist

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
				raise InvalidObject('HueScene', sceneid)

			for lightid, state in lstates.items():
				self.set_light_state(lightid, state)

			return True

		data= {
			'scene': sceneid
		}

		status= self.call(f'groups/{groupid}/action', method='PUT', data=data)
		if not isinstance(status, list):
			raise huectl.exception.BadResponse(status)

		if len(status) != 1:
			raise huectl.exception.BadResponse(status)

		if 'success' not in status:
			raise huectl.exception.BadResponse(status)

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

		kwargs= dict()
		if lights is not None:
			kwargs['lights']= lights
		if sensors is not None:
			kwargs['sensors']= sensors

		group= HueGroup(groupid=groupid, bridge=self)
		group.load(data, **kwargs)

		return group

	def get_all_groups(self, raw=False, lights=None, sensors=None):
		data= self.call('groups', raw=raw)
		if raw:
			return data 

		kwargs= dict()
		if lights is not None:
			kwargs['lights']= lights
		if sensors is not None:
			kwargs['sensors']= sensors

		groups= dict()
		for groupid, groupdata in data.items():
			group= HueGroup(groupid=groupid, bridge=self)
			group.load(groupdata, **kwargs)
			groups[groupid]= group

		return groups

	# Lights
	#--------------------

	def get_light(self, lightid, raw=False):
		data= self.call(f'lights/{lightid}', raw=raw)
		if raw:
			return data

		return HueLight(data, lightid=lightid, bridge=self)
		
	def get_all_lights(self, raw=False):
		data= self.call('lights', raw=raw)
		if raw:
			return data 

		lights= dict()
		for lightid, lightdata in data.items():
			lights[lightid]= HueLight(lightdata, lightid=lightid, bridge=self)

		return lights

	def set_light_attributes(self, lightid, light):
		attrs= {
			'name': light['name'][:32]
		}
		rv= self.call(f'lights/{lightid}', method='PUT', data=attrs)

		raise NotImplementedError

	def set_light_state(self, lightid, state):
		rv= self.call(f'lights/{lightid}/state', method='PUT', data=state)

		if not isinstance(rv, list):
			raise BadResponse(rv)

		if not len(rv):
			raise BadResponse(rv)

		errors= []
		for elem in rv:
			if 'error' in elem:
				errors.append(elem[error].keys()[0])

		if len(errors):
			raise AttrsNotSet(errors)
				
		return True

	# Scenes
	#--------------------

	def get_all_scenes(self, raw=False, lights=None):
		if self.api_version() < HueApiVersion('1.1'):
			raise huectl.exception.APIVersion(have=str(self.api_version()), need='1.1')

		data= self.call('scenes', raw=raw)
		if raw:
			return data

		kwargs= dict()
		if lights is not None:
			kwargs['lights']= lights

		scenes= dict()
		for sceneid, scenedata in data.items():
			scene= HueScene(sceneid=sceneid, bridge=self)
			scene.load(scenedata, **kwargs)
			scenes[sceneid]= scene

		return scenes

	def get_scene(self, sceneid, raw=False, lights=None):
		data= self.call(f'scenes/{sceneid}', raw=raw)
		if raw:
			return data

		kwargs= dict()
		if lights is not None:
			kwargs['lights']= lights
		
		scene= HueScene(sceneid=sceneid, bridge=self)
		scene.load(data, **kwargs)

		return scene

	def delete_scene(self, sceneid):
		status= self.call(f'scenes/{sceneid}', method='DELETE')

		if not isinstance(status, list):
			raise huectl.exception.BadResponse(str(status))
		if len(status) != 1:
			raise huectl.exception.BadResponse(str(status))

		if 'success' in status[0]:
			return True

		raise huectl.exception.BadResponse(str(status[0]))

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

	def create_user(self, registration=True, appname='Python', device='CLI', client_key=None):
		data= { 
			'devicetype': '#'.join([appname, device])
		}
		if client_key is not None:
			data['generate clientkey']= client_key
		response= self.call(None, data=data)

		item= response[0]
		if 'success' in item:
			if 'username' in item['success']:
				return item['success']['username']

		raise huectl.exception.BadResponse(json.dumps(response))

	def get_datastore(self):
		return self.call(None, raw=True)

	# Resourcelinks
	#--------------------

	def get_all_resourcelinks(self, raw=False):
		data= self.call('resourcelinks', raw=raw)
		if raw:
			return data

		raise NotImplemented

	def get_resourcelink(self, reslinkid, raw=False):
		data= self.call(f'resourcelinks/{reslinkid}', raw=raw)
		if raw:
			return data

		raise NotImplemented

	# Raw HTTP calls
	#--------------------

	def call(self, endpoint, registration=False, method='GET', data=None, raw=False):
		if registration:
			# It's a registration call
			url= f'http://{self.address}/api'
			method= 'POST'
		else:
			if endpoint is None:
				url= f'http://{self.address}/api/{self.user_id}'
			else:
				url= f'http://{self.address}/api/{self.user_id}/{endpoint}'

		if data is None:
			request= urllib.request.Request(url=url, method=method)
		else:
			request= urllib.request.Request(url=url, data=bytes(json.dumps(data), 'utf-8'), method=method)
		response= urllib.request.urlopen(request)

		if response.status != 200:
			raise huectl.exception.BadHTTPResponse(url)

		reply= response.read().decode('UTF-8')
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
					response= urllib.request.urlopen(value)
				except Exception as e:
					return

				if response.status != 200:
					return

				try:
					data= response.read().decode('UTF-8')
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


