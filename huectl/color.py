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
			if isinstance(arg0, (tuple, list)):
				for ar in arg0:
					if len(ar) != 2:
						raise ValueError

				self.R= HueColorPoint(arg0[0])
				self.G= HueColorPoint(arg0[1])
				self.B= HueColorPoint(arg0[2])

				self.invalid= False

		elif len(args) == 3:
			for ar in args:
				if not isinstance(ar, (tuple, list)):
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
# HueColor: A color defined by a HueColorPoint and brightness. Colors
#           are stored in the bridge's units and converted on demand.
#===========================================================================

class HueColor:
	range_bri= (1, 254)

	def __init__(self, *args):
		self.pt= None
		self.bri= 0

	def brightness(self, torange=None):
		if torange == None:
			return self.bri

		return map_range(self.bri, HueColor.range_bri, torange)

# Value, RangeIn (start,end), RangeOut (start,end)
def map_range(val, rin, rout):
	val= rout[0] + ((rout[1]-rout[0])/(rin[1]-rin[0])) * (val-rin[0])
	if val > rout[1]:
		val= rout[1]
	elif val < rout[0]:
		val= rout[0]

	return val

#----------------------------------------
# HueColorxyY: A color in the xyY space
#----------------------------------------

class HueColorxyY(HueColor):
	def __init__(self, *args):
		super().__init__()

		if len(args) == 1:
			arg0= args[0]

			if isinstance(arg0, HueColorxyY):
				self.pt= HueColorPointxy(arg0.pt)
				self.bri= arg0.bri

			elif type(arg0) == tuple or list:
				if len(arg0) != 3:
					raise ValueError
				for v in args:
					if type(v) not in (int, float):
						raise TypeError('Need int or float, not '+str(type(v)))

				x, y, self.bri= arg0

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

			x, y, self.bri= args

			self.pt= HueColorPointxy(x, y)

	def __str__(self):
		return '<HueColorxyY> x={:.3f}, y={:.3f}, Y={:.3f} ({:s})'.format(
			self.x(), self.y(), self.brightness(torange=(0,1)), self.name())

	def x(self):
		return self.pt.x
	
	def y(self):
		return self.pt.y

	def name(self):
		inh, ins, inb= xyY_to_hsb((self.x(), self.y(), 
			self.brightness(torange=(0,1))))
		return colorname(xyY_to_hsb((self.x(), self.y(),
			self.brightness(torange=(0,1)))))

	def rgb(self):
		return xyY_to_rgb((self.x(), self.y(), self.brightness(torange=(0,1))))

	def hsb(self):
		inh, ins, inb= xyY_to_hsb((self.x(), self.y(), 
			self.brightness(torange=(0,1))))
		return (map_range(inh, (0,360), HueColorHSB.range_hue),
			map_range(ins, (0,1), HueColorHSB.range_sat),
			map_range(inb, (0,1), HueColor.range_bri))

#----------------------------------------
# HueColorHSB: A color represented by hue, saturation and lightness.
#----------------------------------------

class HueColorHSB(HueColor):
	range_hue= (0, 65535)
	range_sat= (0, 254)

	def __init__(self, *args):
		super().__init__()

		if len(args) == 1:
			arg0= args[0]

			if isinstance(arg0, HueColorHSB):
				self.pt= HueColorPointHS(arg0.pt)
				self.bri= arg0.bri

			elif type(arg0) == tuple or list:
				if len(arg0) != 3:
					raise ValueError
				for v in args:
					if type(v) not in (int, float):
						raise TypeError('Need int or float, not'+str(type(v)))

				h, s, self.bri= arg0

				self.pt= HueColorPointHS(h, s)

			else:
				raise TypeError('Need HueColorHSB, tuple, or list')
	
		elif len(args) == 3:
			h, s, self.bri= args

			self.pt= HueColorPointHS(h, s)

		else:
			raise ValueError

	def asdict(self):
		return { 'hue': self.hue(), 'sat': self.sat(), 'bri': self.brightness() }

	def __str__(self):
		return '<HueColorHSB> hue={:.3f}, sat={:.3f}, bri={:.3f} ({:s})'.format(self.hue(torange=(0,360)), self.sat(torange=(0,1)), self.brightness(torange=(0,1)), self.name())

	def hue(self, torange=None):
		if not torange:
			return self.pt.h
		
		return map_range(self.pt.h, HueColorHSB.range_hue, torange)

	def sat(self, torange=None):
		if not torange:
			return self.pt.s

		return map_range(self.pt.s, HueColorHSB.range_sat, torange)

	def name(self):
		return colorname(self.hue(torange=(0,360)), self.sat(torange=(0,1)),
			self.brightness(torange=(0,1)))

	def rgb(self):
		return hsb_to_rgb(self.hue(torange=(0,360)), self.sat(torange=(0,1)),
			self.brightness(torange=(0,1)))
	
	def xyY(self):
		return hsb_to_xyY((self.hue(torange=(0,360)), self.sat(torange=(0,1)),
			self.brightness(torange=(0,1))))

	def cct(self):
		xyY= self.xyY()
		return xy_to_cct(xyY[0:2])

