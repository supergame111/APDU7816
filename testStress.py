#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename : sendAPDU.py
# python version 2.7 base on (pyscard,swig,VC_for_python2.7)
# pip install pyscard
import os,sys,re,time,traceback
import argparse
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.CardConnectionObserver import ConsoleCardConnectionObserver

OUTPUT_LOG_FILE = "log.txt"
LOG_ENABLE = False;
RESULT_ENABLE = False;

INPUT_SCRIPT_FILE = "script.txt"
OUTPUT_RESULT_FILE = "result.txt"
TEST_COUNT = 1;			# 循环次数 -1 死循环

CMD_WRITE_FLASH_COUNT = 0;	# 实际指令条数 
INIT_POS = 0  # 初始计数
cTestCount =0;
PIN = ''; #待替换的pin码
PIN_LEN = 0;  #PIN码长度

#func
def log_print(msg):
	print(msg);
	if LOG_ENABLE:
		output = open(OUTPUT_LOG_FILE,'a')
		try:
			output.writelines(msg+"\n");
			output.flush()
		finally:
			output.close()
	
#send APDU
def send_APDU(reader,cmdList):
	if TEST_COUNT==-1 or TEST_COUNT>0 :
		gsimTest(reader,cmdList);
	else:
		oneTest(reader,cmdList);
	
	
#load file and send APDU
def readFile(fileName):
	#CardConnected,try load run script
	file = open(fileName,'r')
	lineNum = 0;
	cmd_list=[];
	params={};
	global CMD_WRITE_FLASH_COUNT;
	try:
		for lineCmd in file:
			lineNum += 1
			lineCmd = lineCmd.strip().upper()
			
			# line empty or note
			if(len(lineCmd)<1
				or lineCmd.startswith(';')): 
				continue
			
			# del note: note startWith ;
			#index=0
			index = lineCmd.find(';')
			if index>0:
				log_print("';'index=",index)
				lineCmd = lineCmd[0:index]
				log_print("after:"+lineCmd)
			del index;
			
			#replace params
			for key in params:
				lineCmd = lineCmd.replace(key,params[key])
			
			if(lineCmd.startswith('ASSERT')):
				if(len(cmd_list)>0):
					cmd_list[-1] = cmd_list[-1] + ',' + lineCmd[6:].strip()
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

			del index;
			# add to list
			if(len(lineCmd)>1):
				cmd = re.sub("0x|0X|[.| :;'\"?!@#$%^&*()+=_-]+|[G-Zg-z]+",'',lineCmd)
				if(lineCmd.startswith('8077')): # 实际写入flash的指令
					CMD_WRITE_FLASH_COUNT += 1;
				elif(PIN_LEN>1 and PIN_LEN<9 and lineCmd.startswith('800B010006')): #pin码
					ordPin='';
					for c in PIN:
						ordPin = ordPin+'3'+c;
					lineCmdTar = '800B01000'+str(PIN_LEN)+ordPin;
					print('replace PIN: src=0x'+lineCmd+",dst=0x"+lineCmdTar);
					lineCmd = lineCmdTar;
				
				cmd_list.append(str(lineNum)+ ','+ cmd)
				

	finally:
		file.close()
	return cmd_list;
	
# normal test
def oneTest(reader,cmdList):
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
		log_print(" >>line "+inStr)
		log_print("	<<< "+outStr)

		if(len(target)>1 and not success):
			passFlag = 0;
			log_print('--Assert Fail:')
			log_print('    Line : '+line)
			log_print('    cmd : '+cmd)
			log_print('    target : '+target)
			log_print('    sw     : '+outStr)
			break;
	if(passFlag):
		log_print("--SUCCESS--")
	return;	
	
# GSIM_TEST_BEGIN	
def gsimTest(reader,cmdList):
	beginTime = time.time();
	cTestCount = TEST_COUNT;
	log_print('----runTestCount:'+str(TEST_COUNT)+'-START-----------------')
	test_map={};
	cmd_count = 0; #指令条数
	
	log_print('----InitCmdStart-----')
	for inStr in cmdList:
		# cmds.format = 0,80780000,9000
		cmds = inStr.split(',');
		line = cmds[0]
		cmd = cmds[1]
		if(len(cmds)>=3):
			target = cmds[2]
		else:
			target = ''
		test_map[cmd[0:6]]=0;
		log_print('[I]line='+line+',cmd='+cmd+',taget='+target)
		cmd_count += 1;
	#for key in test_map:
	#	log_print(key,test_map[key])
	log_print('----InitCmdEnd-----')
	c_count = 0; #当前的次数
	fail_cmd = 0; # 失败的指令条数 
	
	log_print('----TestCmdStart-----')
	working = 1; #结束循环标识
	while working:
		log_print('----run test: count='+str(c_count)+',allCount='+str(c_count+INIT_POS)+'----')	
		c_count += 1;
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

			if sw1 != 0x90:
				key = cmd[0:6];
				if test_map[key] == 0:
					failCount = 'count='+str(c_count)+',allCount='+str(c_count+INIT_POS)
					log_print('[somePos Fail]:cmd='+cmd+',count='+failCount)
					fail_cmd += 1;
					
					test_map[key]=failCount+',result=0x'+outStr;
					card_success = open(OUTPUT_RESULT_FILE,'a')
					try:
						card_success.writelines("cmd="+key+"***,"+test_map[key]+"\n")
						card_success.flush()
					finally:
						card_success.close()
					
					if fail_cmd >= CMD_WRITE_FLASH_COUNT:
						log_print("----TestCmdEnd--------")
						working = 0;
						break ;
				else:
					log_print('continue'+str(fail_cmd)+' '+str(cmd_count))
		if cTestCount==0:
			working = 0;
			log_print('------runTest count:'+str(TEST_COUNT)+'--FINISH-----------------')
		elif cTestCount>0:
			cTestCount -= 1;

	log_print('----calcDataBegin---------')
	for key in test_map:
		log_print('result:'+key+str(test_map[key]))
	log_print('----calcDataEnd---------')
	log_print('----Finish----- useTime('+str(time.time()-beginTime)+'s)')
