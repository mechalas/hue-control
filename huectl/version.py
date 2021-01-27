
class HueApiVersion:
	def __init__(self, versionstr):
		self.version= None
		major= 0
		minor= 0
		patch= 0

		verarr= versionstr.split('.')
		if len(verarr) > 3:
			raise ValueError

		major= int(verarr[0])

		if len(verarr) >= 2:
			minor= int(verarr[1])

		if len(verarr) == 3:
			patch= int(verarr[2])

		self.version= (major, minor, patch)

	def __str__(self):
		return '.'.join(list(map(lambda x: str(x), self.version)))

	def _make_version(self, arg):
		if isinstance(arg, HueApiVersion):
			return arg
		else:
			return HueApiVersion(arg)

	def __eq__(self, arg):
		cmpver= self._make_version(arg)
		for a,b in zip(self.version, cmpver.version):
			if a != b:
				return False
		return True

	def __ne__(self, arg):
		cmpver= self._make_version(arg)
		for a,b in zip(self.version, cmpver.version):
			if a != b:
				return True
		return False

	def __gt__(self, arg):
		cmpver= self._make_version(arg)
		for a,b in zip(self.version, cmpver.version):
			if a > b:
				return True
			elif a < b:
				return False

		return False

	def __lt__(self, arg):
		cmpver= self._make_version(arg)
		for a,b in zip(self.version, cmpver.version):
			if a < b:
				return True
			elif a > b:
				return False

		return False

	def __ge__(self, arg):
		cmpver= self._make_version(arg)
		for a,b in zip(self.version, cmpver.version):
			if a < b:
				return False

		return True

	def __le__(self, arg):
		cmpver= self._make_version(arg)
		for a,b in zip(self.version, cmpver.version):
			if a > b:
				return False

		return True

