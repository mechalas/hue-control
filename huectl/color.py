import math
from huectl.colorwheel import colorname

#===========================================================================
# HueColorPoint
#===========================================================================

class HueColorPoint:
	def __init__(self, *args):
		self.pt= list()

		# Validate the constructor arguments. We accept:
		#   HueColorPoint(x,y)
		#   HueColorPoint((x,y))
		#   HueColorPoint([x,y])

		if len(args) == 1:
			arg0= args[0]
			if isinstance(arg0, HueColorPoint):
				self.pt= list(arg0.pt)

			elif type(arg0) == tuple or type(arg0) == list:
				if len(arg0) != 2:
					raise ValueError

				for v in arg0:
					if type(v) not in (float, int):
						raise TypeError

				self.pt= list(arg0)
			else:
				raise TypeError
					
		elif len(args) != 2:
			raise ValueError
		else:
			for v in args:
				if type(v) not in (float, int):
					raise TypeError

			self.pt= list(args)

	def __str__(self):
		return str(tuple(self.pt))

class HueColorPointxy(HueColorPoint):
	def __init__(self, *args):
		super().__init__(*args)

	def __getattr__(self, item):
		if item == 'x':
			return self.pt[0]
		elif item == 'y':
			return self.pt[1]

	def __dict__(self):
		return { 'x': self.pt[0], 'y': self.pt[1] }


class HueColorPointHS(HueColorPoint):
	def __init__(self, *args):
		super().__init__(*args)

	def __getattr__(self, item):
		if item in ('hue', 'h'):
			return self.pt[0]
		elif item in ('sat', 's'):
			return self.pt[1]

	def __dict__(self):
		return { 'hue': self.pt[0], 'sat': self.pt[1] }

#===========================================================================
# HueColorGamut: A color gamut defined by a triangle of HueColorPoint objs
#===========================================================================

class HueColorGamut:
	# Initialize as three tuples, e.g. (Rx,Ry), (Gx,Gy), (Bx,By) OR
	# as one tuple, e.g. ((Rx,Ry), (Gx,Gy), (Bx,By))

	def __init__(self, *args):
		self.R= None
		self.G= None
		self.B= None
		self.invalid= True

		if len(args) == 1:
			arg0= args[0]
			if isinstance(arg0, tuple) or isinstance(arg0, list):
				for ar in arg0:
					if len(ar) != 2:
						raise ValueError

				self.R= HueColorPoint(arg0[0])
				self.G= HueColorPoint(arg0[1])
				self.B= HueColorPoint(arg0[2])

				self.invalid= False

		elif len(args) == 3:
			for ar in args:
				if not ( isinstance(ar, tuple) or isinstance(ar, list) ):
					raise TypeError

				if len(ar) != 2:
					raise ValueError

			self.R= HueColorPoint(args[0])
			self.G= HueColorPoint(args[1])
			self.B= HueColorPoint(args[2])

			self.invalid= False

		elif len(args) == 0:
			# Philips states to use this for unknown bulbs
			self.R= HueColorPoint(1.0, 0.0)
			self.G= HueColorPoint(0.0, 1.0)
			self.B= HueColorPoint(0.0, 0.0)

			self.invalid= False

		if self.invalid:
			raise ValueError

	def __str__(self):
		return f"<HueColorGamut> R={self.R}, G={self.G}, B={self.B}"

	def nearest_color(self, c):
		if not isinstance(c, HueColor):
			raise InvalidColorSpec(c)

		# First, check if the point is within the triangle
		if self._in_triangle(c.pt):
			return(c.pt)

		# Find the closest point on each line in the triangle
		pAB= self._closest_point(self.R, self.G, c.pt)
		pAC= self._closest_point(self.B, self.R, c.pt)
		pBC= self._closest_point(self.G, self.B, c.pt)

		dAB= self._distance(c.pt, pAB)
		dAC= self._distance(c.pt, pAC)
		dBC= self._distance(c.pt, pBC)

		lowest= dAB
		closest= pAB

		if dAC < lowest:
			lowest= dAC
			closest= pAC

		if dBC < lowest:
			lowest= dBC
			closest= pBC

		return HueColorPoint(closest)

	def _closest_point(self, A, B, P):
		AP= HueColorPoint((P.x-A.x, P.y-A.y))
		AB= HueColorPoint((B.x-A.x, B.y-A.y))

		ab2= AB.x*AB.x + AB.y*AB.y
		ap_ab= AP.x*AB.x + AP.y*AB.y

		t= ap_ab/ab2

		if t < 0.0:
			t= 0.0
		elif t > 1.0:
			t= 1.0

		return HueColorPoint((A.x+AB.x*t, A.y+AB.y*t))

	def _distance(self, p1, p2):
		dx= p1.x - p2.x
		dy= p1.y - p2.y

		return math.sqrt(dx*dx + dy*dy)

	def _in_triangle(self, pt):
		d1= self._sign(pt, self.R, self.G)
		d2= self._sign(pt, self.G, self.B)
		d3= self._sign(pt, self.B, self.R)

		has_neg= (d1<0.0) or (d2<0.0) or (d3<0.0)
		has_pos= (d1>0.0) or (d2>0.0) or (d3>0.0)

		return not(has_neg and has_pos)

	def _sign(self, p1, p2, p3):
		return (p1.x-p3.x)*(p2.y-p3.y) - (p2.x-p3.x)*(p1.y-p3.y)


