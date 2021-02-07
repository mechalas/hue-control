# The 24-Hue Color Wheel designed by Warren Mars.
#
# http://warrenmars.com/visual_art/theory/colour_wheel/evolution/evolution.htm
#
# Note that these color names will generally be "in the ballpark" but
# occasionally will be off, esp in the yellow-green space since Hue
# lights tend to have a narrow green gamut.

colors= (
	( 'ham', 'pale raspberry', 'red', 'dark red', 'maroon' ),
	( 'parmesan cheese', 'peanut butter', 'orange', 'brown', 'dark brown' ),
	( 'buff', 'turmeric', 'yellow ochre', 'tan', 'milk chocolate' ),
	( 'wheat ear', 'yellow cheese', 'olive oil', 'cane toad', 'cow dung' ),
	( 'butter', 'yellow', 'wasabi', 'olive', 'olive drab' ),
	( 'champagne', 'golden delicious', 'green grape', 'light kelp', 'dark kelp' ),
	( 'avacado', 'chartreuse', 'celery', 'sage', 'oak leaf' ),
	( 'green cabbage', 'green pea', 'basil', 'spinach', 'rhubarb leaf' ),
	( 'green hellebore', 'granny smith', 'green', 'green grass', 'zucchini' ),
	( 'celadon', 'chayote', 'clover', 'shaded fern', 'cucumber' ),
	( 'variscite', 'crysolite', 'light emerald', 'emerald', 'brunswick green' ),
	( 'blue agave', 'verdigris', 'shallow sea green', 'broccoli', 'malachite' ),
	( 'blue sprice light', 'cyan', 'dark cyan', 'blue spruce dark', 'pthalo green' ),
	( 'uranus', 'turquoise', 'blue topaz', 'sea green', 'dark sea green' ),
	( 'powder blue', 'light azure', 'dark azure', 'cobalt blue', 'prussian blue' ),
	( 'pale sky blue', 'sky blue', 'delphinium blue', 'royal blue', 'dark royal blue' ),
	( 'forget-me-not', 'cornflower', 'light blue', 'blue', 'dark blue' ),
	( 'rose de france', 'lavender', 'dark lavender', 'han purple', 'dioxazine' ),
	( 'mauve', 'kunzite', 'violet', 'dark violet', 'spectral violet' ),
	( 'lilac', 'rose of sharon', 'purple daisy', 'aniline', 'amethyst' ),
	( 'musk', 'magenta', 'dark magenta', 'light purple', 'purple' ),
	( 'dog rose', 'purple loosestrife', 'shocking pink', 'purple bougainvillea', 'purple bean' ),
	( 'light pink', 'pink', 'dark pink', 'prickly pear', 'elderberry' ),
	( 'baby pink', 'pink hydrangea', 'dragon fruit', 'chinese strawberry', 'red plum' )
)

#hueangles= (0, 30, 42, 50, 60, 65, 76, 98, 120, 147, 160, 172, 180, 190, 200, 214, 240, 267, 280, 290, 300, 310, 320, 333, 360)
hueangles= (0, 15, 36, 46, 55, 62.5, 68, 87, 109, 133.5, 153.5, 166, 176, 185, 195, 207, 227, 253.5, 273.5, 285, 295, 305, 315, 326.5, 346.5, 360)

# colors are arranged at:
#   S=0.25,B=1.0
#   S=0.50,B=1.0
#   S=1.0, B=1.0
#   S=1.0, B=0.66
#   S=1.0, B=0.33

pts=((0.25,1.0),(0.50,1.0),(1.0,1.0),(1.0,0.66),(1.0,0.33))

def colorname(*args):
	if len(args) == 1:
		arg0= args[0]
		if isinstance(arg0, (tuple, list)):
			h, s, b= arg0
	elif len(args) == 3:
		h, s, b= args
	else:
		raise ValueError

	if h >= 360:
		h-= 360*int(h/360)

	if h < 0:
		h+= 360*int(h/360)

	for i in range(0,len(hueangles)-1):
		if h >= hueangles[i] and h < hueangles[i+1]:
			hueidx= i
			break

	if hueidx >= len(colors):
		hueidx-= len(colors)

	# Get Euclidean distance to each variation in the hue and pick
	# the closest one

	dmin= None
	i= 0
	for pt in pts:
		d= pow(s-pt[0],2)+pow(b-pt[1],2)
		if dmin is None:
			dmin= d
			idx= i
		elif d < dmin:
			dmin= d
			idx= i
		i+= 1

	return colors[hueidx][idx]

