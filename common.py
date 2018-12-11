import sdf
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import numpy as np

def plot(filename,key,output,xslice=slice(None),yslice=slice(None),zslice=slice(None),vmin=None,vmax=None):
    sdfdata = sdf.read(filename)
    data = sdfdata.__dict__[key]
    ss = (xslice,yslice,zslice)
    dims = -1
    if len(data.dims) == 3:
        var = data.data[ss]
        if isinstance(ss[0],int):
            if isinstance(ss[1],int):
                if isinstance(ss[2],int):
                    dims = 0
                else:
                    dims = 1
                    i0 = 2
            else:
                if isinstance(ss[2],int):
                    dims = 1
                    i0 = 1
                else:
                    dims = 2
                    i0 = 1
                    i1 = 2
        else:
            if isinstance(ss[1],int):
                if isinstance(ss[2],int):
                    dims = 1
                    i0 = 0
                else:
                    dims = 2
                    i0 = 0
                    i1 = 2
            else:
                if isinstance(ss[2],int):
                    dims = 2
                    i0 = 0
                    i1 = 1
                else:
                    dims = 3
                    i0 = 0
                    i1 = 1
                    i2 = 2

    elif len(data.dims) == 2:
        var = data.data[ss[:2]]
        if isinstance(ss[0],int):
            if isinstance(ss[1],int):
                dims = 0
            else:
                dims = 1
                i0 = 1
        else:
            if isinstance(ss[1],int):
                dims = 1
                i0 = 0
            else:
                dims = 2
                i0 = 0
                i1 = 1
    elif len(data.dims) == 1:
        var = data.data[ss[0]]
        if isinstance(ss[0],int):
            dims = 0
        else:
            dims = 1
            i0 = 0

    if dims == 0:
        print(var)
        return var
    elif dims == 1:
        axis0 = data.grid.data[i0][ss[i0]]
        fig, subplot = plt.subplots()
        plot1d(subplot,axis1,var)
        subplot.set_xlabel(axis1_label)
        fig.savefig(output)
    elif dims == 2:
        axis0 = data.grid.data[i0][ss[i0]]
        axis1 = data.grid.data[i1][ss[i1]]
        if key.startswith('Electric_Field') or key.startswith('Magnetic_Field') or key.startswith('Current') or key.startswith('Derived_Poynting_Flux'):
            axis0 = axis0 * 1e6
            axis1 = axis1 * 1e6
            axis0_label = data.grid.labels[i0] + ' $({\mu}m)$'
            axis1_label = data.grid.labels[i1] + ' $({\mu}m)$'
            norm = 0
            cmap = 'bwr'
            if vmax is not None:
                vmin = - vmax
        else:
            norm = None
            cmap = 'viridis'
        fig, subplot = plt.subplots()
        im = plot2d(subplot,axis0,axis1,var,cmap=cmap,norm=norm,vmin=vmin,vmax=vmax)
        subplot.set_xlabel(axis0_label)
        subplot.set_ylabel(axis1_label)
        fig.colorbar(im)
        fig.savefig(output)
    elif dims == 3:
        pass

def plot2d(subplot,x,y,var,cmap='viridis',norm=None,vmin=None,vmax=None):
    cmap = plt.get_cmap(cmap)
    Y, X = np.meshgrid(y,x)
    if norm is not None:
        if vmax is None:
            vmax = np.max(var)
        else:
            vmax = min(np.max(var),vmax)
        if vmin is None:
            vmin = np.min(var)
        else:
            vmin = max(np.min(var),vmin)
        v0 = vmin - norm
        v1 = vmax - norm
        if abs(v0/v1) > 1:
            low = 0
            high = 0.5 * (1 - v1/v0)
        else:
            low = 0.5 * (1 + v0/v1)
            high = 1.0

        cmap = plt.cm.colors.LinearSegmentedColormap.from_list('tr',
                cmap(np.linspace(low,high,256)))
    im = subplot.pcolormesh(X, Y,var,cmap=cmap, vmin=vmin, vmax=vmax)
    return im
