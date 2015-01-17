#!/usr/bin/env python
import os,re,glob,sys
from decode import decode
from beampackage import decode as beamdecode

class decode_beam(decode):
    def __init__(self,run):
	decode.__init__(self,run)
	self.fvariables="variables_beam.txt"
	self.freplayname="replay_beam"
	self.fodefname="HRS_beam.odef"
	self.prefix="bpm"
	
    def decode2pkl(self):
	runpath=os.path.join(self.rootpath,"%s_%i.root"%(self.prefix,self.run))
	frootfiles=glob.glob(os.path.join(self.rootpath,"%s_%i_*.root"%(self.prefix,self.run)))
	frootfiles.append(runpath)
	frootfiles.sort()
	d=beamdecode(runpath,buildtree=0,forceredecode=1)
	d.manualset=True
        d.pklon["rbpm"]=True
        d.pklon["curr"]=True
        d.pklon["hapevent"]=True
        d.pklon["raster"]=True
        d.pklon["clock"]=True
        d.pklon["event"]=True
        if d.fastbus:
	    d.pklon["fbbpm"]=True
        d.getrootfilefamily()
        d.decodefromrootfile()
        if not self.remainroot:
	    for runpath in frootfiles:
		os.remove(runpath)