#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename : sendAPDU.py
# python version 2.7 base on (pyscard,swig,VC for python2.7)

import os,sys,re
from time import sleep
import traceback
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.CardConnectionObserver import ConsoleCardConnectionObserver
from smartcard.CardMonitoring import CardMonitor, CardObserver

SCRIPT_FILE = "script.txt"

class CardInsertObserver(CardObserver):
	
	
	def __init__(self):
		self.observer = ConsoleCardConnectionObserver()	
	
	def update(self,observer,actions):
		(addedcards,removedcards) = actions
		
		for card in addedcards:
			try:
				reader = card.connection = card.createConnection()
				reader.connect()
				card.connection.addObserver(self.observer)
				print("+Card Inserted: "+ toHexString(card.atr).replace(' ',''))
				#load file and send APDU
				cmdList = readFile(SCRIPT_FILE)
				if(len(cmdList)>0):
					send_APDU(reader,cmdList)
				else:
					print('NO cmd to SNED')
			except Exception,e:
				traceback.print_exc()
				print ('----ERR.CARD')
				os.system("pause")
				
		for card in removedcards:
			card.connection=None
			print ('--Card Removed: '+toHexString(card.atr).replace(' ',''))

			
# main
cardMonitor = CardMonitor()
cardObserver = CardInsertObserver()
cardMonitor.addObserver(cardObserver)	

#send APDU
def send_APDU(reader,cmdList):
	passFlag = 1
	for inStr in cmdList:

		# cmds.format = 0,80780000,9000
		cmds = inStr.split(',');
		
		line = cmds[0]
		cmd = cmds[1]
		if(len(cmds)>=3):
			target = cmds[2]
		else:
			target = ''
		
		data,sw1,sw2 = reader.transmit(list(bytearray.fromhex(cmd)))
		
		outStr = toHexString(data) + str.format('%02X %02X' % (sw1,sw2))
		outStr = outStr.replace(' ','')
		
		success = outStr.endswith(target);
		print(" >>line "+inStr)
		print("		<< "+outStr)

		if(len(target)>1 and not success):
			passFlag = 0;
			print('--Assert Fail:')
			print('    Line : '+line)
			print('    cmd : '+cmd)
			print('    target : '+target)
			print('    sw     : '+outStr)
			break;
	if(passFlag):
		print("--SUCCESS--")
	return;
	
#load file and send APDU
def readFile(fileName):
	#CardConnected,try load run script
	file = open(fileName,'r')
	lineNum = 0;
	cmd_list=[];
	params={};
	try:
		for lineCmd in file:
			lineNum += 1
			lineCmd = lineCmd.strip().upper()
			
			# line empty or note
			if(len(lineCmd)<1
				or lineCmd.startswith(';')): 
				continue
			
			# del note: note startWith ;
			index=0
			index = lineCmd.find(';')
			if index>0:
				lineCmd = lineCmd[0,index]
			
			
			#replace params
			for key in params:
				lineCmd = lineCmd.replace(key,params[key])
			
			if(lineCmd.startswith('ASSERT')):
				if(len(cmd_list)>0):
					cmd_list[-1] = cmd_list[-1] + ',' + lineCmd[6:]
				continue;

			index=0
			index = lineCmd.find('=')
			
			if(lineCmd.startswith('APDU=')):
				lineCmd = lineCmd[5:];
			elif(lineCmd.startswith('SEND')):
				lineCmd = lineCmd[4:];
			elif(lineCmd.startswith('EDIT')):  # add params
				lineCmd = lineCmd[4:];
				if index>0:
					key = lineCmd[0:index].strip()
					params[key] = lineCmd[index+1:]
				continue;
			elif(index>0):
				key = lineCmd[0:index].strip()
				params[key] = lineCmd[index+1:]
				continue;
			else:
				lineCmd=''

			# add to list
			if(len(lineCmd)>1):
				cmd = re.sub("0x|0X|[.| '\"?!@#$%^&*()+=_-]+|[G-Zg-z]+",'',lineCmd)
				cmd_list.append(str(lineNum)+ ','+ cmd)
				

	finally:
		file.close()
	return cmd_list;
	


print ('Press AnyKey to Exit')
sys.stdin.read(1)
cardMonitor.deleteObserver(cardObserver)		
