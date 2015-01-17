#!/usr/bin/env python
#align data from epics raw to epics
import time,numpy,sys
from tools import *
from beampackage import runinfo,timer2s,times2r,checkrunavail
from beampackage import getpklpath as beamgetpklpath
from beampackage import decode as beamdecode

#align epics var to events
def epicsalign(run,epicsvar,etype="float32",align2beam=False):
    pp=getpklpath()
    arm="L" if run<20000 else "R"
    info=runinfo()
    fstclkfreq=info.getsqlinfo(run,"fastclkfreq")
    if align2beam:
	#align to beam event
	beampp=beamgetpklpath()
	fstclkpklpath=beampp.getpath("raw","clock",run)
	if not os.path.exists(fstclkpklpath):
	    raise Exception("no fast clock pkl exists, please redecode again")
	fstclk=zload(fstclkpklpath)/float(fstclkfreq)
	epicspklfile=beampp.getpath("epics",epicsvar,run)
    else:
	#align to event
	pp=getpklpath()
	fstclkpklpath=pp.getpath("%sclk.fastclk"%arm,run)
	if not os.path.exists(fstclkpklpath):
	    beampp=beamgetpklpath()
	    fstclkpklpath=beampp.getpath("raw","clock",run)
	    beamevent=beampp.getpath("raw","event",run)
	    event=pp.getpath("event",run)
	    fstclk=sortevents(zload(fstclkpklpath),zload(beamevent),zload(event))
	else:
	    fstclk=zload(fstclkpklpath)
	fstclk=fstclk/float(fstclkfreq)
	epicspklfile=pp.getpath(epicsvar,run)
    
    trunstart=times2r(info.getsqlinfo(run,"RunStartTime"))
    eventtime=fstclk+trunstart
    epicsrawpath=os.getenv("EPICSRAW")
    epics=zload(os.path.join(epicsrawpath,"%s.pkl"%epicsvar))
    lenepics=len(epics["time"])-1
    lenfstclk=len(fstclk)
    epicspkl=numpy.zeros(len(fstclk),etype)
    
    idnow=numpy.argmin(abs(epics["time"]-eventtime[0]))-1
    for i in range(lenfstclk):
	if i%100000==0:print "aligning %i/%i"%(i,lenfstclk),idnow
	while True:
	    if idnow>lenepics or epics["time"][idnow+1]>eventtime[i]:
		break
	    else:idnow+=1
	epicspkl[i]=epics["v0"][idnow]
    zdump(epicspkl,epicspklfile)
    
    