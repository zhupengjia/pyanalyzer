#!/usr/bin/env python
import os,zlib,numpy,re,random,sqlite3
try:import cPickle as pickle
except:import pickle

#compress pickle file by using zlib and cpickle
def zdump(value,filename):
    with open(filename,"wb",-1) as fpz:
	fpz.write(zlib.compress(pickle.dumps(value,-1),9))

#load compressed pkl file from zdump
def zload(filename):
    with open(filename,"rb") as fpz:
	value=fpz.read()
	try:return pickle.loads(zlib.decompress(value))
	except:return pickle.loads(value)
    
#get memory size for numpy array type
def gettypesize(tp,num=1):
    tpsize={"bool_":1,\
	"int8":1,\
	"int16":2,\
	"int32":4,\
	"int64":8,\
	"uint8":1,\
	"uint16":2,\
	"uint32":4,\
	"uint64":8,\
	"float16":2,\
	"float32":4,\
	"float64":8}
    if not tpsize.has_key(tp):return False
    return tpsize[tp]*num

#get pkl file path
class getpklpath:
    def __init__(self,rootfilepath=os.getenv("REPLAY_OUT_PATH")):
	self.rootfilepath=rootfilepath
	self.pkldir=os.getenv("ANAPKLPATH")
	if self.pkldir==None:
	   self. pkldir=os.path.join(self.rootfilepath,"pkl")
	self.pklbak=os.getenv("ANAPKLBAK")
	
    def getdir(self):
	return self.pkldir
    
    #writemode:if writemode=1,will ignore pklbak dir,that is only save pkl data to pkldir
    def getpath(self,varname="",run=0,writemode=0):
	rundir=os.path.join(self.pkldir,str(run))
	filename="%s.pkl"%varname
	path=os.path.join(rundir,filename)
	if writemode:
	    if not os.path.exists(self.pkldir):
		try:os.makedirs(self.pkldir)
		except:raise Exception("Error!!do you have permission to create directory for %s?"%self.pkldir)
	    if not os.path.exists(rundir):
		try:os.makedirs(rundir)
		except:raise Exception("Error!!do you have permission to create directory for %s?"%self.pkldir)
	    return path
	elif os.path.exists(path):return path
	else:
	    if self.pklbak==None:return path
	    else:
		path2=os.path.join(os.path.join(self.pklbak,str(run)),filename)
		if os.path.exists(path2):return path2
		else:return path
	    
class sqliteread:
    def __init__(self,sqlfile):
	self.sqlfile=sqlfile
	self.initsql=False
    
    def __initsql(self):
	if self.initsql:return
	if not os.path.exists(self.sqlfile):
	    raise Exception("Error!! database file %s not exists!!!"%self.initsql)
	con=sqlite3.connect(self.sqlfile)
	con.row_factory = sqlite3.Row
	self.cur=con.cursor()
	self.result={}
	self.initsql=True
	
    def getsqlinfo(self,tree,mainkey,mainid,key=False):
	self.__initsql()
	if not self.result.has_key(mainid):
	    self.cur.execute("select * from %s where %s=%i"%(tree,mainkey,mainid))
	    result=self.cur.fetchone()
	    if result==None:return None
	    self.result[mainid]=result
	if key:
	    if not key in self.result[mainid].keys():return None
	    try:return float(self.result[mainid][key])
	    except:return self.result[mainid][key]
	return dict(self.result[mainid])
	
	    
#sort events for v1, if e1 is events array for v1, e2 is destination events
def sortevents(v1,e1,e2):
    return v1[numpy.searchsorted(e1,e2)]

#used for getting el5 or el6 on farm
def getmachine():
    try:return re.split("[._]",os.uname()[2])[5]
    except:return ""

#generate random color
def generatecolor():
    a=random.uniform(0,1)
    b=random.uniform(0,1)
    t=1-a-b
    t=0 if t<0 else t
    c=random.uniform(t,1)
    return (a,b,c)

#multiply all of numbers in a list
def multiply(lst):
    lst=[x for x in lst if x!=0]
    if len(lst)==1:return lst[0]
    elif len(lst)<1:return 1
    return reduce(lambda x,y:x*y,lst)

#convert list or dict to string
def list2str(l):
    r=""
    if isinstance(l,list) or isinstance (l,tuple):
	for x in l:r+=list2str(x)
    elif isinstance(l,dict):
	for x in l.keys():r+=list2str(l[x])
    else:r=str(l)
    return r
    
# convert lists to a hash key
def list2hash(*l):
    s=""
    for ll in l:
	s+=list2str(l)
    return str(hash(s))
    
#calculate rms from numpy array
def getrms(nparray):
    mean=numpy.nanmean(nparray)
    return mean,numpy.sqrt(numpy.nanmean((nparray-mean)**2))