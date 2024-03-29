#!/usr/bin/env python

import netCDF4
import numpy
import m6plot
import matplotlib.pyplot as plt

try: import argparse
except: raise Exception('This version of python is not new enough. python 2.7 or newer is required.')

parser = argparse.ArgumentParser(description='''Script for plotting meridional overturning.''')
parser.add_argument('annual_file', type=str, help='''Annually-averaged file containing 3D 'temp' and 'e'.''')
parser.add_argument('-l','--label', type=str, default='', help='''Label to add to the plot.''')
parser.add_argument('-o','--outdir', type=str, default='.', help='''Directory in which to place plots.''')
parser.add_argument('-g','--gridspecdir', type=str, required=True,
  help='''Directory containing mosaic/grid-spec files (ocean_hgrid.nc and ocean_mask.nc).''')
cmdLineArgs = parser.parse_args()

#x = netCDF4.Dataset(cmdLineArgs.gridspecdir+'/ocean_hgrid.nc').variables['x'][::2,::2]
y = netCDF4.Dataset(cmdLineArgs.gridspecdir+'/ocean_hgrid.nc').variables['y'][::2,::2]
msk = netCDF4.Dataset(cmdLineArgs.gridspecdir+'/ocean_mask.nc').variables['mask'][:]
area = msk*netCDF4.Dataset(cmdLineArgs.gridspecdir+'/ocean_hgrid.nc').variables['area'][:,:].reshape([msk.shape[0], 2, msk.shape[1], 2]).sum(axis=-3).sum(axis=-1)
depth = netCDF4.Dataset(cmdLineArgs.gridspecdir+'/ocean_topog.nc').variables['depth'][:]
basin_code = netCDF4.Dataset(cmdLineArgs.gridspecdir+'/basin_codes.v20140629.nc').variables['basin'][:]

rootGroup = netCDF4.Dataset( cmdLineArgs.annual_file )
if 'vh' in rootGroup.variables: varName = 'vh'
else: raise Exception('Could not find "vh" in file "%s"'%(cmdLineArgs.annual_file))
if len(rootGroup.variables[varName].shape)==4: VHmod = rootGroup.variables[varName][:].mean(axis=0).filled(0.)
else: VHmod = rootGroup.variables[varName][:].filled(0.)
if 'e' in rootGroup.variables: Zmod = rootGroup.variables['e'][0]
else: Zmod = rootGroup.variables['e'][0] # Using model z-ou:put

def MOCpsi(vh, vmsk=None):
  """Sums 'vh' zonally and cumulatively in the vertical to yield an overturning stream function, psi(y,z)."""
  shape = list(vh.shape); shape[-3] += 1
  psi = numpy.zeros(shape[:-1])
  if len(shape)==3:
    for k in range(shape[-3]-1,0,-1):
      if vmsk==None: psi[k-1,:] = psi[k,:] - vh[k-1].sum(axis=-1)
      else: psi[k-1,:] = psi[k,:] - (vmsk*vh[k-1]).sum(axis=-1)
  else:
    for n in range(shape[0]):
      for k in range(shape[-3]-1,0,-1):
        if vmsk==None: psi[n,k-1,:] = psi[n,k,:] - vh[n,k-1].sum(axis=-1)
        else: psi[n,k-1,:] = psi[n,k,:] - (vmsk*vh[n,k-1]).sum(axis=-1)
  return psi

def plotPsi(y, z, psi, ci, title):
  cmap = plt.get_cmap('dunnePM')
  plt.contourf(y, z, psi, levels=ci, cmap=cmap, extend='both')
  cbar = plt.colorbar()
  plt.contour(y, z, psi, levels=ci, colors='k', hold='on')
  plt.gca().set_yscale('splitscale',zval=[0,-2000,-6500])
  plt.title(title)
  cbar.set_label('[Sv]'); plt.ylabel('Elevation [m]')

def findExtrema(y, z, psi, min_lat=-90., max_lat=90., min_depth=0., mult=1.):
  psiMax = mult*numpy.amax( mult * numpy.ma.array(psi)[(y>=min_lat) & (y<=max_lat) & (z<-min_depth)] )
  idx = numpy.argmin(numpy.abs(psi-psiMax))
  (j,i) = numpy.unravel_index(idx, psi.shape)
  plt.plot(y[j,i],z[j,i],'kx',hold=True)
  plt.text(y[j,i],z[j,i],'%.1f'%(psi[j,i]))


m6plot.setFigureSize(npanels=1)
cmap = plt.get_cmap('dunnePM')

# Global MOC
z = Zmod.min(axis=-1); psiPlot = MOCpsi(VHmod)/1e6
yy = y[1:,:].max(axis=-1)+0*z
ci=m6plot.pmCI(0.,40.,5.)
plotPsi(yy, z, psiPlot, ci, 'Global MOC')
plt.xlabel(r'Latitude [$\degree$N]')
plt.suptitle(rootGroup.title)
findExtrema(yy, z, psiPlot, max_lat=-30.)
findExtrema(yy, z, psiPlot, min_lat=25.)
findExtrema(yy, z, psiPlot, min_depth=2000., mult=-1.)
plt.savefig(cmdLineArgs.outdir+'/MOC_global.png')

# Atlantic MOC
plt.clf()
m = 0*basin_code; m[(basin_code==2) | (basin_code==4) | (basin_code==6) | (basin_code==7) | (basin_code==8)]=1
ci=m6plot.pmCI(0.,22.,2.)
z = (m*Zmod).min(axis=-1); psiPlot = MOCpsi(VHmod, vmsk=m*numpy.roll(m,1,axis=1))/1e6
yy = y[1:,:].max(axis=-1)+0*z
plotPsi(yy, z, psiPlot, ci, 'Atlantic MOC')
plt.xlabel(r'Latitude [$\degree$N]')
plt.suptitle(rootGroup.title)
findExtrema(yy, z, psiPlot, min_lat=26.5, max_lat=27.)
findExtrema(yy, z, psiPlot, max_lat=-33.)
findExtrema(yy, z, psiPlot)
plt.savefig(cmdLineArgs.outdir+'/MOC_Atlantic.png')