#===========================================================================
# HueColor: A color defined by a HueColorPoint and brightness
#===========================================================================

class HueColor:
	def __init__(self, *args):
		self.pt= None
		self.bri= 0

class HueColorxyY(HueColor):
	def __init__(self, *args):
		super().__init__()

		if len(args) == 1:
			arg0= args[0]

			if isinstance(arg0, HueColorHSB):
				pass

			elif isinstance(arg0, HueColorxyY):
				c= arg0
				self.pt= HueColorPointxy(c.pt)
				#self.bri= c.bri/254.0

			elif type(arg0) == tuple or list:
				if len(arg0) != 3:
					raise ValueError
				for v in args:
					if type(v) not in (int, float):
						raise TypeError

				x, y, bri= arg0
				if x < 0.0 or x > 1.0 or y < 0.0 or y > 1.0 or bri < 0 or bri > 254:
					raise ValueError

				#self.bri= bri/254.0

				self.pt= HueColorPointxy(x, y)

			else:
				raise TypeError
	
		elif len(args) == 2:
			pt, Y= args

			if not isinstance(pt, HueColorPointxy):
				raise TypeError

			if type(Y) not in (int, float):
				raise TypeError
			if Y < 0.0 or Y > 1.0:
				raise ValueError

			self.pt= HueColorPointxy(pt)
			self.bri= Y

		elif len(args) == 3:
			for v in args:
				if type(v) not in (int, float):
					raise TypeError

			x, y, bri= args
			if x < 0.0 or x > 1.0 or y < 0.0 or y > 1.0 or bri < 0 or bri > 254:
				raise ValueError

			#self.bri= bri/254.0
			self.pt= HueColorPointxy(x, y)

	def __getattr__(self, item):
		if item == 'x':
			return self.pt.x
		elif item == 'y':
			return self.pt.y
		elif item == 'Y':
			return self.bri

	def __dict__(self):
		return { 'x': self.x, 'y': self.y, 'Y': self.Y }

	def __str__(self):
		return '<HueColorxyY> x={:.3f}, y={:.3f}, Y={:.3f} ({:s})'.format(
			self.x, self.y, self.Y, colorname(self.hsb()))

	def rgb(self):
		return xyY_to_rgb((self.pt.x, self.pt.y, self.bri))

	def hsb(self):
		return xyY_to_hsb((self.pt.x, self.pt.y, self.bri))

