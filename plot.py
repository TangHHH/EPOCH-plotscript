# -*- coding:UTF-8 -*-
# version: 0.2.0
#python2 need
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

def usage():
	print('''
Usage: python plot.py [-option value ...]
	-h:		 usage.
	-i [value]: plot sdf number. default will plot all sdf files.
	-k [value]: the item which will be ploted. default is all.
	-n [value]: num_processes. default is single processing.
	-o [value]: output_directory. default is 'Img'
	-f [value]: func_name. default is plot_file.
	-r:		 override the exist output image.
	-w [value]: work_directory. default is 'Data'
''')

global wkdir,opdir,pool,num_pro,kw_er,override,single_processing,func_name
single_processing = False
opdir = 'Img'
wkdir = 'Data'
num_pro = 1
override = False
sdfid = None
keyword = None
kw_er = {}
func_name = "plot_file"
if sys.version_info[0] == 3:
	kw_er['error_callback'] = lambda e:print(repr(e))

def spec_plot(fname,keyword=None):
	global pool,kw_er,single_processing,opdir
	hpr.getdata(fname,verbose=False)
	data = hpr.sdfr(hpr.get_old_filename(),mmap=False)
	var = data.Derived_Number_Density_electron1
	plt.set_cmap('plasma')
	plot(hpr.plot2d,var,opdir + "/Number_Density_electron1_%0.4i.png" % fname, kwargs={'iso':False})
	grid = CopyableData.convert(data.Grid_Particles_subset_selected_electron1)
	grid = grid.toBlockPointVariable()
	var = histogram([grid[0],data.Particles_Px_subset_selected_electron1], bins=500, range=None, normed=False, weightVar=data.Particles_Weight_subset_selected_electron1)
	try:
		plt.set_cmap('dist')
	except:
		reg_cmap_dist()
		plt.set_cmap('dist')

	plot(hpr.plot2d,var,opdir + "/dist_%0.4i.png" % fname,kwargs={'iso':False,'plotkws':{'norm':matplotlib.colors.LogNorm()}})

def unit_convert(var,convertGrid=True):
	'''存在BUG'''
	unitslist = [
		('J','eV', 1/hpr.q0),
		('kg.m/s','eV/c', hpr.c/hpr.q0 ), 
		('K','eV/kB', hpr.kb/hpr.q0)
		]
	for unit_from, unit_to, coefficient in unitslist:
		if var.units == unit_from:
			var.data = np.multiply(coefficient, var.data)
			var.units = unit_to
		if convertGrid:
			grid = var.grid
			dims = len(grid.dims)
			for i in range(dims):
				if grid.units[i] == unit_from:
					grid.data = list(grid.data)
					grid.data[i] = np.multiply(coefficient, grid.data[i])
					grid.data = tuple(grid.data)
					grid.units = list(grid.units)
					grid.units[i] = unit_to
					grid.units = tuple(grid.units)
					grid.extents = list(grid.extents)
					grid.extents[i] = grid.extents[i] * coefficient
					grid.extents[i+dims] = grid.extents[i+dims] * coefficient
					grid.extents = tuple(grid.extents)

def reg_cmap_dist():
	iname = 'rainbow'
	oname = 'dist'
	low = 0.25
	high = 1.0
	#(position, [r,g,b,a] or #rrggbb)
	special = [(0,[1,1,1,1])]

	cmap = plt.get_cmap(iname)
	N = int((high - low) * 256)
	values = np.linspace(low,high,N)
	colors = cmap(values)
	colorlist = [(values[i],colors[i]) for i in range(N)]
	colorlist = special + colorlist
	cmap = plt.cm.colors.LinearSegmentedColormap.from_list(oname,colorlist)
	#An other example: mpl.colors.LinearSegmentedColormap.from_list('cmap', ['#FFFFFF', '#98F5FF', '#00FF00', '#FFFF00','#FF0000', '#8B0000'], 256)
	plt.cm.register_cmap(cmap=cmap)
	return cmap

def plot(func,var,output_fname,xscale=None,yscale=None,kwargs={}):
	try:
		global override
		if not os.path.isfile(output_fname) or override:
			unit_convert(var)
			func(var,**kwargs)
			if xscale is not None:
				plt.xscale(xscale)
			if yscale is not None:
				plt.yscale(yscale)
			plt.savefig(output_fname)	
	except Exception as e:
		print("[Error in file %s] %s" % (output_fname,e))
		#raise


