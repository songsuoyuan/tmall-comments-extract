#!/usr/bin/env python
#coding=utf-8

import re
import urllib2
import time
import sys, os
import urllib



def Tmall_tagCollect(itemId, sellerId, data_path=''):
	filename = data_path + 'Tag_' + str(itemId) + '_' + str(sellerId) + '.txt'
	f = open(filename,'w')
	req = urllib2.Request('http://rate.tmall.com/listTagClouds.htm?itemId='+ str(itemId) +'&isAll=true&isInner=true&t='+str(sellerId)+'&callback=jsonp2003')
	response = urllib2.urlopen(req)
	the_page = response.read()
	f.write(the_page)
	tag_id = re.findall('{\"count\":[0-9]*?,\"id\":\"([0-9]*?)\",\"posi\":(.*?),\"tag\":\".*?\",\"weight\":[0-9]*?}', the_page)
	time.sleep(0.2)
	return(tag_id)

def Tmall_reviewCollect(itemId,sellerId,data_path='',tagId='', posi='', max_pages=100):
	if tagId == '':
		filename = data_path + 'Tmall_' + str(itemId) + '_' + str(sellerId) + '.txt'
	else:
		filename = data_path + 'Tmall_' + str(itemId) + '_' + str(sellerId) + '_' \
		+ str(tagId) + _ str(posi) + '.txt'
	f = open(filename,'w')
	page = 1
	while True:
		req = urllib2.Request('http://rate.tmall.com/list_detail_rate.htm?itemId='+ \
			str(itemId) +'&sellerId='+str(sellerId)+'&order=1&currentPage='+ str(page) +\
			'tagId=' + str(tagId) + 'posi=' + str(posi) + '&callback=jsonp3023')
		response = urllib2.urlopen(req)
		the_page = response.read()
		f.write(the_page)
		try:
			paginator = re.findall('\"paginator\":{\"items\":([0-9]*?),"lastPage":([0-9]*?),"page":([0-9]*?)}',the_page)[0]
		except Exception, e:
			print e
		if paginator[1] == paginator[2] or page > max_pages:
			break
		page += 1
		time.sleep(0.2)
	f.close()

def Tmall_searchCollect(search_content,data_path='',max_pages=100):
	allId = []
	page = 0
	filename = data_path + 'Tmall_' + search_content + '.txt'	
	f = open(filename,'w')
	while True:
		url = 'http://list.tmall.com/search_product.htm?q='+ search_content + '&s=' + str(60*page)
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		the_page = response.read()
		try:
			result = re.findall('\?id=([0-9]*)&.*?user_id=([0-9]*?)&',the_page)
			allId_thispage = list(set(result))
		except Exception, e:
			print e
		page += 1
		allId.extend(allId_thispage)
		if page > max_pages or len(allId_thispage) == 0:
			break
		time.sleep(0.2)
	for x in allId:
		for k in x:
			f.write(k)
			f.write('\t')
		f.write('\n')
	f.close()
	return(allId)

def Tmall_searchandreview(search_content,data_path,search_max_pages=100,review_max_pages=100):
	search_content = search_content.decode('utf-8').encode('gbk')
	search_content = urllib.quote(search_content)
	data_path = data_path+'Tmall_'+search_content + '/'
	os.mkdir(data_path)
	allId = Tmall_searchCollect(search_content, data_path, search_max_pages)
	for oneId in allId:
	  	print oneId[0]
	  	Tmall_reviewCollect(oneId[0], oneId[1], data_path, review_max_pages)


# Tmall_searchandreview('王楷', 'C:/data/', 1)

temp = Tmall_tagCollect(3459421898, 294040860)



