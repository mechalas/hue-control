from huectl.exception import UnknownOperator, APIVersion

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

	@classmethod
	def supported(cls, otype, version):
		if HueOperator._supported[otype] <= version:
			return True

		return False

class HueCondition:
	def __init__(self, rule=None, address=None, operator=None, value=None):
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

		if not hasattr(HueOperator, op):
			raise UnknownOperator(op)

		if not op.supported(apiver):
			raise APIVersion(bridge.api_version())

		self.address= address
		self.operator= operator
		self.value= value

class HueRuleStatus:
	Enabled= 'enabled'
	Disabled= 'disabled'

class HueRule:
	def __init__(self, ruleid=None, bridge=None, obj=None):
		self.name= None
		self.ruleid= ruleid
		self.lasttriggered= None
		self.creationtime= None
		self.timestriggered= 0
		self.owner= None
		self.status= None
		self.conditions= list()
		self.actions= list()
		self.enabled= HueConditionStatus.Enabled

		if bridge is None:
			raise ValueError('bridge cannot be None')

		self.bridge= bridge

		if obj is None:
			return

		if isinstance(obj, str):
			d= json.loads(obj)
			self._load(d)
		elif isinstance(obj, dict):
			self._load(obj)
		else:
			raise TypeError 

	def load(self, data):
		self.name= data['name']
		if 'lasttriggered' in data:
			self.lasttriggered= HueDateTime(data['lasttriggered'])

		if 'creationtime' in data:
			self.lasttriggered= HueDateTime(data['creationtime'])

		if 'status' in data:
			self.status= data['status']

		self.owner= data['owner']

