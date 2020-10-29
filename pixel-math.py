##
# \file     gimp-plugins/pixel-math.py
# \brief    Implementation of something like PixInsight's Pixel Math
# \author   Dietmar Muscholik <d.muscholik@t-online.de>
# \date     2020-10-22
#           started
# \date     2020-10-24
#           Expressions are compiled to speed up things a little bit.
#           Code cleanup.
#           Copyright notice added.
# \date     2020-10-26
#           File header changed to doxygen style
# \date     2020-10-27
#           speed improvement by using regions instead of calling
#           gimp_drawable_get_pixel() and gimp_drawable_set_pixel()
#           for each pixel
#
#    Copyright (C) 2020  Dietmar Muscholik
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from gimpfu import *
from array import *
from time import *


# get the number of colors and the bytes per color from a drawable
def color_depth(layer):
    if layer.is_rgb:
        cols=3
    else:
        cols=1
    if layer.has_alpha:
        cols+=1
    bpc=layer.bpp/cols
    return cols,bpc


# do the calculation for each pixel of a drawable
def calc_layer(layer_src, layer_dst, expr_r, expr_g, expr_b):
    cols,bpc=color_depth(layer_dst)
    val_max=2**(8*bpc)
    reg_src=layer_src.get_pixel_rgn(0, 0, layer_src.width, layer_src.height)
    reg_dst=layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)
    pdb.gimp_progress_init("working...",None)
    for y in range(reg_dst.h):
        for x in range(reg_dst.w):
            if bpc==1: pixel=array('B',reg_src[x,y])
            elif bpc==2: pixel=array('H',reg_src[x,y])
            elif bpc==4: pixel=array('L',reg_src[x,y])
            else: raise TypeError("Invalid size for pixel value")

            R=float(pixel[0])/val_max
            if cols > 1:
                G=float(pixel[1])/val_max
                B=float(pixel[2])/val_max

            pixel=[int(eval(expr_r)*val_max)]
            if cols > 1:
                pixel+=[int(eval(expr_g)*val_max)]
                pixel+=[int(eval(expr_b)*val_max)]

            if cols > 3:
                pixel+=[val_max-1]

            for n in range(len(pixel)):
                if pixel[n]>=val_max: pixel[n]=val_max-1
                if pixel[n]<0: pixel[n]=0

            if bpc==1: reg_dst[x,y]=array('B',pixel).tostring()
            elif bpc==2: reg_dst[x,y]=array('H',pixel).tostring()
            elif bpc==4: reg_dst[x,y]=array('L',pixel).tostring()
            else: raise TypeError("Invalid size for pixel value")

        pdb.gimp_progress_update(float(y)/reg_dst.h)


# plugin-function
def pixel_math(image, draw, rexpr, gexpr, bexpr, name):
    try:
        rexpr=compile(rexpr,"<STRING>","eval")
        gexpr=compile(gexpr,"<STRING>","eval")
        bexpr=compile(bexpr,"<STRING>","eval")
    except:
        pdb.gimp_message("Error in expression")
        return
    pdb.gimp_plugin_enable_precision()
    layer=pdb.gimp_image_get_layer_by_name(image,name)
    if layer==None:
        layer=pdb.gimp_layer_new(image,
                                 pdb.gimp_drawable_width(draw),
                                 pdb.gimp_drawable_height(draw),
                                 pdb.gimp_drawable_type(draw),
                                 name,
                                 100,
                                 pdb.gimp_layer_get_mode(draw))
        pdb.gimp_image_insert_layer(image,layer,None,0)

    t_start=time()
    calc_layer(draw,layer,rexpr,gexpr,bexpr)
    t_end=time()
    print(t_end-t_start)


# the main-function
register(
    "pixel-math",
    "Pixel Math",
    "Implementation of something like PixInsight's Pixel Math",
    "Dietmar Muscholik",
    "",
    "2020-10-22",
    "Pixel Math",
    "RGB*, GRAY*",
    [
        (PF_IMAGE,    "image",    "Input image",    None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_STRING,   "red",      "R:",             "R"),
        (PF_STRING,   "green",    "G:",             "G"),
        (PF_STRING,   "blue",     "B:",             "B"),
        (PF_STRING,   "layer",    "Layer:",         "pixel_math"),
        ],
    [],
    pixel_math,
    menu="<Image>/Tools"
    )

main()
