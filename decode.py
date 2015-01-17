#!/usr/bin/env python
import os,re,glob,numpy,ROOT,sys,gc
from tools import *

class decode:
    def __init__(self,run):
	self.remainroot=True
	self.run=run
	self.var={}
	self.cut=""
	self.prefix="g2p"
	self.scaleron=False
	self.physicson=False
	self.detectoron=False
	self.helicityon=False
	self.happexon=False
	self.beamon=False
	self.clockon=False
	self.decoderon=False
	self.rootpath=os.path.abspath(os.getenv("REPLAY_OUT_PATH"))
	self.rawpath=os.path.abspath(os.getenv("RAWPATH"))
	self.runpath=os.path.join(self.rootpath,"%s_%i.root"%(self.prefix,self.run))
	self.maxpergrp=1.0e9 #maximum memory size for each decode
	self.fvariables="variables.txt"
	self.freplaydir="replay"
	self.freplayname="replay_%i"%self.run
	self.fodefname="HRS.odef"
	 
    #get variable list from variables.txt
    def getvar(self):
	if self.var:return
	self.freplayc="%s/%s.exe"%(self.freplaydir,self.freplayname)
	self.fodef="%s/%s"%(self.freplaydir,self.fodefname)
	self.arm=(0,"L","left")  if self.run<20000 else (1,"R","right")
	self.var={}
	for l in open(self.fvariables) :
	    l=re.split("[\s#]",l.strip())
	    if len(l)<1 or len(l[0])<1:continue
	    v=""
	    for vv in l[0].split("+"):
		if "/" in vv:
		    v+=vv.split("/")[self.arm[0]]
		else:
		    v+=vv
	    if len(l)<2:
		self.var[v]={"type":0}
	    elif l[1]=="N":
		self.var[v]={"type":1}
	    elif l[1]=="pkl":
		self.var[v]={"type":-10}
	    elif l[1]=="scaler":
		self.scaleron=True
		chan=l[2].split("/")[self.arm[0]]
		if "?" in chan:
		    chan=re.split("[?:]",chan)
		    if eval("self.%s"%chan[0]):
			chan=chan[1]
		    else:
			chan=chan[2]
		self.var[v]={"type":-1,"chan":chan.replace("~"," ")}
	    elif l[1]=="block":
		self.var[v]={"type":10}
	    else:
		self.var[v]={"type":0}
	    if l[-1] in ["bool_","int8","int16","int32","int64","uint8","uint16","uint32","uint64","float16","float32","float64"]:
		self.var[v]["vartype"]=l[-1]
	    else:self.var[v]["vartype"]="float32"
	    if "gold" in v:
		self.physicson=True
	    if any([x in v for x in ["tr","L.prl","R.sh","vdc","cer"]]):
		self.detectoron=True
	    if any([x in v for x in ["BPM","Raster"]]):
		self.beamon=True
	    if any([x in v for x in ["DL.","DR."]]):
		self.decoderon=True
	    if "happex" in v:
		self.happexon=True
	    if "hel" in v:
		self.helicityon=True
	    if "clk" in v:
		self.clockon=True
	
    #create replay.C
    def buildreplayc(self):
	self.getvar()
	with open(self.freplayc,"wb",-1) as f:
	    f.write("const char** PATHS;\n")
	    f.write("const char* RAW_DATA_FORMAT;\n")
	    f.write("const char* STD_REPLAY_OUTPUT_DIR;\n")
	    f.write("const char* CUSTOM_REPLAY_OUTPUT_DIR;\n")
	    f.write("using namespace std;\n")
	    f.write("void %s(Int_t run=%i){\n"%(self.freplayname,self.run))
	    f.write("  char* RNAME=\"%s/"+self.prefix+"_%d.root\";\n")
	    f.write("  char* ODEF=\"%s\";\n"%self.fodefname)
	    f.write("  char* CUTS=\"HRS.cuts\";\n")
	    f.write("  const char *pPATHS[]={\".\",\"%s\",\"raw\"};\n"%self.rawpath)
	    f.write("  const char *pRAW_DATA_FORMAT=\"%s/g2p_%d.dat.%d\";\n")
	    f.write("  const char *pSTD_REPLAY_OUTPUT_DIR=\"%s\";\n"%self.rootpath)
	    f.write("  PATHS=pPATHS;\n")
	    f.write("  RAW_DATA_FORMAT=pRAW_DATA_FORMAT;\n")
	    f.write("  STD_REPLAY_OUTPUT_DIR=pSTD_REPLAY_OUTPUT_DIR;\n")
	    f.write("  CUSTOM_REPLAY_OUTPUT_DIR=pSTD_REPLAY_OUTPUT_DIR;\n")
	    if self.detectoron:
		f.write("  THaApparatus* HRS = new THaHRS(\"%s\",\"%s HRS\");\n"%(self.arm[1],self.arm[2]))
		f.write("  HRS->AddDetector(new THaCherenkov(\"cer\",\"Gas Cherenkov counter\"));\n")
		if self.arm[0]==0:
		    f.write("  HRS->AddDetector(new THaShower(\"prl1\",\"Pre-shower pion rej.\"));\n")
		    f.write("  HRS->AddDetector(new THaShower(\"prl2\",\"shower pion rej.\"));\n")
		else:
		    f.write("  HRS->AddDetector(new THaVDC(\"vdc\",\"Vertical Drift Chamber\"));\n")
		    f.write("  HRS->AddDetector(new THaShower(\"ps\",\"Pre-shower pion rej.\"));\n")
		    f.write("  HRS->AddDetector(new THaShower(\"sh\",\"Shower pion rej.\"));\n")
		f.write("  gHaApps->Add(HRS);\n")
	    if self.beamon or self.helicityon or self.happexon or self.clockon:
		f.write("  THaIdealBeam *ib=new THaIdealBeam(\"ib\",\"Ideal beam\");\n")
		f.write("  gHaApps->Add(ib);\n")
		iborurb="ib"
		if self.beamon:
		    f.write("  THaG2PUnRasteredBeam *urb=new THaG2PUnRasteredBeam(\"%surb\",\"Unrastered beam\");\n"%(self.arm[1]))
		    f.write("  THaG2PRasteredBeam *rb=new THaG2PRasteredBeam(\"%srb\",\"rastered beam\");\n"%(self.arm[1]))
		    f.write("  gHaApps->Add(urb);\n")
		    f.write("  gHaApps->Add(rb);\n")
		    iborurb="urb"
		if self.clockon:
		    f.write("  THaG2PClockDecode *clock=new THaG2PClockDecode(\"%sclk\",\"clock info\");\n"%self.arm[1])
		    f.write("  %s->AddDetector(clock);\n"%iborurb)
		if self.helicityon:
		    f.write("  THaG2PHelicityDecode *HRSHel = new THaG2PHelicityDecode(\"hel.%s\",\"Helicity\");\n"%(self.arm[1]))
		    f.write("  %s->AddDetector(HRSHel);\n"%iborurb)
		if self.happexon:
		    f.write("  THaG2PHappex *happex=new THaG2PHappex(\"happex.%s\",\"happex\");\n"%self.arm[1])
		    f.write("  %s->AddDetector(happex);\n"%iborurb)
	    if self.scaleron:
		f.write("  THaScalerGroup* Scalers = new THaScalerGroup(\"ev%s\");\n"%self.arm[2])
		f.write("  gHaScalers->Add(Scalers);\n")
	    if self.decoderon:
		f.write("  THaApparatus* dec=new THaDecData(\"D%s\",\"Misc. Decoder Data\");\n"%self.arm[1])
		f.write("  gHaApps->Add(dec);\n")
	    if self.physicson:
		f.write("  gHaPhysics->Add( new THaGoldenTrack(\"%s.gold\",\"HRS-%s Golden Track\",\"%s\"));\n"%(self.arm[1],self.arm[1],self.arm[1]))
	    f.write("  ReplayCore(run,-1,0,RNAME,ODEF,CUTS,%i,%i,0,1);\n"%(self.scaleron,self.helicityon))
	    f.write("}\n")
	    
    #create odef file
    def buildodef(self):
	self.getvar()
	content=""
	contentscaler=""
	for v in sorted(self.var.keys()):
	    if self.var[v]["type"]==-1:
		contentscaler+="  %s %s\n"%(v.replace("ev%s_"%self.arm[2],""),self.var[v]["chan"])
	    elif self.var[v]["type"]==10:
		content+="block %s\n"%v
	    elif self.var[v]["type"]<-9:
		continue
	    else:
		content+="variable %s\n"%v
	if self.scaleron:
	    contentscaler="begin scalers ev%s\n"%self.arm[2]+contentscaler+"end scalers\n"
	content=content+contentscaler
	with open(self.fodef,"wb",-1) as f:
	    f.write(content)
	    
    def replay(self,run=False):
	if not run:run=self.run
	self.buildreplayc()
	self.buildodef()
	os.system("cd %s;analyzer -b -q -l %s.exe\\(%i\\);cd -"%(self.freplaydir,self.freplayname,run))
	    
    def decode2pkl(self):
	ROOT.gROOT.SetBatch(True)
	self.getvar()
	eventleaf="fEvtHdr.fEvtNum" #event number
	frootfiles=glob.glob(os.path.join(self.rootpath,"%s_%i_*.root"%(self.prefix,self.run)))
	frootfiles.append(self.runpath)
	frootfiles.sort()
	#get total events
	print "getting total events in rootfiles"
	rootfiles,trees,events={},{},{}
	#for arrays
	for v in self.var.keys():
	    if self.var[v]["type"]==1:
		self.var[v]["events"]=0
	ff=-1
	for runpath in frootfiles:
	    print "events in file %s:"%runpath
	    rootfiles[runpath]=ROOT.TFile(runpath,"READ")
	    if rootfiles[runpath].IsZombie():
		print "Error! file %s abnormal! please redecode it!"%runpath
		if runpath==frootfiles[0]:return False
		else:
		    rootfiles[runpath].Close()
		    rootfiles[runpath]=False
		    continue
	    try:
		trees[runpath]=rootfiles[runpath].Get("T")
		events[runpath]=trees[runpath].GetEntries()
		print "total:%i"%(events[runpath])
	    except:
		print "Error! file %s abnormal! please redecode it!"%runpath
		continue
	    for v in self.var.keys():
		if self.var[v]["type"]==1:
		    try:
			ff+=1
			trees[runpath].Draw(v+">>h%i"%ff)
			h1=ROOT.gPad.GetPrimitive("h%i"%ff)
			vevents=int(h1.GetEntries())
			self.var[v]["events"]+=vevents
			del h1
		    except:
			raise Exception("Error!! no leaf %s in your rootfile!!"%v)
		    print "%s:%i"%(v,vevents)
	totevents=sum(events.values())
	#group mem size for vars
	print "estimating total memory usage"
	for v in self.var.keys():
	    if self.var[v]["type"]==1:
		self.var[v]["size"]=gettypesize(self.var[v]["vartype"],self.var[v]["events"])+gettypesize("uint32",self.var[v]["events"])
	    else:
		self.var[v]["size"]=gettypesize(self.var[v]["vartype"],totevents)
	groupvar=[[]]
	totsize=0
	for v in self.var.keys():
	    groupvar[-1].append(v)
	    totsize+=self.var[v]["size"]
	    print "memory size for %s:%1.2fMB"%(v,self.var[v]["size"]/1000000.)
	    if totsize>self.maxpergrp:
		groupvar.append([])
		totsize=0
	totgroups=len(groupvar)
	print "split %i groups to decode"%totgroups
	#init raw array 
	event=numpy.zeros(totevents,dtype=numpy.uint32)
	#decode
	pkldir=os.path.join(os.getenv("ANAPKLPATH"),str(self.run))
	if not os.path.exists(pkldir):
	    os.makedirs(pkldir)
	ngroup=1
	for gv in groupvar:
	    enorm=0
	    #init raw array
	    values={}
	    for v in gv:
		if self.var[v]["type"]==1:
		    self.var[v]["e"]=0
		    #value,event,ring
		    values[v]=[numpy.zeros(self.var[v]["events"],self.var[v]["vartype"]),numpy.zeros(self.var[v]["events"],dtype=numpy.uint32),numpy.zeros(self.var[v]["events"],dtype=numpy.uint8)]
		else:
		    values[v]=numpy.zeros(totevents,self.var[v]["vartype"])
	    #decode
	    for runpath in frootfiles:
		print "decoding raw data from rootfile %s %i/%i..."%(runpath,ngroup,totgroups)
		try:leventleaf=trees[runpath].GetLeaf(eventleaf)
		except Exception as err:
		    print err
		    raise Exception("Error!! no leaf %s in your rootfile!!"%eventleaf)
		leaves,branchs,ndataleaves={},{},{}
		#get leaves
		for v in gv:
		    try:
			if self.var[v]["type"]==1:
			    branchs[v]=trees[runpath].GetBranch(v)
			    leaves[v]=branchs[v].GetLeaf("data")
			    ndataleaves[v]=trees[runpath].GetLeaf("Ndata."+v)
			    ndataleaves[v].GetNdata()#check if leaf available
			else:
			    leaves[v]=trees[runpath].GetLeaf(v)
			leaves[v].GetNdata() #check if leaf available
		    except Exception as err:
			print err
			raise Exception("Error!! no leaf %s in your rootfile!!"%v)
		#decode from rootfile
		for e in xrange(events[runpath]):
		    if e%1000==0:
			print "%i/%i,decoding %i events, %i left"%(ngroup,totgroups,e,events[runpath]-e)
		    trees[runpath].GetEntry(e)
		    ee=leventleaf.GetValue()
		    event[enorm]=ee
		    for v in gv:
			if self.var[v]["type"]==1:
			    numv=int(ndataleaves[v].GetValue())
			    if numv<1:continue
			    for i in range(numv):
				values[v][0][self.var[v]["e"]]=leaves[v].GetValue(i)
				values[v][1][self.var[v]["e"]]=ee
				values[v][2][self.var[v]["e"]]=i
				self.var[v]["e"]+=1
			else:
			    values[v][enorm]=leaves[v].GetValue()
		    enorm+=1
	    #save to disk
	    if ngroup==1 and not os.path.exists(os.path.join(pkldir,"event.pkl")):
		zdump(event,os.path.join(pkldir,"event.pkl"))
	    for v in gv:
		print "dumping %s"%v
		zdump(values[v],os.path.join(pkldir,"%s.pkl"%v))
		del values[v]
	    gc.collect()
	    ngroup+=1
	for runpath in frootfiles:
	    rootfiles[runpath].Close()
	if not self.remainroot:
	    for runpath in frootfiles:
		os.remove(runpath)
