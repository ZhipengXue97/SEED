# coding=utf-8
"""
	顾名思义 我是个爬虫
	作用: 爬取codeforces的代码并自动提交
	作者: 大哥
"""
import random
import re
import time
import threading
import requests
from bs4 import BeautifulSoup
from lxml import etree
import os

#用户名
name='543984341@qq.com'
#密码
password='xzp971007'

user_agent = [
	'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 '
	'Safari/534.50',
	'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
	'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',
	'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; '
	'.NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko',
	'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
	'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
	'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
	'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
	'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
	'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 '
	'Safari/535.11',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR '
	'2.0.50727; SE 2.X MetaSr 1.0)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
	'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
	'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) '
	'Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
	'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) '
	'Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
	'Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 '
	'Mobile/8J2 Safari/6533.18.5',
	'Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) '
	'Version/4.0 Mobile Safari/533.1',
	'MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 ('
	'KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
	'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10',
	'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 '
	'Safari/534.13',
	'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile '
	'Safari/534.1+',
	'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 '
	'Safari/534.6 TouchPad/1.0',
	'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) '
	'AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
	'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)',
	'UCWEB7.0.2.37/28/999',
	'NOKIA5700/ UCWEB7.0.2.37/28/999',
	'Openwave/ UCWEB7.0.2.37/28/999',
	'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999', ]
s=requests.session()
#登录
def login():
	agent=random.choice(user_agent)
	header={'User-Agent' : agent}
	s.headers.update(header)
	try:
		res = s.get('http://codeforces.com/enter?back=%2F')
		soup=BeautifulSoup(res.text,'lxml')
		csrf_token=soup.find(attrs={'name' : 'X-Csrf-Token'}).get('content')
		form_data={
			'csrf_token' : csrf_token,
			'action' : 'enter',
			'ftaa' : '',
			'bfaa' : '',
			'handleOrEmail' : name,
			'password' : password,
			'remember' : []
		}
		s.post('http://codeforces.com/enter',data=form_data)
	except Exception as e:
		print('登陆失败',e)
#获取代码
def getcode(a,b) :
	os.mkdir('D:/codeforces/' + a + b)
	res=s.get('http://codeforces.com/problemset/submit')
	soup=BeautifulSoup(res.text,'lxml')
	csrf_token=soup.find(attrs={'name' : 'X-Csrf-Token'}).get('content')
	data={
		'csrf_token' : csrf_token,
		'action' : 'setupSubmissionFilter',
		'frameProblemIndex' : b,
		'verdictName' : 'OK',
		'programTypeForInvoker' : 'java8',
		'comparisonType' : 'NOT_USED',
		'judgedTestCount' : '',
	}
	s.post('https://codeforces.com/contest/'+a+'/status',data=data)
	res=s.get('https://codeforces.com/contest/'+a+'/status')
	links=re.findall('submission/(.+?)"',res.text)
	if len(links)<=0 :
		return False
	for i in range(len(links)):
		res2=s.get('https://codeforces.com/contest/'+a+'/submission/'+links[i])
		selector=etree.HTML(res2.text.encode("utf-8","ignore"))
		out=selector.xpath('//*[@id="program-source-text"]')[0]
		file_name = 'D:/codeforces/'+a+b + "/" + str(i)+'.java'
		f = open(file_name, "w",encoding='utf-8')
		f.write(out.text)
		print('题号:', a + b + str(i), '获取代码成功')
		time.sleep(5)
	print('题号:',a+b,'获取代码成功')
	return out.text

def getname(a,b):
	url = "http://codeforces.com/contest/"+ a +"/problem/" + b
	html = s.get(url).text
	name = re.findall(r'<div class="title">(.*?)</div>',html)[0]
	name = name.split(".")[-1].strip()
	return name


def solve(a) :
	global s
	html=s.get('https://codeforces.com/contest/'+a).text
	if not html :
		return
	links=re.findall('<a href="/contest/'+a+'/problem/(.+?)"><!--',html)
	setlinks=set(links)
	links=list(setlinks)
	links.sort()
	for b in links :
		if len(b)<3 :
			# getcode(a,b)
			name = getname(a,b)
			with open("name.txt",'a+')as f:
				print(a+b+":"+name)
				f.write(a+b+":"+name+"\n")
			time.sleep(2)
	print('solve:',a)


login()
f = int(input('from:'))
for a in range(f,501) :
	solve(str(a))
	# threading.Thread(target=solve, args=(str(a),)).start()
	# time.sleep(10)

