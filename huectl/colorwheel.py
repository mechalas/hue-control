# The 12-Hue Color Wheel (Step 3) designed by Warren Mars. The full 24-hue
# color-corrected wheel is something that may happen some day.
#
# http://warrenmars.com/visual_art/theory/colour_wheel/evolution/evolution.htm
#
# Note that these color names will generally be "in the ballpark" but
# occasionally will be off, esp in the yellow-green space since Hue
# lights tend to have a narrow green gamut.

colors= (
	( 'ham', 'pale raspberry', 'red', 'dark red', 'maroon' ),
	( 'pale buff', 'buff', 'tumeric', 'yellow ochre', 'milk chocolate' ),
	( 'cream', 'butter', 'yellow', 'wasabi', 'olive' ),
	( 'pale avacado', 'avacado', 'chartreuse', 'sage', 'oak leaf' ),
	( 'extra pale green', 'green hellbore', 'granny smith', 'green', 'zucchini' ),
	( 'pale variscite', 'variscite', 'crysolite', 'light emerald', 'brunswick green' ),
	( 'extra pale cyan', 'blue sprice light', 'cyan', 'dark cyan', 'pthalo green' ),
	( 'powder blue', 'light azure', 'azure', 'cobalt blue', 'prussian blue' ),
	( 'forget-me-not', 'cornflower', 'blue', 'ultramarine', 'navy' ),
	( 'mauve', 'kunzite', 'violet', 'dark violet', 'spectral violet' ),
	( 'light musk', 'musk', 'magenta', 'dark magenta', 'purple' ),
	( 'light pink', 'pink', 'dark pink', 'prickly pear', 'elderberry' )
)

hueangles= (0, 20, 50, 70, 100, 140, 170, 190, 220, 260, 290, 310, 340, 360)

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
		if isinstance(arg0, tuple) or isinstance(arg0, list):
			h, s, b= arg0
	elif len(args) == 3:
		h, s, b= args
	else:
		raise ValueError

	if h > 360:
		h-= 360*int(h/360)

	if h < 0:
		h+= 360*int(h/360)

	for i in range(0,len(hueangles)-1):
		if h >= hueangles[i] and h < hueangles[i+1]:
			hueidx= i
			break

	if i >= len(colors):
		i-= len(colors)

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

