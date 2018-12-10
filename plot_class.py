#python2 need
from __future__ import print_function
#python3 need
from functools import reduce
import numpy as np


class CopyableData:
	@classmethod
	def convert(cls,orgdata):
		mod = __import__(cls.__module__)
		cs = getattr(mod,orgdata.__class__.__name__,None)
		if cs is None:
			cvtdata = cls()
		else:
			cvtdata = cs()
		for item in dir(orgdata):
			if not item.startswith('_'):
				try:
					var = getattr(orgdata,item,None)
				except:
					var = None
				if var.__class__.__module__ == 'sdf':
					setattr(cvtdata,item,cls.convert(var))
				else:
					setattr(cvtdata,item,var)
		return cvtdata

class BlockPointMesh:
	def __init__(self,data=None,geometry=1,id=None,labels=None,mult=None,name=None,species_id=None,units=None):
		self.set_data(data)
		self.geometry = geometry
		self.id = id
		self.labels = labels
		self.mult = mult
		self.name = name
		self.species_id = species_id
		self.units = units

	def set_data(self,data):
		self.data = data
		if data is None:
			self.data_length = None
			self.datatype = None
			self.dims = None
			self.extents = None
		else:
			self.data_length = sum([d.size * d.itemsize for d in data])
			self.datatype = getattr(__import__(data[0].__class__.__module__),data[0].dtype.name,None)
			self.dims = reduce(lambda x,y:x+y,[d.shape for d in data])
			self.extents = tuple([np.min(d) for d in data]+[np.max(d) for d in data])

	def toBlockPointVariable(self):
		length = len(self.dims)
		rtnList = list()
		for i in range(length):
			var = BlockPointVariable()
			var.data = self.data[i]
			var.data_length = self.data_length/3
			var.datatype = self.datatype
			var.dims = (self.dims[i],)
			var.grid = self
			var.grid_id = self.id
			var.id = self.labels[i] + '/' + self.species_id.lower()
			var.mult = self.mult[i]
			var.name = 'Particles/' + self.labels[i] + self.name[14:]
			var.species_id = self.species_id
			var.units = self.units[i]
			rtnList.append(var)
		return rtnList

class BlockPlainMesh:
	def __init__(self,data=None,geometry=1,id=None,labels=None,mult=None,name=None,stagger=None,units=None,extents=None):
		'''data must be tuple'''
		self.set_data(data)
		self.geometry = geometry
		self.id = id
		self.labels = labels
		self.mult = mult
		self.name = name
		self.stagger = stagger
		self.units = units
		if extents is not None:
			self.extents = extents

	def shrink(self,step=None):
		"""step must be tuple or list of int."""
		if step is None:
			return
		self.set_data(tuple([self.data[i][::step[i]] for i in range(len(self.dims))]))

	def transpose(self,axes):
		self.set_data(tuple([self.data[i] for i in axes]))


	def set_data(self,data):
		self.data = data
		if data is None:
			self.data_length = None
			self.datatype = None
			self.dims = None
			self.extents = None
		else:
			self.data_length = sum([d.size * d.itemsize for d in data])
			self.datatype = getattr(__import__(data[0].__class__.__module__),data[0].dtype.name,None)
			self.dims = reduce(lambda x,y:x+y,[d.shape for d in data])
			self.extents = tuple([d[0] for d in data] + [d[-1] for d in data])

	def si_prefix(self):
		l = len(self.dims)
		mult = [1]*l
		sym = ['']*l
		for i in range(l):
			length = abs(self.extents[i+l] - self.extents[i])
			#length = max(abs(self.extents[i]),abs(self.extents[i+l]))
			mult[i], sym[i] = get_si_prefix(length)
		self.set_data(tuple([self.data[i]*mult[i] for i in range(l)]))
		self.units = tuple([sym[i] + self.units[i] for i in range(l)])

	def toBlockPointMesh(self):
		arli = list()
		for i in range(len(self.dims)):
			arrays = self.data[i]
			for j in range(len(self.dims)):
				if i!=j:
					arrays=np.stack([arrays for k in range(self.dims[j])],axis=j)
			arli.append(arrays.ravel())
		return BlockPointMesh(tuple(arli),geometry=self.geometry,id=self.id,labels=self.labels,
			mult=self.mult,name=self.name,species_id='plain',units=self.units)

	def toBlockPlainVariable(self,i):
		arrays = self.data[i]
		for j in range(len(self.dims)):
			if i!=j:
				arrays=np.stack([arrays for k in range(self.dims[j])],axis=j)
		return BlockPlainVariable(arrays,id=self.labels[i],mult=self.mult[i],name=self.name[i],units=self.units[i])

class BlockPointVariable:
	def __init__(self,data=None,grid=None,grid_id=None,
		grid_mid=None,id=None,mult=None,name=None,species_id=None,units=None):
		self.set_data(data)
		self.grid = grid
		self.grid_id = grid_id
		self.grid_mid = grid_mid
		self.id = id
		self.mult = mult
		self.name = name
		self.species_id = species_id
		self.units = units

	def set_data(self,data):
		self.data = data
		if data is None:
			self.data_length = None
			self.datatype = None
			self.dims = None
		else:
			self.data_length = data.size * data.itemsize
			self.datatype = getattr(__import__(data.__class__.__module__),data.dtype.name,None)
			self.dims = data.shape

	def cutrange(self,_min=None,_max=None,_abs=False):
		if _min is None and _max is None:
			return
		if _abs:
			self._cutrange(lambda x: (_min is None or abs(x[0]) > _min) and (_max is None or abs(x[0]) < _max))
		else:
			self._cutrange(lambda x: (_min is None or x[0] > _min) and (_max is None or x[0] < _max))

	def _cutrange(self,func):
		arr = np.stack([self.data]+[i for i in self.grid.data],axis=1)
		flr = filter(func, arr)
		arr = np.array([i for i in flr])
		self.set_data(arr[:,0])
		self.grid.set_data(tuple([arr[:,i+1] for i in range(len(self.grid.dims))]))