# GSIM_TEST_END	

#main
parser = argparse.ArgumentParser(description=
'''manual to this script \r\n 
  count  cycle count, default=1, \r\n
		0 while(true) \r\n
  init  init count position, default=1 \r\n
  port card usb port, default=-1 \r\n
		-1 user select port
  pin Card PIN code, default='' \r\n
		pin must in [1,9] \r\n
		1<= pin.len <=9  \r\n
  input input APDU script file, default='script.txt' \r\n
  output output result file, default=result_{PORT}.txt \r\n
  log output log file, default=log_{PORT}.txt \r\n
''')
# count  循环次数 默认1次
parser.add_argument('--count',type=int,default=1)
# initpos  起始计数次数 默认1
parser.add_argument('--init',type=int,default=1)
# port 读卡器端口号 默认 0
parser.add_argument('--port',type=int,default=-1)
# pin 卡片PIN码 默认无
parser.add_argument('--pin',type=str,default='')
# input 输入脚本 默认 script.txt
parser.add_argument('--input',type=str,default='script.txt')
# result 输出结果文件，默认result.txt
parser.add_argument('--output',type=str,default='result_{}.txt')
# log 输出log文件，默认log.txt
parser.add_argument('--log',type=str,default='log_{}.txt')
args = parser.parse_args()

LOG_ENABLE = len(args.log)>1
RESULT_ENABLE = len(args.output)>1

if LOG_ENABLE:
	OUTPUT_LOG_FILE = args.log.format(args.port)
if RESULT_ENABLE:
	OUTPUT_RESULT_FILE = args.output.format(args.port)
INPUT_SCRIPT_FILE = args.input
if len(INPUT_SCRIPT_FILE)<1:
	print('NoInputScript..')

if(args.count<=0): # 循环次数 <=0 死循环
	TEST_COUNT = -1
else:
	TEST_COUNT = args.count;
	
CMD_WRITE_FLASH_COUNT = 0;	# 实际指令条数
INIT_POS = args.init  # 初始计数
cTestCount =0;
PIN = args.pin; #待替换的pin码
PIN_LEN = len(PIN);

print '-------------------init------------------'
print 'port='+str(args.port)
print 'initpos='+str(args.init)
print 'count='+str(args.count)
print 'input='+args.input
if args.count ==1:
	RESULT_ENABLE = False;
	LOG_ENABLE = False;
	print 'beause count=1,disable output'
	
if len(PIN)>1 and len(PIN)<10:
	print 'pin='+args.pin
else:
	print 'pin.replace is diable'
if RESULT_ENABLE:
	print 'resultFile='+args.output.format(args.port)
else:
	print 'resultFile.output is disable'
if LOG_ENABLE:
	print 'logFile='+args.log.format(args.port)
else:
	print 'logFile.output is disable'


#load file and send APDU
cmdList = readFile(INPUT_SCRIPT_FILE)
if(len(cmdList)<=0):
	print("can't found APDU in "+INPUT_SCRIPT_FILE);
	
selectPort = True;
port = args.port;
readList = readers();
if(port in range(len(readList)) ):
	card = readList[port]
	selectPort = False
else:
	selectPort = True;

while(selectPort):
	readList = readers();
	read_len = len(readList);
	print('please select a port:')
	for i in range(read_len):
		print('\t{0} -- {1}'.format(i,readList[i]))
	port = int(sys.stdin.read(1));
	if(port in range(read_len)):
		card = readList[port];
		print('select port:{0},card={1}'.format(port,card));
		selectPort = False
	else:
		print('select port invalid.')


reader = card.connection = card.createConnection()
reader.connect()
log_print("--CardReader:"+str(card))

send_APDU(reader,cmdList)


	
print ('Press AnyKey to Exit')
sys.stdin.read(1)
