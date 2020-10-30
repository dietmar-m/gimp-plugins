#!/usr/bin/python
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
#           attempt to speed up using threads
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
from threading import Thread
from time import *
#from time import sleep


max_cpus=8

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
##def calc_layer(layer_src, layer_dst, expr_r, expr_g, expr_b):
##    cols,bpc=color_depth(layer_dst)
##    val_max=2**(8*bpc)
##    reg_src=layer_src.get_pixel_rgn(0, 0, layer_src.width, layer_src.height)
##    reg_dst=layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)
##    pdb.gimp_progress_init("working...",None)
##    for y in range(reg_dst.h):
##        for x in range(reg_dst.w):
##            if bpc==1: pixel=array('B',reg_src[x,y])
##            elif bpc==2: pixel=array('H',reg_src[x,y])
##            elif bpc==4: pixel=array('L',reg_src[x,y])
##            else: raise TypeError("Invalid size for pixel value")
##
##            R=float(pixel[0])/val_max
##            if cols > 1:
##                G=float(pixel[1])/val_max
##                B=float(pixel[2])/val_max
##
##            pixel=[int(eval(expr_r)*val_max)]
##            if cols > 1:
##                pixel+=[int(eval(expr_g)*val_max)]
##                pixel+=[int(eval(expr_b)*val_max)]
##
##            if cols > 3:
##                pixel+=[val_max-1]
##
##            for n in range(len(pixel)):
##                if pixel[n]>=val_max: pixel[n]=val_max-1
##                if pixel[n]<0: pixel[n]=0
##
##            if bpc==1: reg_dst[x,y]=array('B',pixel).tostring()
##            elif bpc==2: reg_dst[x,y]=array('H',pixel).tostring()
##            elif bpc==4: reg_dst[x,y]=array('L',pixel).tostring()
##            else: raise TypeError("Invalid size for pixel value")
##
##        pdb.gimp_progress_update(float(y)/reg_dst.h)


class Calc(Thread):
    def __init__(self, str_src, y_min, y_max, cols, bpc,
                 expr_r, expr_g, expr_b,
                 progress=FALSE):
        Thread.__init__(self)
        if bpc==1: typecode='B'
        elif bpc==2: typecode='H'
        elif bpc==4: typecode='L'
        self.a_src=array(typecode, str_src)
        self.y_min=y_min
        self.y_max=y_max
        self.cols=cols
        self.expr_r=expr_r
        self.expr_g=expr_g
        self.expr_b=expr_b
        self.progress=progress
        self.val_max=2**(8*bpc)
        self.bpp=cols*bpc
        #self.a_dst=array('H', (0 for i in range(len(self.a_src))))
        self.a_dst=array(typecode, str_src)
        self.start()

    def result(self): return self.a_dst.tostring()
    
    def run(self):
        #print(self.ident,"run()")
        color=[]
        for i in range(self.cols):
            color+=[0]

        count=0        
        for pixel in range(0, len(self.a_dst), self.cols):
            R=float(self.a_src[pixel])/self.val_max
            if self.cols > 0:
                G=float(self.a_src[pixel+1])/self.val_max
                B=float(self.a_src[pixel+2])/self.val_max
                
            color[0]=int(eval(self.expr_r)*self.val_max)
            if self.cols > 0:
                color[1]=int(eval(self.expr_g)*self.val_max)
                color[2]=int(eval(self.expr_b)*self.val_max)
                
            for i in range(len(color)):
                if color[i] >= self.val_max: color[i]=self.val_max-1
                if color[i] < 0: color[i]=0
                self.a_dst[pixel+i]=color[i]

            if self.progress and count % 1000 == 0:
                #print(float(count*self.cols)/len(self.a_dst))
                pdb.gimp_progress_update(float(count*self.cols)/len(self.a_dst))
                #pdb.gimp_displays_flush()
            count+=1

# plugin-function
def pixel_math(image, draw_src, expr_r, expr_g, expr_b, name, num_threads):
    #print(asctime())
    try:
        expr_r=compile(expr_r,"<STRING>","eval")
        expr_g=compile(expr_g,"<STRING>","eval")
        expr_b=compile(expr_b,"<STRING>","eval")
    except:
        pdb.gimp_message("Error in expression")
        return

    pdb.gimp_plugin_enable_precision()
    layer_dst=pdb.gimp_image_get_layer_by_name(image,name)
    if layer_dst==None:
        layer_dst=pdb.gimp_layer_new(image,
                                     draw_src.width,
                                     draw_src.height,
                                     draw_src.type,
                                     name,
                                     100,
                                     pdb.gimp_layer_get_mode(draw_src))
        pdb.gimp_image_insert_layer(image,layer_dst,None,0)

        t_start=time()

    #calc_layer(draw_src,layer_dst,rexpr,gexpr,bexpr)

    reg_src=draw_src.get_pixel_rgn(0, 0, draw_src.width, draw_src.height)
    reg_dst=layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)
    cols,bpc=color_depth(layer_dst)

    pdb.gimp_progress_init("working...",None)

    num_threads=int(num_threads)
    threads=[]
    y=0
    h=reg_dst.h/num_threads
    for t in range(num_threads-1):
        #print("starting thread",t)
        threads+=[Calc(reg_src[0:reg_src.w, y:y+h],
                       y, y+h,
                       cols, bpc,
                       expr_r, expr_g, expr_b)]
        y+=h
    threads+=[Calc(reg_src[0:reg_src.w, y:reg_src.h],
                   y, reg_dst.h,
                   cols, bpc,
                   expr_r, expr_g, expr_b, progress=TRUE)]

    for t in threads:
        t.join()
        reg_dst[0:reg_dst.w, t.y_min:t.y_max]=t.result()

    #print("done")
    #print(asctime())
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
        (PF_ADJUSTMENT, "threads",  "Threads:",       1, (1, max_cpus, 1)),
        ],
    [],
    pixel_math,
    menu="<Image>/Tools"
    )

main()
