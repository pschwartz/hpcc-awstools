#!/usr/bin/env python
#-*- coding:utf-8 -*-

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.base import Node,NodeImage, NodeSize, NodeLocation
import libcloud.security
import threading
import Queue
import time
import os
import logging
from CLIParser.OptionParser import OptionParser


libcloud.security.VERIFY_SSL_CERT = True

class instanceRunner(threading.Thread):
	def __init__(self, **kwargs):
		threading.Thread.__init__(self)
		self.queue = kwargs['queue']
		self.location = kwargs['location']
		self.id = kwargs['id']
		self.key = kwargs['key']
		self.image = kwargs['image']
		self.size = kwargs['size']

	def run(self):
		while True:
			name = self.queue.get()
			if name != None:
				EC2 = get_driver(Provider.EC2_US_EAST)
				driver = EC2(self.id,self.key)
				try:
					logging.info("Creating node: "+name)
					node = driver.create_node(name=name, image=self.image, 
							size=self.size, location=self.location, 
							ex_keyname="HPCC_Key")
				except Exception as err:
					logging.error(err)
					logging.error("Pushing fail back to queue: "+name)
					self.queue.put(name)
				self.queue.task_done()

start = time.time()
def main():
	if (os.path.isfile("config")):
		opt.parse_config_file("config")
	opt.parse_command_line()
	
	if not opt.options.logging:
		opt.options.logging="debug"
		
	if opt.options.instances:
		iTC = opt.options.instances
	else:
		iTC = 25 
		
	if opt.options.per_thread:
		iPT = opt.options.per_thread
	else:
		iPT = 10
		
	if opt.options.threads:
		tCT = opt.options.threads
	else:
		tCT = iTC / iPT
	
	if tCT == 0:
		tCT = 1
		
	if opt.options.size:
		size = opt.options.size
	else:
		size = "t1.micro"
		
	if opt.options.ami:
		ami = opt.options.ami
	else:
		ami = "ami-c8817ea1"

    if opt.options.amazon_id:
        id = opt.options.amazon_id
    else:
        print("You must set your id.")
        sys.exit(1)

    if opt.options.amazon_key:
        key = opt.options.amazon_key
    else:
        print("You must set your key.")
        sys.exit(1)
	
	
	if opt.options.location:
		alocation = opt.options.location
	else:
		alocation = 'us-east-1b'
		
	if opt.options.tag:
		tag = opt.options.tag
	else:
		tag = "hpcc_node"
	
	image = NodeImage(id=ami, name="", driver="")
	isize = NodeSize(id=size, name="", ram=None, 
				disk=None, bandwidth=None, price=None, driver="")

	EC2 = get_driver(Provider.EC2_US_EAST)
	driver = EC2(id,key)

	locations = driver.list_locations()
	for location in locations:
		if location.availability_zone.name == alocation:
			break 
			
	runnerPool = Queue.Queue(iTC)	

	logging.info("Creating "+str(tCT)+" threads.")
	
	for x in xrange(tCT):
		iC = instanceRunner(queue=runnerPool, location=location, 
				image=image, size=isize, id=id, key=key)
		iC.setDaemon(True)
		iC.start()

	for x in range(1,iTC+1):
		name=tag+str(x)
		runnerPool.put(name)
	
	runnerPool.join()


if __name__ == '__main__':
	opt = OptionParser.instance("[command]")
	opt.option("help", type=bool, help="Show this help information.")
	opt.option("instances", type=int, metavar="INSTANCES", help="Instances to create.")
	opt.option("threads", type=int, metavar="THREADS", help="Threads to use.")
	opt.option("per_thread", type=int, metavar="PER_THREAD", help="Instances to create per threads.")
	opt.option("ami", type=str, metavar="AMI", help="AMI ID")
	opt.option("size", type=str, metavar="SIZE", help="Instance Size")
	opt.option("location", type=str, metavar="LOCATION", help="location to use.")
	opt.option("logging", type=str, metavar="LEVEL", help="Logging Level")
	opt.option("tag", type=str, metavar="TAG", help="Instance TAG prefix")
	opt.option("amazon_id", type=str, metavar="ID", help="Amazon User ID")
	opt.option("amazon_key", type=str, metavar="Key", help="Amazon User Key")
	main()
	
logging.debug("Elapsed Time: %s" % (time.time() - start))