#===========================================================================
# HueColorTemp: Hue White and Hue White with Ambiance 
#===========================================================================

# Hue bulbs use the Mired scale

class HueColorTemp:
	def __init__(self, ct, bri=HueColor.range_bri[1], kelvin=False):
		self.bri= bri

		if type(ct) not in (float, int):
			raise TypeError

		if kelvin:
			self.ct= round(kelvin_to_mired(ct))
		else:
			self.ct= ct

	def __str__(self):
		ct= self.kelvin()
		return f'<HueColorTemp> {ct}K'

	def kelvin(self):
		return round(mired_to_kelvin(self.ct))

	def mired(self):
		return self.ct

	def xy(self):
		return cct_to_xy(self.kelvin())

	def xyY(self):
		xy= self.xy()
		return HueColorxyY(xy[0], xy[1], self.bri)

	def rgb(self):
		return self.xyY().rgb()

	def hsb(self):
		inh, ins, inb= rgb_to_hsb(self.rgb())
		return HueColorHSB(
			map_range(inh, (0, 360), HueColorHSB.range_hue),
			map_range(ins, (0, 1), HueColorHSB.range_sat),
			map_range(inb, (0, 1), HueColor.range_bri)
		)

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
	h= s= v= None

	if len(args) == 1:
		arg0= args[0]
		if isinstance(arg0, (tuple, list)):
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

	while hh >= 360.0:
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
		if isinstance(arg0, (tuple, list)):
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

	# Now convert to XYZ using the D65 transformation matrix

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

	# Using the D65 transformation

	R=  X*1.656492 - Y*0.354851 - Z*0.255038
	G= -X*0.707196 + Y*1.655397 + Z*0.036152
	B=  X*0.051713 - Y*0.121364 + Z*1.011530

	# Normalize by the largest value that is >1.0
	R, G, B= normalize_rgb(R, G, B)

	# Monitors actually use sRGB, so we need to convert back
	# from linear RGB. It's also possible to get a color that
	# is outside the RGB gamut, so deal with that, too.

	r= _from_linear(R)
	g= _from_linear(G)
	b= _from_linear(B)

	r, g, b= normalize_rgb(r, g, b)

	return r, g, b

# Normalize RGB to the range 0 to 1 using the largest value > 1

def normalize_rgb(R,G,B):
	if R>1.0 and R>B and R>G:
		R= 1.0
		G/= R
		B/= R
	elif G>R and G>1.0 and G>B:
		R/= G
		G= 1.0
		B/= G
	elif B>R and B>G and B>1.0:
		R/= B
		G/= B
		B= 1.0

	return R, G, B

# HSB is just a transform of RGB

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

# Kelvin to Mired

def mired_to_kelvin(m):
	return 1000000.0/m

def kelvin_to_mired(k):
	return 1000000.0/k