class HueColorHSB(HueColor):
	def __init__(self, *args):
		super().__init__()

		if len(args) == 1:
			arg0= args[0]

			if isinstance(arg0, HueColorHSB):
				self.pt= HueColorPointHS(arg0.pt)
				self.bri= arg0.bri

			elif isinstance(arg0, HueColorxyY):
				pass

			elif type(arg0) == tuple or list:
				if len(arg0) != 3:
					raise ValueError
				for v in args:
					if type(v) not in (int, float):
						raise TypeError

				h, s, self.bri= arg0
				s= min(1,max(s,0))
				self.bri= min(1,max(self.bri,0))
				if h< 0.0:
					raise ValueError(h)

				self.pt= HueColorPointHS(h, s)

			else:
				raise TypeError(arg0)
	
		elif len(args) == 2:
			pt, b= args

			if not isinstance(pt, HueColorPointHS):
				raise TypeError(pt)

			if type(b) not in (int, float):
				raise TypeError(b)
			b= min(1,max(0,b))

			self.pt= HueColorPointHS(pt)
			self.bri= b

		elif len(args) == 3:
			for v in args:
				if type(v) not in (int, float):
					raise TypeError(v)

			h, s, self.bri= args
			s= min(1,max(0,s))
			self.bri= min(1,max(0,self.bri))
			if h< 0.0:
				raise ValueError(h)

			self.pt= HueColorPointHS(h, s)

		else:
			raise ValueError

	def __getattr__(self, item):
		if item == 'h' or item == 'hue':
			return self.pt.h
		elif item == 's' or item == 'sat':
			return self.pt.s
		elif item == 'b':
			return self.bri

	def __dict__(self):
		return { 'hue': self.h, 'sat': self.s, 'bri': self.bri }

	def __str__(self):
		return '<HueColorHSB> hue={:.3f}, sat={:.3f}, bri={:.3f} ({:s})'.format(self.hue, self.sat, self.bri, colorname(self.hue, self.sat, self.bri))

	def rgb(self):
		return hsb_to_rgb(self.hue, self.sat, self.bri)

#===========================================================================
# HueColorTemp: Hue White and Hue White with Ambiance 
#===========================================================================

# Hue bulbs use the Mired scale

class HueColorTemp:
	def __init__(self, ct):
		if type(ct) not in (float, int):
			raise TypeError

		self.ct= ct

	def __str__(self):
		ct= self.kelvin()
		return f'<HueColorTemp> {ct}K'

	def kelvin(self):
		return int(round(mired_to_kelvin(self.ct), 0))

#===========================================================================
# Utility functions
#===========================================================================

def hex_to_rgb(s):
	h= s.lstrip('#')

	if len(h) == 3:
		try:
			return tuple(int(h[i:i+1]*2, 16) for i in (0, 1, 2))
		except:
			pass
	elif len(h) == 6:
		try:
			return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
			ok= True
		except:
			pass

	raise InvalidColorSpec(s)


def rgb_to_hex(rgb):
	r, g, b= rgb

	return('#{:02x}{:02x}{:02x}'.format(round(r*255.0,0), round(g*255.0,0),
		round(b*255.0,0)))


def hsb_to_rgb(*args):
	# Use hsv instead of hsb to avoid confusion with rgb
	h= s= b= None

	if len(args) == 1:
		arg0= args[0]
		if isinstance(arg0, list) or isinstance(arg0, tuple):
			for x in arg0:
				if type(x) not in (int, float):
					raise TypeError
			h, s, v= arg0
		else:
			raise TypeError

	elif len(args) == 3:
		for x in args:
			if type(x) not in (int, float):
				raise TypeError

		h, s, v= args

	else:
		raise ValueError

	if s < 0.0 or s > 1.0 or v < 0.0 or v > 1.0:
		raise ValueError

	if s < 0:
		r, g, b= v, v, v
	else:
		hh= h

	while hh > 360.0:
		hh-= 360.0

	hh/= 60.0
	i = int(hh)
	ff= hh-i
	p= v*(1.0-s)
	q= v*(1.0-(s*ff))
	t= v*(1.0-(s*(1.0-ff)))

	if i == 0:
		r, g, b= v, t, p
	elif i == 1:
		r, g, b= q, v, p
	elif i == 2:
		r, g, b= p, v, t
	elif i == 3:
		r, g, b= p, q, v
	elif i == 4:
		r, g, b= t, p, v
	else:
		r, g, b= v, p, q

	return r, g, b

