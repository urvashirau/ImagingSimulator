#!/usr/bin/env python

"""calcsim.py: Methods to implement an interferometric imaging simulator."""

__author__      = "Urvashi R.V."
__email__ = "rurvashi@nrao.edu"

import pylab as pl
import numpy as np
import copy
import time

class CalcSim:

    def __init__(self):
        self.npix= 256

        self.antennalist={'EastLoc':[], 'NorthLoc':[], 'ElevLoc':[], 'AntName':[]}
        self.randseed=1
        self.calcAntList() # default

        self.sky=None
        self.ftsky=None
        self.setsky() # default

        self.uvcov=None
        self.psf=None
        self.sumwt=None
        self.makeUVcov() # default

#        self.padded_arr=None
#        self.padded_arr=np.zeros( [npix*2, npix*2], 'complex')

        self.obssky=None

    def calcAntList(self, configtype='YConfig',changeseed=True, zoom=1.0, nant=20):
        self.antennalist={'EastLoc':[], 'NorthLoc':[], 'ElevLoc':[], 'AntName':[]}
        N = nant
#        if configtype=='YConfig':
#            eastlocs, northlocs, elevlocs, antnames = self.readAntListFile('vla_ants.txt')
        if 1.0: #configtype in ['YConfig','CircleConfig','SpiralConfig','RandomConfig','RandomCoreConfig']:
            antnames = []
            for aa in range(0,N):
                antnames.append('Ant'+str(aa))

            if configtype=='CircleConfig':
                eastlocs = np.zeros(N)
                northlocs = np.zeros(N)
                elevlocs = np.ones(N)*0.1
                degs = np.arange(0,360.0, 360.0/N) * np.pi/180.0
                for adeg in range(0,N):
                    eastlocs[adeg] = np.cos(degs[adeg]) * 250
                    northlocs[adeg] = np.sin(degs[adeg]) * 250

            elif configtype=='YConfig':
                eastlocs = np.zeros(N)
                northlocs = np.zeros(N)
                elevlocs = np.ones(N)*0.1

                ang = 90.0
                rad=0.1
                for ant in range(0,N):
                    #print ant, ang, rad
                    eastlocs[ant] = (0.01+rad**1.5) *np.cos(ang*np.pi/180.0) * 400
                    northlocs[ant] = (0.01+rad**1.5) *np.sin(ang*np.pi/180.0) * 400
                    rad = rad+3.0/N 
                    if ant>0 and (ant+1) % (int(N/3.0)) ==0:
                        ang = ang+120.0
                        rad=0.1

            elif configtype=='SpiralConfig':
                eastlocs = np.zeros(N)
                northlocs = np.zeros(N)
                elevlocs = np.ones(N)*0.1

                ant=0
                for d1 in np.arange(0,360.0, 120.0) :
                    rad=0.2
                    for d2 in np.arange(d1, d1+120.0, 120.0/(N/3.0)) :
                        deg = d2 * np.pi/180.0
                        eastlocs[ant] =  (0.01+rad**1.5) * np.cos(deg) * 300
                        northlocs[ant] = (0.01+rad**1.5) * np.sin(deg) * 300
                        rad = rad+ 3.0/N 
                        ant=ant+1
                        if ant>=N :
                            break
                            
            elif configtype=='RandomCoreConfig':
                if changeseed==True:
                    self.randseed=int(time.time())
                np.random.seed(self.randseed)
                eastlocs = np.random.randn(N) * 200
                northlocs = np.random.randn(N) * 200
                elevlocs = np.random.randn(N) * 0.3
                eastlocs[0:int(N/5)] = eastlocs[0:int(N/5)] * 0.1
                northlocs[0:int(N/5)] = northlocs[0:int(N/5)] * 0.1

            else:
                if changeseed==True:
                    self.randseed=int(time.time())
                np.random.seed(self.randseed)
                eastlocs = np.random.randn(N) * 200
                northlocs = np.random.randn(N) * 200
                elevlocs = np.random.randn(N) * 0.3

        eastlocs = eastlocs * zoom
        northlocs = northlocs * zoom

        for aa in range(0, len(eastlocs)):
            self.antennalist['EastLoc'].append(eastlocs[aa])
            self.antennalist['NorthLoc'].append(northlocs[aa])
            self.antennalist['ElevLoc'].append(elevlocs[aa])
            self.antennalist['AntName'].append(antnames[aa])

