#!/usr/bin/env python
#used to make cut for variable condition
import re,numpy,sys
from tools import *

class makecut:
    def __init__(self,run):
	self.run=run
	self.pp=getpklpath()
	self.cut=True
    
    #split varname from string
    def __getvars(self,cuts):
	varnames=[]
	for c in cuts:
	    for cc in re.split("&",c):
		v=self.__getvar(cc)
		if not v in varnames and len(v)>0:
		    varnames.append(v)
	return varnames
    
    #split varname from string from one statement
    def __getvar(self,cut):
	return re.split("[!><=]",cut)[0].strip()
    
    #read pkl for cut, 'or' between each cut, use & in one cut for 'and'
    def addcut(self,*cuts):
	print "add cut",cuts
	#load var
	varpkls={}
	for v in self.__getvars(cuts):
	    vs=re.split("[\[\]]",v)
	    varpkls[v]=zload(self.pp.getpath(vs[0],self.run))
	    if len(vs)>1:
		#for the array variable
		varpkls[v][2]=varpkls[v][2]==int(vs[1])
		varpkls[v][0]=self.usecut(varpkls[v][0],varpkls[v][2])
		varpkls[v][1]=self.usecut(varpkls[v][1],varpkls[v][2],1)
		varpkls[v]=varpkls[v][:2]
		if not varpkls.has_key("event"):
		    varpkls["event"]=zload(self.pp.getpath("event",self.run))
	fcut=False
	for cc in cuts:
	    cut=True
	    for c in re.split("&",cc):
		v=self.__getvar(c)
		if len(varpkls[v])<5:
		    #for array variable,sort event first
		    tmpcut=eval(c.replace(v,"varpkls['%s'][0]"%v))
		    zerocut=numpy.zeros(len(varpkls["event"]),numpy.bool_)
		    zerocut[numpy.searchsorted(varpkls["event"],varpkls[v][1])]=tmpcut
		    cut=cut*zerocut
		else:
		    #for normal variable
		    cut=cut*eval(c.replace(v,"varpkls['%s']"%v))
	    fcut=cut+fcut
	self.cut=fcut*self.cut
    
    #use cut for var,here var is variable
    def usecut(self,var,cut=None,cuttype=0):
	if cut==None:cut=self.cut
	if cuttype==0:
	    var=var+1e10*cut-1e10
	    return var[var>-1e9]
	else:
	    var=var*cut
	    return var[var>0]
	
    #var is var name here
    def usecutbypkl(self,var):
	return self.usecut(self.pp.getpath(var))