def plot_file(fname,keyword=None):
	global pool,kw_er,single_processing
	data = hpr.getdata(fname,verbose=False)
	for key,var in data.__dict__.items():
		if keyword is not None and key != keyword:
			continue
		if not key.startswith('CPU') and var.__class__.__name__ == 'BlockPlainVariable':
			if single_processing:
				plot_img(fname,key)
			else:
				pool.apply_async(plot_img,(fname,key),**kw_er)

def plot_img(fname,key):
	"""
	sdf模块中的类由C链接库创建，无法在进程间拷贝，并且sdf_helper模块中的
	函数用到了global变量，在画图前需要先调用getdata函数，因此需要在进程开
	始调用getdata函数
	"""
	global opdir
	hpr.getdata(fname,verbose=False)
	data = hpr.sdfr(hpr.get_old_filename(),mmap=False)
	var = data.__dict__[key]
	iso = None
	norm = None
	plotkws = {}
	xscale = None
	yscale = None
	if key.startswith('dist_fn'):
		try:
			plt.set_cmap('dist')
		except:
			reg_cmap_dist()
			plt.set_cmap('dist')
		
		s=list()
		for i in var.dims:
			if i == 1:
				s.append(0)
			else:
				s.append(slice(None))
		var.data = var.data[s]
		var.dims = var.grid.dims
		plotkws['norm'] = matplotlib.colors.LogNorm()
		if len(var.dims) == 1:
			yscale = 'log'
		iso = False
	elif key.startswith('Electric_Field') or key.startswith('Magnetic_Field') or key.startswith('Current') or key.startswith('Derived_Poynting_Flux'):
		plt.set_cmap('bwr')
		norm = 0
		iso = False
	elif key.startswith('Derived_Number_Density'):
		plt.set_cmap('plasma')
		plotkws['norm'] = matplotlib.colors.LogNorm()
	elif key.startswith('Derived_Temperature'):
		plt.set_cmap('gist_heat')
		plotkws['norm'] = matplotlib.colors.LogNorm()
	else:
		plt.set_cmap('viridis')

	if len(var.dims) == 1:
		plot(hpr.plot1d,var,opdir + "/%s_%0.4i.png" % (key,fname),yscale=yscale)
	elif len(var.dims) == 2:
		plot(hpr.plot2d,var,opdir + "/%s_%0.4i.png" % (key,fname),kwargs={'iso':iso,'norm':norm,'plotkws':plotkws})
	elif len(var.dims) == 3:
		plot(hpr.plot2d,var,opdir + "/%s_iy_%0.4i.png" % (key,fname),kwargs={'iso':iso,'fast':False,'iy':-1,'norm':norm,'plotkws':plotkws})
		plot(hpr.plot2d,var,opdir + "/%s_ix_%0.4i.png" % (key,fname),kwargs={'iso':iso,'fast':False,'ix':200,'norm':norm,'plotkws':plotkws})
		plot(hpr.plot2d,var,opdir + "/%s_iz_%0.4i.png" % (key,fname),kwargs={'iso':iso,'fast':False,'iz':-1,'norm':norm,'plotkws':plotkws})

if __name__ == "__main__":
	starttime = time.time()
	opts, args = getopt.getopt(sys.argv[1:], "hrsk:f:i:w:o:n:")
	for op, value in opts:
		if op == "-w":
			wkdir = value
		elif op == "-o":
			opdir = value
		elif op == "-n":
			num_pro = int(value)
		elif op == "-f":
			func_name = value
		elif op == "-r":
			override = True
		elif op == "-i":
			sdfid = int(value)
		elif op == "-k":
			keyword = value
		elif op == "-h":
			usage()
			sys.exit()

	if num_pro == 1:
		single_processing = True
	hpr.set_wkdir(wkdir)
	if not single_processing:
		pool = multiprocessing.Pool(processes = num_pro)
	if not os.path.isdir(opdir):
		os.makedirs(opdir)
	listdir =  os.listdir(hpr.get_wkdir())
	if sdfid is None:
		for fl in listdir:
			if fl.endswith('.sdf'):
				globals()[func_name](int(fl[:-4]),keyword=keyword)
	elif "%0.4i.sdf" % sdfid in listdir:
		globals()[func_name](sdfid,keyword=keyword)
	else:
		print("File %0.4i.sdf not exists." % sdfid)

	if not single_processing:
		pool.close()
		pool.join()
	
	endtime = time.time()
	print("The program runs in %.2f seconds." % (endtime - starttime))
