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

# get the number of colors and the bytes per color from a drawable
def color_depth(layer):
    if pdb.gimp_drawable_is_rgb(layer):
        cols=3
    else:
        cols=1
    if pdb.gimp_drawable_has_alpha(layer):
        cols+=1
    bpc=pdb.gimp_drawable_bpp(layer)/cols
    return cols,bpc

# get the colors from a byte-tuple of a pixel
def pixel_to_color(bpc,pixel):
    color=[0,0,0,0]
    for c in range(len(pixel)/bpc):
        for n in range(bpc-1,-1,-1):
            color[c]=(color[c]<<8)+pixel[c*bpc+n]
    return tuple(color)

# make a byte-tuple of a pixel from colors
def color_to_pixel(bpc,color):
    pixel=[]
    for c in color:
        for n in range(0,bpc):
            pixel+=[c & 0xff]
            c>>=8
    return tuple(pixel)

# copy a layer (not longer needed)
def copy_layer(src, dst):
    w=pdb.gimp_drawable_width(dst)
    h=pdb.gimp_drawable_height(dst)
    pdb.gimp_progress_init("working...",None)
    for y in range(h):
        for x in range(w):
            d,p=pdb.gimp_drawable_get_pixel(src,x,y)
            pdb.gimp_drawable_set_pixel(dst,x,y,d,p)
        pdb.gimp_progress_update(float(y)/h)

# do the calculation for each pixel of a drawable
def calc_layer(src, dst, rexpr, gexpr, bexpr):
    cols,bpc=color_depth(dst)
    val_max=2**(8*bpc)
    w=pdb.gimp_drawable_width(dst)
    h=pdb.gimp_drawable_height(dst)
    pdb.gimp_progress_init("working...",None)
    for y in range(h):
        for x in range(w):
            bpp,pixel=pdb.gimp_drawable_get_pixel(src,x,y)
            R,G,B,A=pixel_to_color(bpc,pixel)
            R=float(R)/val_max
            if cols > 1:
                G=float(G)/val_max
                B=float(B)/val_max
            pixel=[int(eval(rexpr)*val_max)]
            if cols > 1:
                pixel+=[int(eval(gexpr)*val_max)]
                pixel+=[int(eval(bexpr)*val_max)]
            for n in range(len(pixel)):
                if pixel[n]>=val_max: pixel[n]=val_max-1
                if pixel[n]<0: pixel[n]=0
            pdb.gimp_drawable_set_pixel(dst,x,y,bpp,
                                        color_to_pixel(bpc,tuple(pixel)))
        pdb.gimp_progress_update(float(y)/h)

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
    calc_layer(draw,layer,rexpr,gexpr,bexpr)

# the main-function
register(
    "didi_pixel_math",
    "Pixel Math",
    "Implementation of something like PixInsight's Pixel Math",
    "Dietmar Muscholik",
    "",
    "Oct 2020",
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

        
