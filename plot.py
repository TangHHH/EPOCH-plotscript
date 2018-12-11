import sys, getopt
import os, time
from common import plot

def usage():
    print('''
Usage: python plot.py [-option value ...]
    -h,--help:         usage.
    -i [value]: input sdf file.
    -k [value]: the item which will be ploted.
    -o [value]: output filename.
    -x,--xslice [value]: x slice.
    -y,--yslice [value]: y slice.
    -z,--zslice [value]: z slice.
    --vmax [value]
    --vmin [value]
''')

def handle_slice(s):
    s = s.split(',')
    if len(s) == 1:
        return int(s[0])
    elif len(s) == 2:
        return slice(int(s[0]),int(s[1]))
    else:
        return slice(int(s[0]),int(s[1]),int(s[2]))

if __name__ == "__main__":
    starttime = time.time()
    opts, args = getopt.getopt(sys.argv[1:], "hx:y:z:k:i:o:",['help','xslice=','yslice=','zslice=','vmax=','vmin='])
    xslice,yslice,zslice,vmax,vmin = (slice(None),slice(None),slice(None),None,None)
    for op, value in opts:
        if op == "-o":
            output = value
        elif op == "-i":
            filename = value
        elif op == "-k":
            key = value
        elif op in ('-x','--xslice'):
            xslice = handle_slice(value)
        elif op in ('-y','--yslice'):
            yslice = handle_slice(value)
        elif op in ('-z','--zslice'):
            zslice = handle_slice(value)
        elif op == '--vmax':
            vmax = float(value)
        elif op == '--vmin':
            vmin = float(value)
        elif op in ("-h","--help"):
            usage()
            sys.exit()

    plot(filename,key,output,xslice=xslice,yslice=yslice,zslice=zslice,vmax=vmax,vmin=vmin)
    
    endtime = time.time()
#    print("The program runs in %.2f seconds." % (endtime - starttime))
