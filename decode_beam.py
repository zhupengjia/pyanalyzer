#!/usr/bin/env python
import os,re,glob,sys
from decode import decode
from beampackage import decode as beamdecode

class decode_beam(decode):
    def __init__(self,run):
      decode.__init__(self,run)
      self.fvariables="variables_beam.txt"
      self.freplayname="replaybeam_%i"%self.run
      self.fodefname="%sHRS_beam.odef"%self.arm[1]
      self.prefix="bpm"
      
    def decode2pkl(self,availkeys=[]):
      runpath=os.path.join(self.rootpath,"%s_%i.root"%(self.prefix,self.run))
      frootfiles=glob.glob(os.path.join(self.rootpath,"%s_%i_*.root"%(self.prefix,self.run)))
      frootfiles.append(runpath)
      frootfiles.sort()
      d=beamdecode(runpath,buildtree=0,forceredecode=1)
      d.manualset=True
      if len(availkeys)<1:
          for k in ["rbpm","curr","hapevent","hapraster","raster","clock","event"]:
              d.pklon[k]=True
          if d.fastbus:
              d.pklon["fbbpm"]=True
      else:
          for k in availkeys:
              d.pklon[k]=True
      d.getrootfilefamily()
      d.decodefromrootfile()
      if not self.remainroot:
          for runpath in frootfiles:
              os.remove(runpath)
