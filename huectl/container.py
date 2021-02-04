# A collection of Hue objects.
#
# Functionally, this is a lot like a dict() and employs methods to mimic
# that behavior. But, it has a notion of "unresolved" keys (keys where
# no values are present), which is needed to support HueScene where the
# full scene list only provides member light ID's and not light
# state information. We need a way to keep track of those unreoslved
# items.

class HueCollection:
	def __init__(self, *args, **kwargs):
		self.item_type= args[0]
		self.resolved_items= dict()
		self.unresolved_item_ids= set()

	# Make a copy of the collection. This copies the keys (item ID's)
	# but NOT the objects that they reference.

	def clone(self):
		h= HueCollection(self.item_type)
		h.resolved_items.update(self.resolved_items)
		h.unresolved_item_ids= set(self.unresolved_item_ids)
		return h

	def remove(self, item_id):
		if item_id in self.resolved_items:
			del self.resolved_items[item_id]
			return True
		elif item_id in self.unresolved_item_ids:
			self.unresolved_item_ids.remove(item_id)
			return True

		return False

	def clear(self):
		self.resolved_items= dict()
		self.unresolved_item_ids= set()

	def keys(self, sort=False, unresolved=False):
		idlist= list(self.resolved_items.keys())
		if unresolved:
			idlist+= list(self.unresolved_item_ids)

		if sorted:
			return sorted(idlist, key=lambda x: int(x))

		return idlist

	def items(self, unresolved=False):
		d= dict(self.resolved_items)
		if unresolved:
			d.update(dict.fromkeys(self.unresolved_item_ids, None))
		return d.items()

	# Add a dictionary of form { id: obj }
	def update(self, items):
		if not isinstance(items, dict):
			raise TypeError('Expected list or dict')

		if not(len(items)):
			return False

		rv= False

		for itemid, itemobj in items.items():
			skey= str(itemid)
			if self.item_type != type(itemobj):
				raise TypeError(f'Expected {self.item_type}')

			if skey not in self.resolved_items:
				rv= True

				self.resolved_items[skey]= itemobj

				if skey in self.unresolved_item_ids:
					self.unresolved_item_ids.remove(skey)

		return rv
	
	def update_fromkeys(self, items):
		if not isinstance(items, (list, tuple)):
			raise TypeError

		if not len(items):
			return False

		n= len(self.unresolved_item_ids)

		# Make sure the keys are strings
		self.unresolved_item_ids|= set(map(lambda x: str(x), items))

		if len(self.unresolved_item_ids) == n:
			return False

		return True

	def item(self, itemid):
		skey= str(itemid)
		if skey in self.resolved_items:
			return self.resolved_items[skey]
		elif skey in self.unresolved_item_ids:
			return None

		raise KeyError(skey)

	def resolve_items(self, cache):
		if not isinstance(cache, dict):
			raise TypeError

		# Store our old set
		need= set(self.unresolved_item_ids)

		for itemid in self.unresolved_item_ids:
			if itemid in cache:
				self.resolved_items[itemid]= cache[itemid]
				need.remove(itemid)

		# Update the set with the new set
		self.unresolved_item_ids= need

	def unresolved_items(self):
		if len(self.unresolved_item_ids):
			return True
		return False

# An object that contains one or more Hue collections. These collections
# can be added dynamically, and then referenced as an object attribute.

class HueContainer:
	def __init__(self):
		self.name= None

		# Container dictionary. Key = container type, Val = HueCollection
		self.collections= dict()

	def __getattr__(self, item):
		if item in self.collections:
			return self.collections[item]

	def add_collection(self, name, dtype):
		self.collections[name]= HueCollection(dtype)

