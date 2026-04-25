from matplotlib.colors import ListedColormap
from cmap import Colormap #https://cmap-docs.readthedocs.io/en/latest/
import numpy as np
import settings

label_cmap = ListedColormap(["black","xkcd:beige", "xkcd:royal", "xkcd:claret", "xkcd:light brown", "xkcd:mustard yellow", "xkcd:brick orange", "xkcd:rust", "xkcd:pale cyan", "xkcd:grass", "xkcd:light lavendar", "xkcd:bright lavender", "xkcd:shit", "xkcd:lavender", "xkcd:jade green", "xkcd:dark orange", "xkcd:teal blue", "xkcd:caramel", "xkcd:yellowish tan", "xkcd:fire engine red", "xkcd:bile", "xkcd:foam green", "xkcd:toupe", "xkcd:barbie pink", "xkcd:khaki", "xkcd:light mint green", "xkcd:bright sky blue", "xkcd:reddish brown", "xkcd:sand", "xkcd:purpleish", "xkcd:creme", "xkcd:mint", "xkcd:purple/blue", "xkcd:greeny grey", "xkcd:rosa", "xkcd:light lime", "xkcd:cool blue", "xkcd:celadon", "xkcd:butterscotch", "xkcd:orange", "xkcd:dark forest green", "xkcd:sickly yellow", "xkcd:pinkish brown", "xkcd:greyish green", "xkcd:cloudy blue", "xkcd:faded orange", "xkcd:pinkish grey", "xkcd:sunny yellow", "xkcd:puke", "xkcd:pale blue", "xkcd:pastel orange", "xkcd:off blue", "xkcd:wine red", "xkcd:eggshell blue", "xkcd:steel blue", "xkcd:dark lavender", "xkcd:pinkish purple", "xkcd:rose red", "xkcd:sage green", "xkcd:aqua marine", "xkcd:really light blue", "xkcd:faded pink", "xkcd:light beige", "xkcd:blue violet", "xkcd:orangey brown"],N=64)
LUTs = {
    "Green": Colormap('green'),
    "Magenta": Colormap(['black','magenta','white']),
    "Cyan": Colormap(['black','cyan','white']),
    "Grey": Colormap('gray'),
    "Black": Colormap(['black','black'])}

outline_cmap = ListedColormap(['black','yellow'], N = 2)

adjacent_cmap=[]

for item in np.linspace(1, 0, int(settings.adjacency["adjacency_cells"]) + 1):
    adjacent_cmap.append((0, item, 0))

adjacent_cmap.append("black")
adjacent_cmap = ListedColormap(adjacent_cmap)