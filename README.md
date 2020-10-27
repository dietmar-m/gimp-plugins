# gimp-plugins
Plugins for GIMP
pixel-math.py:
An implementation of something like PixInsights' PixelMath as a GIMP-plugin written in python.
For the evaluation of expressions the python-function 'expr()' is used, so every valid python-expression returning a numeric value is allowed. Pixel values are converted to floats between 0.0 and 1.0 before beeing evaluated. Expression-results outside this range are clipped. Colors in expressions are references by R, G and B (all upper case).

You can convert an RGB-image to grayscale by using the expressions:
R=(R+G+B)/3
G=(R+G+B)/3
B=(R+G+B)/3
or:
R=max(R,G,B)
G=max(R,G,B)
B=max(R,G,B)

Or you can assign all values to a single color:
R=(R+G+B)/3
G=0
B=0

Since I have no idea how to determine a float from a 32-bit-int currentlyonly integer types (8, 16 or 32 bit) are allowed. Because for every pixel an expresion must be parsed (and python is a scripting language) it is rather slow, better do not use it on large images.

Have fun and CS
Dietmar
