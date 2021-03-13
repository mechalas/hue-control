
#============================================================================
# Hue accessory. A physical device that contains one or more sensots. An
# accessory is a physical product that is generally referred to by name,
# and whose behavior is a combination of multiple sensor inputs, schedules,
# and rules.
# 
# A Hue accessory has a "default way of working" that is defined by the
# Hue App, but at the bridge level these devices can be given an arbitrary
# behavior set.
#============================================================================

class HueAccessory():
	@staticmethod
	def collate(sensors):
		accessories= []
		if sensors is None:
			return accessories

		if len(sensors) == 0:
			return accessories

		# Get our list of primary sensors

		for sensor in sensors.values():
			if sensor.is_primary():
				accessories.append(HueAccessory(sensor))
		
		# Now loop through the list, and identify all sensors grouped with
		# the primary sensor.

		for acc in accessories:
			psensor= acc.primary()
			paddr= psensor.address()
			for sensor in sensors.values():
				if psensor == sensor or sensor.is_primary():
					continue

				if sensor.address() == paddr:
					acc.sensors.append(sensor)

		return accessories

	def __init__(self, sensor):
		self.bridge= sensor.bridge
		self.primary_id= sensor.id
		self.sensors= [ sensor ]

	def name(self):
		return self.primary().name

	def productname(self):
		return self.primary().productname

	# Return the primary sensor, which is the first sensor in the list.

	def primary(self):
		return self.sensors[0]

