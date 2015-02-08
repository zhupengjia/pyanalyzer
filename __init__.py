#!/usr/bin/env python
modules=["tools","decode","decode_beam","epicsalign","makecut","roottools"]
for m in modules:
    try:
	exec("from %s import *"%m)
    except Exception as err:
	print "Error!!",err
