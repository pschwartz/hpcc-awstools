#!/usr/bin/env python
#-*- coding:utf-8 -*-

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
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
		self.id = kwargs['id']
		self.key = kwargs['key']

	def run(self):
		while True:
			node = self.queue.get()
			if node != None:
				EC2 = get_driver(Provider.EC2_US_EAST)
				driver = EC2(self.id,self.key)
				try:
					logging.info("Stopping node: "+node.name)
					driver.destroy_node(node)
				except Exception as err:
					logging.error(err)
					logging.error("Pushing fail back to queue: "+node.name)
					self.queue.put(node)
				self.queue.task_done()

start = time.time()
def main():
	if (os.path.isfile("config")):
		opt.parse_config_file("config")
	opt.parse_command_line()
	
	if not opt.options.logging:
		opt.options.logging="debug"
	
	if opt.options.threads:
		tCT = opt.options.threads
	else:
		tCT = 1

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

	
	EC2 = get_driver(Provider.EC2_US_EAST)
	driver = EC2(id,key)
	nodes = driver.list_nodes()

	runnerPool = Queue.Queue()	
	
	logging.info("Creating "+str(tCT)+" threads.")
	
	for x in xrange(tCT):
		iR = instanceRunner(queue=runnerPool, id=id, key=key)
		iR.setDaemon(True)
		iR.start()

	for x in nodes:
		if x.state == 0:
			runnerPool.put(x)
	
	runnerPool.join()

if __name__ == '__main__':
	opt = OptionParser.instance("[command]")
	opt.option("help", type=bool, help="Show this help information.")
	opt.option("logging", type=str, metavar="LEVEL", help="Logging Level")
	opt.option("threads", type=int, metavar="THREADS", help="Threads to use.")
	opt.option("amazon_id", type=str, metavar="ID", help="Amazon User ID")
	opt.option("amazon_key", type=str, metavar="Key", help="Amazon User Key")
	main()
	
logging.debug("Elapsed Time: %s" % (time.time() - start))