# x,y to Correlated Color Temperature in Kelvin using McCamy's 
# approximation which is good enough for our purposes. 
#
# The only reason we need these at all is to be able to represent color
# temperature as an RGB color in a GUI. In fact, we likely don't need
# xy_to_cct() at all, but it's here for completeness.
#
# Note that xy_to_cct() and cct_to_xy() are not going to agree, but we 
# really don't care about that for this usage.
#
# Note: McCamy is really only valid for small deltas from the black-body
# curve (delta uv +/- 0.5), so light sources that are "nearly white", from 
# about 2000K to 30000K.

def xy_to_cct(xy):
	x, y= xy
	
	n= (x-0.3320)/(0.1858-y)
	return 437*n*n*n+3601*n*n+6861*n+5517


# The easiest and fastest way to go from CCT to xy is to use lookup tables.
# This one goes from 2000 to 6500 in increments of 10.

CCT_to_xy= (
(0.52667628,0.413297275), (0.525587009,0.413461773),
(0.524501547,0.413618465), (0.523419903,0.413767443),
(0.522342086,0.413908799), (0.521268106,0.414042625),
(0.520197971,0.414169012), (0.519131691,0.414288052),
(0.518069273,0.414399834), (0.517010725,0.414504451),
(0.515956054,0.414601991), (0.514905268,0.414692545),
(0.513858374,0.414776202), (0.512815378,0.414853051),
(0.511776286,0.41492318), (0.510741104,0.414986678),
(0.509709837,0.415043632), (0.508682492,0.41509413),
(0.507659072,0.415138258), (0.506639581,0.415176101),
(0.505624025,0.415207747), (0.504612407,0.415233279),
(0.503604729,0.415252783), (0.502600996,0.415266342),
(0.50160121,0.415274039), (0.500605374,0.415275958),
(0.499613489,0.415272181), (0.498625557,0.415262789),
(0.497641579,0.415247863), (0.496661557,0.415227484),
(0.495685492,0.415201732), (0.494713383,0.415170685),
(0.493745231,0.415134422), (0.492781035,0.415093022),
(0.491820796,0.41504656), (0.490864511,0.414995114),
(0.48991218,0.414938759), (0.488963802,0.414877572),
(0.488019374,0.414811625), (0.487078894,0.414740994),
(0.48614236,0.414665751), (0.485209769,0.414585969),
(0.484281119,0.41450172), (0.483356405,0.414413074),
(0.482435624,0.414320103), (0.481518773,0.414222875),
(0.480605846,0.414121461), (0.47969684,0.414015928),
(0.47879175,0.413906344), (0.477890572,0.413792776),
(0.476993298,0.41367529), (0.476099925,0.413553952),
(0.475210446,0.413428827), (0.474324856,0.413299979),
(0.473443148,0.413167472), (0.472565315,0.413031368),
(0.471691352,0.41289173), (0.47082125,0.412748618),
(0.469955003,0.412602095), (0.469092603,0.412452219),
(0.468234043,0.41229905), (0.467379315,0.412142648),
(0.46652841,0.411983069), (0.465681321,0.411820372),
(0.464838039,0.411654612), (0.463998555,0.411485847),
(0.46316286,0.411314131), (0.462330946,0.41113952),
(0.461502803,0.410962066), (0.460678421,0.410781825),
(0.459857792,0.410598847), (0.459040905,0.410413186),
(0.45822775,0.410224893), (0.457418317,0.410034019),
(0.456612596,0.409840614), (0.455810577,0.409644727),
(0.455012248,0.409446407), (0.4542176,0.409245703),
(0.453426621,0.409042663), (0.452639301,0.408837333),
(0.451855627,0.40862976), (0.45107559,0.408419989),
(0.450299176,0.408208067), (0.449526376,0.407994037),
(0.448757177,0.407777944), (0.447991568,0.407559832),
(0.447229536,0.407339742), (0.446471069,0.407117718),
(0.445716156,0.406893801), (0.444964784,0.406668033),
(0.444216942,0.406440454), (0.443472615,0.406211104),
(0.442731793,0.405980023), (0.441994462,0.405747249),
(0.441260611,0.405512822), (0.440530225,0.405276779),
(0.439803292,0.405039158), (0.439079799,0.404799995),
(0.438359734,0.404559326), (0.437643083,0.404317189),
(0.436929834,0.404073617), (0.436219972,0.403828646),
(0.435513485,0.40358231), (0.434810359,0.403334643),
(0.434110581,0.403085679), (0.433414138,0.40283545),
(0.432721016,0.402583988), (0.432031202,0.402331326),
(0.431344682,0.402077495), (0.430661442,0.401822526),
(0.429981469,0.401566449), (0.429304749,0.401309295),
(0.428631269,0.401051094), (0.427961015,0.400791874),
(0.427293972,0.400531664), (0.426630128,0.400270493),
(0.425969468,0.400008388), (0.425311978,0.399745378),
(0.424657645,0.399481488), (0.424006455,0.399216747),
(0.423358394,0.398951179), (0.422713447,0.398684812),
(0.422071602,0.39841767), (0.421432844,0.398149778),
(0.420797159,0.397881162), (0.420164533,0.397611845),
(0.419534952,0.397341851), (0.418908402,0.397071205),
(0.41828487,0.396799929), (0.417664341,0.396528045),
(0.417046802,0.396255578), (0.416432238,0.395982547),
(0.415820635,0.395708977), (0.41521198,0.395434887),
(0.414606259,0.395160299), (0.414003457,0.394885233),
(0.413403561,0.394609711), (0.412806557,0.394333752),
(0.412212431,0.394057375), (0.411621169,0.393780601),
(0.411032757,0.393503449), (0.410447182,0.393225937),
(0.409864429,0.392948084), (0.409284485,0.392669907),
(0.408707337,0.392391426), (0.408132969,0.392112657),
(0.40756137,0.391833618), (0.406992524,0.391554326),
(0.406426418,0.391274797), (0.405863039,0.390995049),
(0.405302374,0.390715097), (0.404744407,0.390434958),
(0.404189127,0.390154646), (0.403636518,0.389874177),
(0.403086569,0.389593568), (0.402539265,0.389312831),
(0.401994593,0.389031982), (0.40145254,0.388751036),
(0.400913092,0.388470006), (0.400376237,0.388188907),
(0.39984196,0.387907751), (0.399310248,0.387626553),
(0.398781089,0.387345326), (0.398254468,0.387064082),
(0.397730374,0.386782834), (0.397208793,0.386501596),
(0.396689712,0.386220378), (0.396173118,0.385939193),
(0.395658998,0.385658053), (0.395147339,0.38537697),
(0.394638128,0.385095955), (0.394131353,0.384815019),
(0.393627,0.384534173), (0.393125058,0.384253428),
(0.392625512,0.383972795), (0.392128352,0.383692284),
(0.391633563,0.383411906), (0.391141134,0.38313167),
(0.390651052,0.382851586), (0.390163305,0.382571664),
(0.38967788,0.382291914), (0.389194765,0.382012344),
(0.388713948,0.381732964), (0.388235416,0.381453784),
(0.387759158,0.381174811), (0.38728516,0.380896054),
(0.386813412,0.380617522), (0.3863439,0.380339224),
(0.385876613,0.380061167), (0.38541154,0.379783359),
(0.384948667,0.379505808), (0.384487984,0.379228523),
(0.384029479,0.37895151), (0.383573139,0.378674776),
(0.383118953,0.37839833), (0.38266691,0.378122178),
(0.382216998,0.377846327), (0.381769205,0.377570784),
(0.381323521,0.377295556), (0.380879932,0.377020649),
(0.380438429,0.37674607), (0.379999,0.376471825),
(0.379561634,0.376197919), (0.379126319,0.37592436),
(0.378693044,0.375651153), (0.378261799,0.375378304),
(0.377832571,0.375105819), (0.377405351,0.374833702),
(0.376980127,0.37456196), (0.376556888,0.374290598),
(0.376135624,0.37401962), (0.375716324,0.373749033),
(0.375298977,0.373478841), (0.374883572,0.373209049),
(0.374470099,0.372939661), (0.374058547,0.372670683),
(0.373648906,0.372402119), (0.373241165,0.372133972),
(0.372835314,0.371866249), (0.372431342,0.371598953),
(0.37202924,0.371332087), (0.371628997,0.371065657),
(0.371230602,0.370799666), (0.370834046,0.370534117),
(0.370439319,0.370269016), (0.37004641,0.370004364),
(0.36965531,0.369740167), (0.369266009,0.369476427),
(0.368878496,0.369213148), (0.368492762,0.368950334),
(0.368108798,0.368687987), (0.367726593,0.36842611),
(0.367346138,0.368164708), (0.366967423,0.367903782),
(0.366590439,0.367643335), (0.366215176,0.367383372),
(0.365841625,0.367123893), (0.365469776,0.366864903),
(0.36509962,0.366606404), (0.364731148,0.366348397),
(0.364364351,0.366090887), (0.363999218,0.365833874),
(0.363635742,0.365577362), (0.363273913,0.365321353),
(0.362913721,0.365065849), (0.362555159,0.364810852),
(0.362198217,0.364556364), (0.361842886,0.364302387),
(0.361489157,0.364048924), (0.361137022,0.363795976),
(0.360786471,0.363543545), (0.360437497,0.363291632),
(0.36009009,0.36304024), (0.359744242,0.362789371),
(0.359399944,0.362539024), (0.359057188,0.362289204),
(0.358715965,0.36203991), (0.358376267,0.361791144),
(0.358038086,0.361542908), (0.357701413,0.361295203),
(0.35736624,0.361048031), (0.357032559,0.360801391),
(0.356700361,0.360555287), (0.356369639,0.360309718),
(0.356040385,0.360064687), (0.35571259,0.359820193),
(0.355386246,0.359576239), (0.355061346,0.359332824),
(0.354737882,0.359089951), (0.354415845,0.358847619),
(0.354095228,0.35860583), (0.353776024,0.358364584),
(0.353458224,0.358123882), (0.353141821,0.357883725),
(0.352826807,0.357644114), (0.352513175,0.357405048),
(0.352200917,0.35716653), (0.351890025,0.356928559),
(0.351580493,0.356691135), (0.351272313,0.35645426),
(0.350965477,0.356217933), (0.350659979,0.355982156),
(0.35035581,0.355746928), (0.350052964,0.355512249),
(0.349751434,0.355278121), (0.349451212,0.355044543),
(0.349152291,0.354811516), (0.348854665,0.35457904),
(0.348558325,0.354347114), (0.348263266,0.35411574),
(0.347969481,0.353884917), (0.347676961,0.353654645),
(0.347385702,0.353424924), (0.347095695,0.353195755),
(0.346806934,0.352967137), (0.346519412,0.352739071),
(0.346233123,0.352511556), (0.34594806,0.352284592),
(0.345664216,0.352058179), (0.345381585,0.351832317),
(0.345100161,0.351607005), (0.344819936,0.351382245),
(0.344540904,0.351158034), (0.344263059,0.350934374),
(0.343986395,0.350711264), (0.343710905,0.350488703),
(0.343436583,0.350266692), (0.343163422,0.35004523),
(0.342891417,0.349824316), (0.342620561,0.34960395),
(0.342350848,0.349384133), (0.342082272,0.349164863),
(0.341814827,0.348946139), (0.341548507,0.348727963),
(0.341283305,0.348510332), (0.341019217,0.348293247),
(0.340756235,0.348076708), (0.340494354,0.347860713),
(0.340233569,0.347645261), (0.339973873,0.347430354),
(0.33971526,0.347215989), (0.339457726,0.347002167),
(0.339201263,0.346788886), (0.338945867,0.346576146),
(0.338691531,0.346363947), (0.338438251,0.346152288),
(0.33818602,0.345941168), (0.337934833,0.345730586),
(0.337684684,0.345520542), (0.337435569,0.345311035),
(0.337187481,0.345102064), (0.336940415,0.344893629),
(0.336694366,0.344685728), (0.336449328,0.344478362),
(0.336205296,0.344271529), (0.335962265,0.344065228),
(0.335720229,0.343859459), (0.335479184,0.34365422),
(0.335239124,0.343449512), (0.335000043,0.343245333),
(0.334761938,0.343041682), (0.334524802,0.342838558),
(0.33428863,0.342635962), (0.334053418,0.34243389),
(0.333819161,0.342232344), (0.333585853,0.342031321),
(0.33335349,0.341830822), (0.333122066,0.341630844),
(0.332891577,0.341431387), (0.332662018,0.341232451),
(0.332433384,0.341034034), (0.332205671,0.340836135),
(0.331978873,0.340638753), (0.331752985,0.340441888),
(0.331528004,0.340245538), (0.331303924,0.340049702),
(0.33108074,0.33985438), (0.330858449,0.33965957),
(0.330637045,0.339465271), (0.330416524,0.339271482),
(0.330196881,0.339078203), (0.329978111,0.338885432),
(0.329760212,0.338693168), (0.329543176,0.338501411),
(0.329327002,0.338310158), (0.329111683,0.338119409),
(0.328897215,0.337929163), (0.328683595,0.337739419),
(0.328470818,0.337550176), (0.328258879,0.337361433),
(0.328047774,0.337173188), (0.327837499,0.336985441),
(0.32762805,0.33679819), (0.327419423,0.336611435),
(0.327211612,0.336425173), (0.327004615,0.336239405),
(0.326798427,0.336054129), (0.326593044,0.335869343),
(0.326388461,0.335685048), (0.326184675,0.335501241),
(0.325981682,0.335317921), (0.325779478,0.335135088),
(0.325578058,0.33495274), (0.325377419,0.334770876),
(0.325177557,0.334589495), (0.324978468,0.334408596),
(0.324780147,0.334228177), (0.324582592,0.334048238),
(0.324385798,0.333868777), (0.324189761,0.333689793),
(0.323994478,0.333511285), (0.323799944,0.333333252),
(0.323606157,0.333155692), (0.323413112,0.332978605),
(0.323220805,0.33280199), (0.323029233,0.332625844),
(0.322838393,0.332450167), (0.32264828,0.332274958),
(0.322458891,0.332100216), (0.322270222,0.331925939),
(0.32208227,0.331752126), (0.321895031,0.331578777),
(0.321708502,0.331405889), (0.321522678,0.331233461),
(0.321337558,0.331061493), (0.321153136,0.330889984),
(0.32096941,0.330718931), (0.320786376,0.330548335),
(0.320604031,0.330378193), (0.320422371,0.330208504),
(0.320241393,0.330039268), (0.320061094,0.329870483),
(0.31988147,0.329702148), (0.319702518,0.329534261),
(0.319524234,0.329366822), (0.319346616,0.329199829),
(0.31916966,0.329033282), (0.318993363,0.328867178),
(0.318817721,0.328701517), (0.318642732,0.328536298),
(0.318468391,0.328371519), (0.318294697,0.328207178),
(0.318121646,0.328043276), (0.317949234,0.327879811),
(0.317777459,0.327716781), (0.317606317,0.327554185),
(0.317435806,0.327392023), (0.317265922,0.327230292),
(0.317096663,0.327068992), (0.316928025,0.326908122),
(0.316760005,0.32674768), (0.3165926,0.326587665),
(0.316425807,0.326428076), (0.316259624,0.326268912),
(0.316094047,0.326110171), (0.315929074,0.325951853),
(0.315764701,0.325793956), (0.315600926,0.325636479),
(0.315437746,0.32547942), (0.315275157,0.32532278),
(0.315113158,0.325166555), (0.314951745,0.325010746),
(0.314790915,0.324855351), (0.314630666,0.324700369),
(0.314470995,0.324545798), (0.314311899,0.324391638),
(0.314153375,0.324237887), (0.313995421,0.324084545),
(0.313838034,0.323931609), (0.313681211,0.323779079),
(0.313524949,0.323626954)
)

def cct_to_xy(cct):
	if cct < 2000 or cct > 6500:
		raise ValueError(cct)

	# Always pick the lower index
	r= int(cct/10)
	idx= int(r-200)
	delta= cct-r*10

	x, y= CCT_to_xy[idx]

	if delta:
		# Linear approx between points
		x1, y1= CCT_to_xy[idx+1]
		x+= (x1-x)*delta/10
		y+= (y1-y)*delta/10

	return x, y