def rgb_to_hsb(*args):
	r= g= b= None

	if len(args) == 1:
		arg0= args[0]
		if isinstance(arg0, list) or isinstance(arg0, tuple):
			for x in arg0:
				if type(x) not in (int, float):
					raise TypeError
				if x < 0 or x > 1:
					raise ValueError
			r, g, b= arg0
		else:
			raise TypeError

	elif len(args) == 3:
		for x in args:
			if type(x) not in (int, float):
				raise TypeError
			if x < 0 or x > 1:
				raise ValueError

		r, g, b= args

	else:
		raise ValueError

	cmax= max(r, g, b)
	cmin= min(r, g, b)

	v= cmax

	if cmin == cmax:
		return (0.0, 0.0, v)
	
	d= (cmax - cmin)
	s= d / cmax
	rc= (cmax-r) / d
	gc= (cmax-g) / d
	bc= (cmax-b) / d

	if r == cmax:
		h= bc - gc
	elif g == cmax:
		h= 2.0 + rc - bc
	else:
		h= 4.0 + gc - rc
	
	h= (h/6.0) % 1.0

	return h*360, s, v


# Convert sRGB to xyY

def rgb_to_xyY(rgb):
	# Monitors actually use sRGB, so we need to convert to 
	# the linear RGB color space first.

	r, g, b= rgb

	R= _to_linear(r)
	G= _to_linear(g)
	B= _to_linear(b)

	# Now convert to xyz using the D65 transformation matrix

	X= R*0.649926 + G*0.103455 + B*0.197109
	Y= R*0.234327 + G*0.743075 + B*0.022598
	Z=              G*0.053077 + B*1.035763

	t= X+Y+Z

	if t:
		return X/t, Y/t, Y

	return 0.0, 0.0, Y

# Convert xyY to sRGB

def xyY_to_rgb(xyY):
	x, y, Y= xyY

	z= 1.0-x-y
	if y == 0:
		# This is a fudge. Most advice says to set X, Y and Z to 0 when
		# y == 0, but that gives you black, which is not at all 
		# helpful. So, instead, we fudge 0 to a very small number which
		# is "almost" 0. 

		y= .00001

	X= (Y/y)*x
	Z= (Y/y)*z

	R=  X*1.656492 - Y*0.354851 - Z*0.255038
	G= -X*0.707196 + Y*1.655397 + Z*0.036152
	B=  X*0.051713 - Y*0.121364 + Z*1.011530

	# Monitors actually use sRGB, so we need to convert back
	# from linear RGB. It's also possible to get a color that
	# is outside the RGB gamut, so deal with that, too.

	r= min(1,max(0,_from_linear(R)))
	g= min(1,max(0,_from_linear(G)))
	b= min(1,max(0,_from_linear(B)))

	return r, g, b

def hsb_to_xyY(hsb):
	rgb= hsb_to_rgb(hsb)
	return rgb_to_xyY(rgb)

def xyY_to_hsb(xyY):
	rgb= xyY_to_rgb(xyY)
	return rgb_to_hsb(rgb)

def _to_linear(v):
	if v <= 0.04045:
		return v/12.92

	return math.pow((v + 0.055)/1.055, 2.4)

def _from_linear(v):
	if v <= 0.0031308:
		return 12.92*v

	return 1.055 * math.pow(v, 1.0/2.4) - 0.055

def mired_to_kelvin(m):
	return 1000000.0/m

def kelvin_to_mired(k):
	return 1000000.0/k

