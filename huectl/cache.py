from datetime import datetime as dt
import time
import json
import tempfile
import random
import os
import os.path

#============================================================================
# A class for caching Hue objects. For objects like lights and sensors,
# this is really to prevent rapid-fire requests to the bridge so a short
# cache life is in order. For schedules, rules, and groups, the cache life
# can be a little longer.
#
# For scene attributes, we rely on the lastupdate property. Scene 
# attributes are cached individually, not as a whole, since they must be
# fetched individually.
#
# Note that this class is not MP or MT safe. A process can read the cache and
# write a new one while another process or thread has a stale copy.
#
# TODO: This can (mostly) be addressed by checking the mod time on the cache.
#============================================================================

class HueCache:
	ValidObjs= ('lights', 'groups', 'rules', 'scenes', 'scene_attrs', 'schedules', 'sensors', '_control')
	DefCache= {
		'_control': {
			'lastupdated': {}
		}
	}
	MinLifetime= 5

	def __init__(self, filename):
		self._cache_file= os.path.expanduser(filename)
		self._cache= dict(HueCache.DefCache)

	def __getattr__(self, attr):
		if attr in HueCache.ValidObjs:
			if attr not in self._cache:
				self._cache[attr]= dict()

			return self._cache[attr]

	# Load the cache file

	def load(self):
		try:
			if os.path.exists(self._cache_file):
				c= dict(HueCache.DefCache)
				with open(self._cache_file) as fp:
					c.update(json.load(fp))

				self._cache= c
		except Exception as e:
			raise(e)

		self._sanitize()

	# Save the cache file. Make this an atomic operation. 

	def save(self):
		self._sanitize()
		try:
			newfile= '{:s}{:08x}'.format(
				os.path.join(tempfile.gettempdir(), '.huecache'),
				random.getrandbits(64))
			with open(newfile, 'w') as fp:
				json.dump(self._cache, fp)

			os.rename(newfile, self._cache_file)
		except Exception as e:
			raise(e)

	# Remove objects that we don't recognize

	def _sanitize(self, obj=None):
		if obj is None:
			obj= self._cache
			
		objlist= list(obj.keys())

		for k in objlist:
			if k not in HueCache.ValidObjs:
				del obj[k]

	# Get the last time objects of type objclass (lights, sensors, etc.) were updated

	def lastupdate(self, oclass):
		if oclass not in HueCache.ValidObjs:
			raise ValueError(f"unknown object class {oclass}")

		c= self._cache

		try:
			return c['_control']['lastupdated'][oclass]
		except KeyError:
			pass

		return None

	# Is our cache less than interval seconds old?
	def is_current(self, oclass, interval):
		# Our minimum interval 
		if interval < HueCache.MinLifetime:
			interval= HueCache.MinLifetime

		if oclass not in HueCache.ValidObjs:
			raise ValueError(f"unknown object class {oclass}")

		lastupdate= self.lastupdate(oclass)
		if lastupdate is None:
			return False

		if time.time() - lastupdate >= interval:
			return False

		return True

	def mark_dirty(self, oclass):
		if oclass not in HueCache.ValidObjs:
			raise ValueError(f"unknown object class {oclass}")

		self._cache['_control']['lastupdate']= None

	def delete_oid(self, oclass, oid):
		if oclass not in HueCache.ValidObjs:
			raise ValueError(f"unknown object class {oclass}")
		try:
			del self._cache[oclass][oid]
		except KeyError:
			pass

		return

	def update_oid(self, oclass, obj):
		if isinstance(obj, str):
			data= json.loads(obj)
		else:
			data= obj

		try:
			c= self._cache[oclass]
		except KeyError:
			return

		c.update(data)

	def update(self, obj):
		if isinstance(obj, str):
			data= json.loads(obj)
		else:
			data= obj

		self._sanitize(obj=data)

		c= self._cache
		c.update(data)
		for k in data.keys():
			try:
				c['_control']['lastupdated'][k]= time.time()
			except KeyError:
				# Repair the cache
				c['_control']['lastupdated']= dict()

	def clear(self, oclass):
		if oclass not in HueCache.ValidObjs:
			raise ValueError(f"unknown object class {oclass}")
		self._cache[oclass]= {}
		self._cache['lastupdated'][oclass]= None

