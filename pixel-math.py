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

# do the calculation for each pixel of a drawable (old version)
def calc_layer_old(src, dst, rexpr, gexpr, bexpr):
    cols,bpc=color_depth(dst)
    print(cols,bpc)
    val_max=2^(8*bpc)
    #val_max=256
    #rgb=pdb.gimp_drawable_is_rgb(dst)
    #alpha=pdb.gimp_drawable_has_alpha(dst)
    w=pdb.gimp_drawable_width(dst)
    h=pdb.gimp_drawable_height(dst)
    r=g=b=a=0
    pdb.gimp_progress_init("working...",None)
    for y in range(h):
        for x in range(w):
            bpp,pixel=pdb.gimp_drawable_get_pixel(src,x,y)
            r=float(pixel[0])/val_max
            if cols > 1:
                g=float(pixel[1])/val_max
                b=float(pixel[2])/val_max
            pixel=[eval(rexpr)*val_max]
            if cols > 1:
                pixel+=[eval(gexpr)*val_max]
                pixel+=[eval(bexpr)*val_max]
            if cols==2 or cols==4:
                pixel+=[val_max-1]
            pdb.gimp_drawable_set_pixel(dst,x,y,bpp,pixel)
            pass
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
            r,g,b,a=pixel_to_color(bpc,pixel)
            r=float(r)/val_max
            if cols > 1:
                g=float(g)/val_max
                b=float(b)/val_max
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
    "Python implementation of Pixel Math",
    "Dietmar",
    "",
    "2020",
    "Pixel Math",
    "RGB*, GRAY*",
    [
        (PF_IMAGE,    "image",    "Input image",    None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_STRING,   "red",      "R:",             "r"),
        (PF_STRING,   "green",    "G:",             "g"),
        (PF_STRING,   "blue",     "B:",             "b"),
        (PF_STRING,   "layer",    "Layer:",         ""),
        ],
    [],
    pixel_math,
    menu="<Image>/Tools"
    )

main()

        
