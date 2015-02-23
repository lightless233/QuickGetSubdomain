#!/usr/bin/python
#coding:utf-8

import threading
import socket, urllib
import sys, time
from Queue import Queue

# Global variable
isReadFinished = 0
isFindFinished = 0
isWriteFinished = 0

workQueue = Queue()
logQueue  = Queue()

domainLock = threading.Lock()

thread_list = []

# read subdomain from dict
class ReadSubFromFile(threading.Thread):

	def __init__(self, dictFilename):
		threading.Thread.__init__(self)
		self.dictFilename = dictFilename

	def run(self):
		global isReadFinished
		global workQueue

		f = open('dict.txt', 'r')
		for eachline in f:
			workQueue.put(eachline)

		f.close()
		isReadFinished = 1


class FindSubdomain(threading.Thread):

	def __init__(self, url):
		threading.Thread.__init__(self)
		self.url = url

	def run(self):
		global workQueue
		global isFindFinished
		global domainLock
		global logQueue

		#print "[+] Thread start"

		while True:
			if domainLock.acquire():
				if workQueue.empty() and isReadFinished:
					domainLock.release()
					break

				domain_prefix = workQueue.get()
				domainLock.release()

			domain = domain_prefix.strip() + "." + self.url
			#print "[-] try " + domain

			try:
				target_addr = socket.getaddrinfo(domain, 'http')[0][4][0]
				if target_addr == "1.1.1.1":
					pass
				else:
					s = urllib.urlopen('http://'+domain)
					statusCode = s.getcode()
					s.close()
					if statusCode == 404:
						continue
					else:
						print "[+] Found: " + domain + " code:" + str(statusCode)
						logQueue.put(domain + " code:" + str(statusCode))
			except Exception, e:
				pass

			if isReadFinished and workQueue.empty():
				break

class WriteLog(threading.Thread):

	def __init__(self, logfilename):
		threading.Thread.__init__(self)
		self.logfilename = logfilename

	def run(self):
		global logQueue
		global isWriteFinished

		f = open(self.logfilename+"_result.txt", "w+")

		while True:

			if isReadFinished and isFindFinished:
				break

			if logQueue.empty():
				continue

			try:
				item = logQueue.get(block=False)
			except Exception, e:
				item = "-1"

			if item != "-1":
				#print "item", item
				f.write(str(item)+"\n")
			
		f.close()
		isWriteFinished = 1


def work(inputurl):
	global thread_list
	global isWriteFinished
	global isReadFinished
	global isFindFinished

	socket.setdefaulttimeout(10)

	readfileThread = ReadSubFromFile("dict.txt")
	readfileThread.start()

	for i in range(20):
		thread_list.append(FindSubdomain(inputurl))
		thread_list[i].start()
		# thread_list[i].join()

	writelogThread = WriteLog(inputurl)
	writelogThread.start()

	while True:
		cnt = 0
		if isFindFinished and isReadFinished and isWriteFinished:
			sys.exit()
		for t in thread_list:
			if t.isAlive():
				cnt += 1
		
		if cnt == 0:
			isFindFinished = 1

		# print 'isFindFinished', isFindFinished
		# print 'isReadFinished', isReadFinished
		# print 'isWriteFinished', isWriteFinished
		# print 'cnt', cnt
		# print '======================='
		# time.sleep(2)

if __name__ == '__main__':
	print \
'''
 ____        _     ____                        _       
/ ___| _   _| |__ |  _ \  ___  _ __ ___   __ _(_)_ __  
\___ \| | | | '_ \| | | |/ _ \| '_ ` _ \ / _` | | '_ \ 
 ___) | |_| | |_) | |_| | (_) | | | | | | (_| | | | | |
|____/ \__,_|_.__/|____/ \___/|_| |_| |_|\__,_|_|_| |_|
By Lightless
'''

	if len(sys.argv) == 1:
		print "Usage: " + sys.argv[0] + " domain.com"
		sys.exit()
	
	inputurl = sys.argv[1]

	work(inputurl)