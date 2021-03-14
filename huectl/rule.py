from huectl.exception import UnknownOperator, APIVersion
from huectl.version import HueApiVersion
from huectl.time import HueDateTime

class HueOperator:
	Equals= 'eq'
	GreaterThan= 'gt'
	LessThan= 'lt'
	ValueChanged= 'dx'
	DelayedValueChanged= 'ddx'
	Stable= 'stable'
	NotStable= 'not stable'
	TimeIn= 'in'
	TimeNotIn= 'not in'

	_supported= {
		Equals: HueApiVersion('1.13'),
		GreaterThan: HueApiVersion('1.13'),
		LessThan: HueApiVersion('1.13'),
		ValueChanged: HueApiVersion('1.13'),
		DelayedValueChanged: HueApiVersion('1.13'),
		Stable: HueApiVersion('1.13'),
		NotStable: HueApiVersion('1.13'),
		TimeIn: HueApiVersion('1.14'),
		TimeNotIn: HueApiVersion('1.14')
	}

	@staticmethod
	def supported(otype, version):
		if HueOperator._supported[otype] <= version:
			return True

		return False

class HueCondition:
	def __init__(self, rule, address=None, operator=None, value=None):
		self.rule= rule
		self.address=None
		self.operator= None
		self.value= None

		if rule is None:
			raise TypeError('rule cannot be None')

		if address is None:
			raise TypeError('address cannot be None')
		if operator is None:
			raise TypeError('operator cannot be None')

		apiver= self.rule.bridge.api_version()

		if not HueOperator.supported(operator, apiver):
			raise APIVersion(bridge.api_version())

		self.address= address
		self.operator= operator
		if value:
			self.value= value

	def __str__(self):
		s= f'<HueCondition> {self.address} {self.operator}'
		if self.value:
			s+= ' '+self.value
		return s

class HueRuleStatus:
	Enabled= 'enabled'
	Disabled= 'disabled'

class HueRule:
	@staticmethod
	def parse_definition(obj, bridge=None, ruleid=None):
		if isinstance(obj, str):
			d= json.loads(obj)
			self._load(d)
		elif isinstance(obj, dict):
			self._load(obj)
		else:
			raise TypeError 

		rule= HueRule(bridge)

		rule.id= ruleid
		self.name= data['name']

		if 'lasttriggered' in data:
			if data['lasttriggered'] != 'none':
				self.lasttriggered= HueDateTime(data['lasttriggered'])

		if 'creationtime' in data:
			self.lasttriggered= HueDateTime(data['creationtime'])

		if 'status' in data:
			self.status= data['status']

		self.owner= data['owner']

		for cdata in data['conditions']:
			if 'value' in cdata:
				value= cdata['value']
			else:
				value= None

			self.conditions.append(HueCondition(self, address=cdata['address'],
				operator=cdata['operator'], value=value))

	def __init__(self, bridge):
		self.bridge= bridge
		self.name= None
		self.ruleid= None
		self.lasttriggered= None
		self.creationtime= None
		self.timestriggered= 0
		self.owner= None
		self.status= HueRuleStatus.Enabled
		self.conditions= list()
		self.actions= list()

	def __str__(self):
		return f'<HueRule> {self.ruleid} {self.name}, {self.status}'