#    def scaleAntList(self,zoom):
#        print "Zoom : ", zoom
#    
#        ## Scale to zoom
#        for aa in range(0, len(self.antennalist['EastLoc'])):
#            self.antennalist['EastLoc'][aa] = self.antennalist['EastLoc'][aa] * zoom
#            self.antennalist['NorthLoc'][aa] = self.antennalist['NorthLoc'][aa] * zoom
#

#        self.antennalist['EastLoc'] =  self.antennalist['EastLoc'] * zoom
#        self.antennalist['NorthLoc'] =  self.antennalist['NorthLoc'] * zoom
        

    def getAntList(self):
        return self.antennalist

    def calcAntUVWList(self,
                       has=[-3.5,-1.0], 
                       dec=+50.0, 
                       obslatitude=34.0):
        """
        For the given timerange, gather a list of rotated antUVWs.
        """
        locs=[]
        maxval=4000.0
        ##  cell size : 1/(4000.0/(3e+8/1e+9)) * 180.0/3.14 * 60 * 60 = 15.47 arcsec
        
        for hourangle in np.arange(has[0],has[1]+0.1,0.25):
                alocs = self.getAntUVWs(hourangle=hourangle, 
                                        declination=dec, 
                                        obslatitude=obslatitude)
                for aloc in alocs:
                    locs.append( [ aloc[0]/maxval, aloc[1]/maxval ] )
        return locs


    def getAntUVWs(self,
                   hourangle=-3.5, 
                   declination=+20.0, 
                   obslatitude=34.0):

        eastlocs = self.antennalist['EastLoc']
        northlocs = self.antennalist['NorthLoc']
        elevlocs = self.antennalist['ElevLoc']
        antnames = self.antennalist['AntName']

        ## Assign x->East and x-North. This is the local geographic csys
        Xlocs = eastlocs
        Ylocs = northlocs 

        ################################ Construct XYZ
        ## Start with  local xyz
        AL = 1000.0
        xdir1 = np.array( [AL,0,0], 'float' )
        ydir1 = np.array( [0,AL,0], 'float' )
        zdir1 = np.array( [0,0,AL], 'float' )

        ################################ Construct uvw
        ## Start with local xyz
        ## Rotate to get 'z' pointed to where 'w' should be when HA=0, DEC=0
        ## Rotate by HA and DEC in appropriate directions.
        ## Rotate by observatory latitude.
        latrot = -90+obslatitude

        udir = self.localxyz2uvw( xdir1, hourangle, declination, latrot )
        vdir = self.localxyz2uvw( ydir1, hourangle, declination, latrot )
        wdir = self.localxyz2uvw( zdir1, hourangle, declination, latrot )

        ################################
        ## Calculate UVWs for all antennas.
        axyz=np.array( [0.0,0.0,0.0], 'float')
        antuvws = np.zeros( (len(Xlocs), 3) ,'float')
        for ant in range(0,len(Xlocs)):
            axyz[0] = Xlocs[ant]
            axyz[1] = Ylocs[ant]
            axyz[2] = elevlocs[ant]
            # Project onto UVW axes.
            antuvws[ant,0] = np.dot(axyz,udir)/np.linalg.norm(udir)
            antuvws[ant,1] = np.dot(axyz,vdir)/np.linalg.norm(vdir)
            antuvws[ant,2] = np.dot(axyz,wdir)/np.linalg.norm(wdir)

        return antuvws


    def setsky(self, imtype='im1'):
        """
        Later, make this in world coords, so that changes in pixel size work ok. 
        """
        npix = self.npix
        self.sky = np.zeros((npix,npix),'float')

        ### Stay between 0.25 and 0.75

        if imtype=='im1':
            
            self.sky[int(npix*0.5),int(npix*0.6)] = 4.0
            
            self.sky[int(npix*0.5),int(npix*0.63)] = 1.0
            self.sky[int(npix*0.5),int(npix*0.64)] = 1.0
            self.sky[int(npix*0.5),int(npix*0.65)] = 1.0
            self.sky[int(npix*0.5),int(npix*0.66)] = 2.0
            self.sky[int(npix*0.5),int(npix*0.67)] = 1.0
            
            self.sky[int(npix*0.53),int(npix*0.57)] = 1.0
            self.sky[int(npix*0.54),int(npix*0.56)] = 1.0
            self.sky[int(npix*0.55),int(npix*0.55)] = 2.0
            self.sky[int(npix*0.56),int(npix*0.54)] = 1.0
            
            self.sky[int(npix*0.3),int(npix*0.3)] = 4.0
            self.sky[int(npix*0.7),int(npix*0.45)] = 5.0

        elif imtype=='im3':

            self.sky[int(npix*0.3),int(npix*0.3)] = 5.0
            self.sky[int(npix*0.5),int(npix*0.65)] = 2.0
            self.drawGaussian( int(npix*0.5),  int(npix*0.5) , 0.02, npix*0.08)
            self.drawGaussian( int(npix*0.4),  int(npix*0.65) , 0.02, npix*0.12)
            self.drawGaussian( int(npix*0.6),  int(npix*0.6) , 0.02, npix*0.06)
            

        else:  # type im2
            self.sky[int(npix*0.5), int(npix*0.5)] = 1.0
            
     
        self.ftsky = self.ft2d(self.sky)


    def drawdisk(self, xpos, ypos, rad):
        for xx in range(xpos-rad,xpos+rad):
            for yy in range(ypos-rad,ypos+rad):
                if (xx-xpos)**2 + (yy-ypos)**2 < rad**2:
