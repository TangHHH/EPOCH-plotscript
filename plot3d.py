# -*- coding:UTF-8 -*-
from __future__ import print_function
#python3 need
from functools import reduce
import matplotlib
matplotlib.use('AGG')
import sdf_helper as hpr
import matplotlib.pyplot as plt
import numpy as np
import multiprocessing
import sys, getopt
import os, time

from plot_class import *
from mpl_toolkits.mplot3d import Axes3D

def usage():
	print('''
Usage: python plot3d.py [-option value ...]
	-h:		 usage.
	-i [value]: plot sdf number. default will plot all sdf files.
	-k [value]: the item which will be ploted. default is all.
	-n [value]: num_processes. default is os.cpu_count()
	-o [value]: output_directory. default is 'Img'
	-r:		 override the exist output image.
	-s:		 not multiprocessing.
	-w [value]: work_directory. default is 'Data'
''')

global wkdir,opdir,pool,num_pro,kw_er,override,single_processing
single_processing = False
opdir = 'Img'
wkdir = 'Data'
num_pro = None
override = False
sdfid = None
keyword = None
kw_er = {}
if sys.version_info[0] == 3:
	kw_er['error_callback'] = lambda e:print(repr(e))

def point_scatter3D(var,elev=None,azim=None,hold=False,iso=False,norm=None,plotkws={}):
	cmap = plt.get_cmap()
	if norm is not None:
		v0 = np.min(var.data) - norm
		v1 = np.max(var.data) - norm
		if abs(v0/v1) > 1:
			low = 0
			high = 0.5 * (1 - v1/v0)
		else:
			low = 0.5 * (1 + v0/v1)
			high = 1.0

		cmap = plt.cm.colors.LinearSegmentedColormap.from_list('tr',
				cmap(np.linspace(low,high,256)))

	if not hold:
		try:
			plt.clf()
		except:
			pass
	grid = var.grid
	fig = plt.gcf()
	ax = plt.gca(projection='3d')
	ax.view_init(elev=elev, azim=azim)
	im = ax.scatter(grid.data[0], grid.data[1], grid.data[2], c=var.data, cmap=cmap, **plotkws)
	ax.set_xlabel(grid.labels[0] + ' $(' + grid.units[0] + ')$')
	ax.set_ylabel(grid.labels[1] + ' $(' + grid.units[1] + ')$')
	ax.set_zlabel(grid.labels[2] + ' $(' + grid.units[2] + ')$')
	plt.title(var.name + ' $(' + var.units + ')$, ' + hpr.get_title(),
				  fontsize='large', y=1.03)
	plt.axis('tight')
	if iso:
		plt.axis('image')

	if not hold:
		plt.colorbar(im)
	fig.set_tight_layout(True)
	#plt.draw()

def reg_cmap_transparent(iname,alpha):
	oname = iname + '_transparent'
	cmap = plt.get_cmap(iname)
	values = np.linspace(0,1,256)
	colors = cmap(values)
	for i in range(256):
		colors[i][3] = alpha[i]
	colorlist = [(values[i],colors[i]) for i in range(256)]
	cmap = plt.cm.colors.LinearSegmentedColormap.from_list(oname,colorlist)
	plt.cm.register_cmap(cmap=cmap)
	return cmap

def create_alpha(func):
	"""alpha可见的最低值是0.002"""
	return [ 1 if func(i)>1 else 0 if func(i)<0 else func(i) for i in range(256)]


def plot3d(fname,key,_abs=True,index=3,xshrink=1,yshrink=1,zshrink=1,log=False):
	hpr.getdata(fname,verbose=False)
	data = hpr.sdfr(hpr.get_old_filename(),mmap=False)
	var = data.__dict__[key]
	var = CopyableData.convert(var)
	var.shrink((xshrink,yshrink,zshrink))
	var.grid.si_prefix()
	var.grid_mid.si_prefix()
	var = var.toBlockPointVariable()
	plotkws = {'marker':'.','edgecolors':'none'}
	norm = None

	if _abs:
		norm = 0
		_min = max(np.max(var.data),np.min(var.data))**(0.002**(1.0/index)) if log else max(np.max(var.data),np.min(var.data))*0.002**(1.0/index)
		plt.set_cmap(reg_cmap_transparent('bwr',create_alpha(lambda x:abs(x/127.5-1)**index)))
	else:
		_min = np.max(var.data)**(0.002**(1.0/index)) if log else np.max(var.data)*0.002**(1.0/index)
		plt.set_cmap(reg_cmap_transparent('plasma_r',create_alpha(lambda x:abs(x/255.0)**index)))
		
		#special code
		_min = max(_min,1.1e27*0.8)
		var._cutrange(lambda x : x[1] < 3)

	if log:
		plotkws['norm'] = matplotlib.colors.LogNorm()

	var.cutrange(_min=_min,_abs=_abs)
	point_scatter3D(var,norm=norm,plotkws=plotkws)


def plot3d_img(fname,key):
	global opdir, override
	output_fname = opdir + "/%s_%0.4i.png" % (key,fname)
	if not os.path.isfile(output_fname) or override:
		if key.startswith('Electric_Field') or key.startswith('Magnetic_Field'):
			plot3d(fname,key,_abs=True,index=3,xshrink=1,yshrink=2,zshrink=2)
			plt.savefig(output_fname)
		elif key.startswith('Derived_Number_Density'):
			plot3d(fname,key,_abs=False,index=1,xshrink=1,yshrink=1,zshrink=1)
			plt.savefig(output_fname)

def plot3d_file(fname,keyword=None):
	global pool,kw_er,single_processing,override
	data = hpr.getdata(fname,verbose=False)
	for key,var in data.__dict__.items():
		if keyword is not None and key != keyword:
			continue
		if not key.startswith('CPU') and var.__class__.__name__ == 'BlockPlainVariable':
			if single_processing:
				plot3d_img(fname,key)
			else:
				pool.apply_async(plot3d_img,(fname,key),**kw_er)

if __name__ == '__main__':
	starttime = time.time()
	opts, args = getopt.getopt(sys.argv[1:], "hrsk:i:w:o:n:")
	for op, value in opts:
		if op == "-w":
			wkdir = value
		elif op == "-o":
			opdir = value
		elif op == "-n":
			num_pro = int(value)
		elif op == "-r":
			override = True
		elif op == "-i":
			sdfid = int(value)
		elif op == "-s":
			single_processing = True
		elif op == "-k":
			keyword = value
		elif op == "-h":
			usage()
			sys.exit()

	hpr.set_wkdir(wkdir)
	if not single_processing:
		pool = multiprocessing.Pool(processes = num_pro)
	if not os.path.isdir(opdir):
		os.makedirs(opdir)
	listdir =  os.listdir(hpr.get_wkdir())
	if sdfid is None:
		for fl in listdir:
			if fl.endswith('.sdf'):
				plot3d_file(int(fl[:-4]),keyword=keyword)
	elif "%0.4i.sdf" % sdfid in listdir:
		plot3d_file(sdfid,keyword=keyword)
	else:
		print("File %0.4i.sdf not exists." % sdfid)

	if not single_processing:
		pool.close()
		pool.join()
	
	endtime = time.time()
	print("The program runs in %.2f seconds." % (endtime - starttime))
