class BadHTTPResponse(Exception):
	def __init__(self, code):
		msg = f"The bridge returned HTTP response code {code}"

class BadResponse(Exception):
	def __init__(self, text):
		msg= f"The bridge returned an unrecognized response {text}"

class InvalidColorSpec(Exception):
	def __init__(self, colorspec):
		msg = "Invalid color spec "+str(colorspec)

class InvalidOperation(Exception):
	pass

class APIVersion(Exception):
	def __init__(self, have=None, need=None):
		if have is not None:
			if need is not None:
				msg= f"API version {need} required, bridge version is {have}"
			else:
				msg= f"Not supported by bridge API version {have}"
		elif need is not None:
			msg= f"API version {need} required"
		else:
			msg= f"Not supported by bridge API version"

class InvalidObject(Exception):
	pass

class AttrsNotSet(Exception):
	def __init__(self, attrs):
		msg= f"Could not set attributes: {attrs}"

class UnknownOperator(Exception):
	def __init__(self, op):
		msg= f"Unknown operator: {op}"

# The Hue Bridge conveniently provides message text for these

class HueGenericException(Exception):
	def __init__(self, message):
		msg= message

class UnauthorizedUser(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class InvalidJSON(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class ResourceUnavailable(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class MethodNotAvailable(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class MissingParameters(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class ParameterUnavailable(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class ParameterReadOnly(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class TooMany(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class PortalRequired(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

class InternalError(HueGenericException):
	def __init__(self, *args):
		super().__init__(*args)