#                    if action=='add':
#                        self.uvcov[xx,yy] = self.uvcov[xx,yy]+1.0
#                    if action=='blank':
                    self.uvcov[xx,yy] = 0.0
        return 

    def drawGaussian(self,  xpos, ypos, amp, sigma):
        rad = sigma*5
        shp = self.sky.shape
        #print shp[0], shp[1]
        #        for xx in range( np.max(xpos-rad,0), np.min(xpos+rad,shp[0]-1)):
        #           for yy in range( np.max(ypos-rad,0),np.min(ypos+rad,shp[1]-1)):
        for xx in range(0,shp[0]):
            for yy in range(0,shp[1]):
                self.sky[xx,yy] = self.sky[xx,yy] + amp * np.exp(-0.5* ( (xx-xpos)**2 + (yy-ypos)**2 ) / (sigma**2) )
        return 

    def ft2d(self, inpdat):
        idata = np.fft.ifftshift(inpdat)
        fdata=(np.fft.fftn(idata));
        outdat=np.fft.fftshift(fdata);
#        padded_arr=np.zeros( [self.npix*2, self.npix*2], 'float')
#        padded_arr[int(self.npix*0.5):int(self.npix*1.5), int(self.npix*0.5):int(self.npix*1.5)] = inpdat
 #       idata = np.fft.ifftshift(padded_arr)
  #      fdata=(np.fft.fft2(idata));
   #     padded_outdat=np.fft.fftshift(fdata);
    #    outdat = padded_outdat[int(self.npix*0.5):int(self.npix*1.5), int(self.npix*0.5):int(self.npix*1.5)]
        return outdat

    def makeUVcov(self,
                  has=[-1.0,+1.0],
                  dec=+50.0, 
                  obslatitude=34.0,
                  weighting='natural'):
        
        locs = self.calcAntUVWList(has=has, 
                                   dec=dec, 
                                   obslatitude=obslatitude)

        rad=1.5
        aparr = np.zeros((self.npix,self.npix),'float')
        dcarr = np.zeros((self.npix,self.npix),'float')
        for loc in locs:
            xloc = int(self.npix/2)+int(loc[0]*self.npix/2)
            yloc = int(self.npix/2)+int(loc[1]*self.npix/2)
            aparr[xloc,yloc] = aparr[xloc,yloc]+1.0


        varr = self.ft2d(aparr)
        parr = np.real(varr * np.conj(varr))
        self.uvcov = np.real(self.ft2d(parr))
        
        wmax = np.max(np.real(self.uvcov))
        self.uvcov = self.uvcov/wmax
        
        if weighting=='uniform':
            self.uvcov = self.uvcov/ (self.uvcov+0.0001)
        elif weighting=='robust':
            self.uvcov = (self.uvcov)**2/ ( (self.uvcov)**2 + 0.005 )

        self.drawdisk(int(self.npix/2),int(self.npix/2),int(rad))
        self.psf = np.real(self.ft2d(self.uvcov))
        self.sumwt = np.max(self.psf)
        #print 'Max of psf : ', np.max(self.psf)
        self.psf = self.psf / self.sumwt
        #ftsky = ft2d(self.sky)

        #print 'Max of psf : ', np.max(self.psf)

    def makeImage(self):

        obsvis = self.uvcov * self.ftsky
        self.obssky = np.real(self.ft2d(obsvis)) / self.sumwt

    def getImage(self):
        return np.rot90(np.fliplr(self.obssky))

    def getUVcov(self):
        p1=int(self.npix*0.35)
        p2=int(self.npix*0.65)
        themax = np.max(self.uvcov[p1:p2,p1:p2])
        return np.rot90(np.fliplr(np.real(np.sqrt(self.uvcov[p1:p2,p1:p2]/themax+0.001))))


    #############################################

    def readAntListFile(self, antfile=''):
        fp = open(antfile,'r')
        thelines = fp.readlines()

        eastlocs=[]
        northlocs=[]
        elevlocs=[]
        antnames=[]
        for aline in thelines:
            if aline[0] != '#':
                words = aline.split()
                antnames.append( words[1] )
                ## make the indices 6,7,8 for listobs files that do not contain pad/station info !!
                ## make the indices 7,8,9 for listobs files that contain antenna pad info !!
                eastlocs.append( eval( words[7] ) )
                northlocs.append( eval( words[8] ) )
                elevlocs.append( eval( words[9] ) )

        #print 'Antenna names : ', antnames
        #print 'East : ', eastlocs
        #print 'North :', northlocs
        #print 'Elev : ',elevlocs
        return np.array(eastlocs), np.array(northlocs), np.array(elevlocs), antnames

    ###################################################

    # xyz : local geographical coordinates, with x->East, y->North, z->Zenith.
    # XYZ : Earth/Celestial coordinate system (located at the array location) 
    #          with X->East, Z->NCP and Y to make a RH system.
    # uvw : When HA=0, DEC=90, uvw is coincident with XYZ.  
    #          v and w and NCP are always on a Great-circle, u completes the RH system
    #          When 'v' or 'w' is the NCP, then 'u' points East.  

    ## Rotate counter-clockwise about x
    def rotx(self, xyz , angle ):
        newxyz = np.array( [0.0,0.0,0.0], 'float' )
        ang = angle*np.pi/180.0
        newxyz[0] = xyz[0]
        newxyz[1] = xyz[1] * np.cos(ang) - xyz[2] * np.sin(ang)
        newxyz[2] = xyz[1] * np.sin(ang) + xyz[2] * np.cos(ang)
        return newxyz

    ## Rotate counter-clockwise about y
    def roty(self, xyz , angle ):
        newxyz = np.array( [0.0,0.0,0.0], 'float' )
        ang = angle*np.pi/180.0
        newxyz[0] = xyz[0] * np.cos(ang) + xyz[2] * np.sin(ang)
        newxyz[1] = xyz[1]
        newxyz[2] = -1* xyz[0] * np.sin(ang) + xyz[2] * np.cos(ang)
        return newxyz

    ## Rotate counter-clockwise about z
    def rotz(self, xyz , angle ):
        newxyz = np.array( [0.0,0.0,0.0], 'float' )
        ang = angle*np.pi/180.0
        newxyz[0] = xyz[0] * np.cos(ang) - xyz[1] * np.sin(ang)
        newxyz[1] = xyz[0] * np.sin(ang) + xyz[1] * np.cos(ang)
        newxyz[2] = xyz[2]
        return newxyz

    ## Three rotations. 
    ## Start with uvw aligned with local xyz
    ## Rotate about x by 90 deg, to get 'w' to point HA=0, DEC=0
    ## Rotate about x by -DEC 
    ## Rotate about z by -HA
    def xyz2uvw(self, xyz , ha, dec ):
        newuvw = self.rotz( self.rotx( self.rotx( xyz, 90 ) , -1*dec ) , -1*ha*15 )
        return newuvw

    def localxyz2uvw(self, xyz, hourangle, declination, latrot ):
        uvwdir = self.xyz2uvw( xyz, hourangle, declination )
        uvwdir = self.rotx( uvwdir, latrot )
        return uvwdir






