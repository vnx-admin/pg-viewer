import time
import os
import threading
import datetime
import sys
import pygame
import Queue
import re
import ConfigParser

def getIp():
	return open('/tmp/myip').readline()[:-1]
	
def getConfig(confItems):
	config = ConfigParser.ConfigParser()
	config.read('viewer.conf')
	confDict={}
	ip=getIp()
	for cItem in confItems:
		try:
			confDict[cItem]=config.get(ip,cItem)
		except ConfigParser.NoOptionError:
			confDict[cItem]=config.get('default',cItem)
	return confDict

def checkImages(config):
	chSText=open(config['path']+'/images.md5').read()
	result=[]
	res = re.findall(r'MD5 \(/usr/smb/timetable/images/(tablo_'+config['id']+'_[0-9]+.jpg)\) = ([a-f0-9]+)',chSText, re.DOTALL|re.MULTILINE)
	if res:
		result.append(config['id'])
	else:
		res = re.findall(r'MD5 \(/usr/smb/timetable/images/(tablo_'+config['default_id']+'_[0-9]+.jpg)\) = ([a-f0-9]+)',chSText, re.DOTALL|re.MULTILINE)
		result.append(config['default_id'])
	if not res:
		return False
	else:
		res.sort()
		result.append(res)
		return result
	
def imageThread(config):
	images={}
	cur_pic=''
	cur_mode=''
	playlist=[]
	imageSum=[]
	counter=[0,0,0]
	interval=int(float(config['change_interval'])*(1/float(config['sum_refresh'])))
	while True:
		imageSum=checkImages(config)
		if imageSum[0]==cur_mode:
			counter[1]=0
			temp_pl=[]
			for i in imageSum[1]:
				temp_pl.append(i[0])
			if playlist==temp_pl:
				for i in imageSum[1]:
					if i[1]!=images[i[0]][1]:
						try:
							images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
						except:
							time.sleep(1)
							images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
						if cur_pic==i[0]:
							img_q.put(images[cur_pic][0])
					else:
						pass
			else:
				for i in imageSum[1]:
					if images.has_key(i[0]):
						if i[1]!=images[i[0]][1]:
							try:
								images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
							except:
								time.sleep(1)
								images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
							if cur_pic==i[0]:
								img_q.put(images[cur_pic][0])
						else:
							pass
						playlist.remove(i[0])
					else:
						try:
							images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
						except:
							time.sleep(1)
							images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
				for i in playlist:
					del images[i]
				playlist=temp_pl
		else:
			counter[1]=1
			del images
			playlist=[]
			images={}
			for i in imageSum[1]:
				try:
					images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
				except:
					time.sleep(1)
					images.update({i[0]:[pygame.image.load(config['path']+'/'+i[0]),i[1]]})
					
				playlist.append(i[0])
			cur_mode=imageSum[0]
		time.sleep(float(config['sum_refresh']))
		if (counter[0]==interval) or (counter[0]==0) or (counter[1]==1):
			if (counter[2]>=len(playlist)) or (counter[1]==1):
				counter[2]=0
			cur_pic=playlist[counter[2]]
			img_q.put(images[cur_pic][0])
			counter[2]=counter[2]+1
			counter[0]=0
		counter[0]=counter[0]+1

def clockThread():
	t_set=True
	lcd_f=pygame.font.Font('lcd.ttf',24)
	img=img_q.get()
	while True:
		clock.tick(2)
		if t_set:
			t=datetime.datetime.now().strftime('%H:%M')
			tg=lcd_f.render(t, True, (255,225,255) )
		else: 
			t=datetime.datetime.now().strftime('%H %M')
			tg=lcd_f.render(t, True, (255,225,255) )
		t_set = not t_set
		if img_q.empty()==False:
			img=img_q.get()
		s.blit(img, (0,0))
		s.blit(tg, (944,10))
		pygame.display.update()



confDict=getConfig(['path','change_interval','default_id','id','sum_refresh'])
pygame.init()
pygame.display.init()
clock = pygame.time.Clock()
img_q=Queue.Queue()
imgLoadQueue=Queue.Queue()
s = pygame.display.set_mode((1024,768))
thickarrow_strings = ("                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ","                        ")
datatuple, masktuple = pygame.cursors.compile( thickarrow_strings,black='.', white='X', xor='o' )
pygame.mouse.set_cursor((24,24),(0,0),datatuple,masktuple)
p1=threading.Thread(target=imageThread,args=[confDict]).start()
p2=threading.Thread(target=clockThread,args=[]).start()