class BlockPlainVariable:
	def __init__(self,data=None,grid=None,grid_id=None,id=None,mult=1.0,name=None,units=None):
		self.set_data(data)
		self.grid = grid
		self.grid_id = grid_id
		if grid is not None and grid.dims != self.dims:
			self.grid_mid = BlockPlainMesh(
				data = tuple([(d[1:] + d[:-1])/2 for d in grid.data]),
				extents = grid.extents,
				id = grid.id + '_mid',
				name = grid.name + '_mid',
				mult = grid.mult,
				units = grid.units,
				labels = grid.labels
			)
		else:
			self.grid_mid = None			
		self.id = id
		self.mult = mult
		self.name = name
		self.units = units

	def set_data(self,data):
		self.data = data
		if data is None:
			self.data_length = None
			self.datatype = None
			self.dims = None
		else:
			self.data_length = data.size * data.itemsize
			self.datatype = getattr(__import__(data.__class__.__module__),data.dtype.name,None)
			self.dims = data.shape

	def shrink(self,step=None):
		"""step must be tuple or list of int."""
		if step is None:
			return
		ss = [slice(None,None,i) for i in step]
		self.set_data(self.data[ss])
		if self.grid_mid is None:
			self.grid.shrink(step=step)
		else:
			self.grid_mid.shrink(step=step)

	def transpose(self,axes):
		self.set_data(np.transpose(self.data,axes))
		if self.grid_mid is None:
			self.grid.transpose(axes)
		else:
			self.grid_mid.transpose(axes)

	def toBlockPointVariable(self):
		if self.grid_mid is None:
			grid = self.grid
		else:
			grid = self.grid_mid
		return BlockPointVariable(self.data.ravel(),grid=grid.toBlockPointMesh(),grid_id=self.grid_id,
			id=self.id,mult=self.mult,name=self.name,species_id='plain',units=self.units)

def histogram(pointVarList, bins=10, range=None, normed=False, weightVar=None):
	dims =len(pointVarList)
	sample = [ pv.data for pv in pointVarList ]
	labels = [ pv.id[:pv.id.find('/')] for pv in pointVarList]
	varname = reduce(lambda x,y:x+'_'+y,labels) + '/' + pointVarList[0].species_id
	if isinstance(weightVar,np.ndarray):
		weights = weightVar
	else:
		weights = weightVar.data

	if dims == 1:
		hist, bin_edges = np.histogram(sample[0], bins=bins, range=range, normed=normed, weights=weights)
		edges = [bin_edges]
	if dims == 2:
		hist, xedges, yedges = np.histogram2d(sample[0],sample[1], bins=bins, range=range, normed=normed, weights=weights)
		edges = [xedges,yedges]
	else:
		sample = np.vstack(sample)
		sample.transpose()
		hist, edges = np.histogramdd(sample, bins=bins, range=range, normed=normed, weights=weights)
	
	grid = BlockPlainMesh(
		data = tuple(edges),
		id = 'grid/' + varname,
		name = 'Grid/' + varname,
		mult = tuple([1.0 for edge in edges]),
		units = tuple([pv.units for pv in pointVarList]),
		labels = tuple(labels)
	)

	var = BlockPlainVariable(
		grid = grid,
		data = hist,
		id = varname,
		name = 'dist_fn/' + varname,
		units = 'npart/cell'
	)

	return var

def get_si_prefix(scale, full_units=False):
    scale = abs(scale)
    mult = 1
    sym = ''

    if scale < 1e-24:
        full_units = True
    elif scale < 1e-21:
        # yocto
        mult = 1e24
        sym = 'y'
    elif scale < 1e-19:
        # zepto
        mult = 1e21
        sym = 'z'
    elif scale < 1e-16:
        # atto
        mult = 1e18
        sym = 'a'
    elif scale < 1e-13:
        # femto
        mult = 1e15
        sym = 'f'
    elif scale < 1e-10:
        # pico
        mult = 1e12
        sym = 'p'
    elif scale < 1e-7:
        # nano
        mult = 1e9
        sym = 'n'
    elif scale < 1e-4:
        # micro
        mult = 1e6
        sym = '{\mu}'
    elif scale < 1e-1:
        # milli
        mult = 1e3
        sym = 'm'
    elif scale >= 1e27:
        full_units = True
    elif scale >= 1e24:
        # yotta
        mult = 1e-24
        sym = 'Y'
    elif scale >= 1e21:
        # zetta
        mult = 1e-21
        sym = 'Z'
    elif scale >= 1e18:
        # exa
        mult = 1e-18
        sym = 'E'
    elif scale >= 1e15:
        # peta
        mult = 1e-15
        sym = 'P'
    elif scale >= 1e12:
        # tera
        mult = 1e-12
        sym = 'T'
    elif scale >= 1e9:
        # giga
        mult = 1e-9
        sym = 'G'
    elif scale >= 1e6:
        # mega
        mult = 1e-6
        sym = 'M'
    elif scale >= 1e3:
        # kilo
        mult = 1e-3
        sym = 'k'

    if full_units:
        scale = scale * mult
        if scale <= 0:
            pwr = 0
        else:
            pwr = (-np.floor(np.log10(scale)))
        mult = mult * np.power(10.0, pwr)
        if np.rint(pwr) != 0:
            sym = "(10^{%.0f})" % (-pwr) + sym

    return mult, sym