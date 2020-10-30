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
# \date     2020-10-29
#           major speed improvement by converting regions to arrays
#           as a whole
# \date     2020-10-20
#           support for floating point precision added
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
##def color_depth(layer):
##    if layer.is_rgb:
##        cols=3
##    else:
##        cols=1
##    if layer.has_alpha:
##        cols+=1
##    bpc=layer.bpp/cols
##    return cols,bpc


# do the calculation for each pixel of a drawable
def calc_layer(layer_src, layer_dst, expr_r, expr_g, expr_b):
    prec=pdb.gimp_image_get_precision(layer_src.image)
##    pdb.gimp_message("precision="+str(prec))
##    pdb.gimp_message("bpp="+str(layer_src.bpp))
    if prec in [100,150]:
        typecode='B'
        val_max=2**8
    elif prec in [200,250]:
        typecode='H'
        val_max=2**16
##    elif prec in [300,350]:
##        typecode='L'
        val_max=2**32
    elif prec in [600,650]:
        typecode='f'
        val_max=1
##    else: raise TypeError("Invalid size for pixel value")
    else: raise TypeError("Invalid precision: "+str(prec)+
                          " (bpp="+str(layer_src.bpp)+")")

    if layer_src.is_rgb: cols=3
    else: cols=1
    if layer_src.has_alpha: cols+=1

##    cols,bpc=color_depth(layer_dst)
##    val_max=2**(8*bpc)
##    if bpc==1: typecode='B'
##    elif bpc==2: typecode='H'
##    elif bpc==4: typecode='L'
##    else: raise TypeError("Invalid size for pixel value")

    reg_src=layer_src.get_pixel_rgn(0, 0, layer_src.width, layer_src.height)
    reg_dst=layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)
    a_src=array(typecode,reg_src[:,:])
    a_dst=array(typecode,reg_src[:,:])

    color=[]
    for i in range(cols):
        color+=[0]
    
    pdb.gimp_progress_init("working...",None)
    count=0

    for pixel in range(0, len(a_src), cols):
        R=float(a_src[pixel])/val_max
        if cols > 1:
            G=float(a_src[pixel+1])/val_max
            B=float(a_src[pixel+2])/val_max

##        color[0]=int(eval(expr_r)*val_max)
##        if cols > 1:
##            color[1]=int(eval(expr_g)*val_max)
##            color[2]=int(eval(expr_b)*val_max)

        color[0]=eval(expr_r)*val_max
        if cols > 1:
            color[1]=eval(expr_g)*val_max
            color[2]=eval(expr_b)*val_max

        for i in range(len(color)):
            if typecode in "BHL":
                color[i]=int(color[i])
                if color[i] >= val_max: color[i]=val_max-1
                if color[i] < 0 : color[i]=0
            a_dst[pixel+i]=color[i]

        count+=1
        if count % (1<<16) == 0:
            pdb.gimp_progress_update(float(count)*cols/len(a_src))

    reg_dst[:,:]=a_dst.tostring()
        

# plugin-function
def pixel_math(image, draw, rexpr, gexpr, bexpr, name):
    try:
        rexpr=compile(rexpr,"<STRING>","eval")
        gexpr=compile(gexpr,"<STRING>","eval")
        bexpr=compile(bexpr,"<STRING>","eval")
    except Exception as e:
        pdb.gimp_message(str(e))
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
    try:
        calc_layer(draw,layer,rexpr,gexpr,bexpr)
    except Exception as e:
        pdb.gimp_message(str(e))
    t_end=time()
    print(t_end-t_start)


# the main-function
register(
    "pixel-math",
    "Pixel Math",
    "Implementation of something like PixInsight's Pixel Math",
    "Dietmar Muscholik",
    "",
    "2020-10-30",
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
