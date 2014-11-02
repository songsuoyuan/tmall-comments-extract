#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import time
import random
import urllib
import urllib2
import MySQLdb
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

SEARCH = 'http://list.tmall.com/search_product.htm'
RATE   = 'http://rate.tmall.com/list_detail_rate.htm'

def request(url, **kw):
    """
    return urlopen result, raise ConnectionError if response code is not 200

    >>> request(SEARCH, q='苹果手机', s=0)
    '<!DOCTYPE HTML>
    <html>
    ...'
    
    """
    req = urllib2.Request(parse_url(url, **kw))
    req.add_header('Accept-Language', 'zh-CN,zh')
    response = urllib2.urlopen(req)
    if (response.code != 200):
        raise ConnectionError('%d, %s' % (response.code, response.msg))
    return response.read().decode('gbk').encode('utf-8')

def parse_url(url, **kw):
    """
    parse url from dictionary params
    
    >>> parse_url(SEARCH, q='iphone6', s=0)
    'http://list.tmall.com/search_product.htm?q=iphone6&s=0'

    >>> parse_url(SEARCH, q='苹果手机', s=59)
    'http://list.tmall.com/search_product.htm?q=%C6%BB%B9%FB%CA%D6%BB%FA&s=59'

    """
    args = []
    for k, v in kw.iteritems():
        v = str(v).decode('utf-8').encode('gbk')
        args.append('%s=%s' % (k, urllib.quote(v)))
    return url + '?' + '&'.join(args)

def match(source):
    """
    source:
    <p class="productTitle"><
    <a href="//detail.tmall.com/item.htm?id=27465092661&amp;skuId=49350663223
    &amp;areaId=440300&amp;cat_id=50024400&amp;standard=1&amp;
    sku_properties=1627207:3232481;10004:3231342;12304035:48072;
    5919063:6536025;null" target="_blank" title="Apple/苹果 iPhone 5s" 
    atpanel="1-11,27465092661,1512,1000004538042116,spu,1,spu,263726286">
    Apple/<span class=H>苹果</span> iPhone 5s
    </a>
    </p>
    <div class="productCSPU clearfix">
       <span title="深空灰色">深空灰色</span>
       <span title="WCDMA(3G)">WCDMA(3G)</span>
       <span title="16g">16g</span>
       </div>
    <div class="productShop">
    <a class="productShop-name" href="search_shopitem.htm?user_id=263726286&
    from=_1_&stype=search" target="_blank"
    atpanel="1-3,263726286,,,spu,2,spu,263726286">
    能良数码官方旗舰店
    </a>

    retrieve:
    {store: '能良数码官方旗舰店', title: 'Apple/苹果 iPhone 6', id: 27465092661
        user_id: 263726286}

    """
    regex_shop = \
        '<a class="productShop-name"[\s\S]*?atpanel="[\s\S]*?">\n\s(.*?)\n'
    regex_shop_id = \
        '<a class="productShop-name"[\s\S]*?user_id=([0-9]*)'
    regex_product = \
        '<p class="productTitle">[\s\S]*? title="(.*?)" atpanel'
    regex_product_id = \
        '<p class="productTitle">[\s\S]*?id=([0-9]*)'

    shop_list       = re.findall(regex_shop,       source)
    shop_id_list    = re.findall(regex_shop_id,    source)
    product_list    = re.findall(regex_product,    source)
    product_id_list = re.findall(regex_product_id, source)

    def assert_equal(x, y, z, w):
        return len(x) == len(y) and len(x) == len(z) and len(x) == len(w)

    if not assert_equal(shop_list, shop_id_list, product_list, 
        product_id_list):
        print len(shop_list), len(shop_id_list)
        print len(product_list), len(product_id_list)
        print source

    tmp_list = []
    for name in shop_list:
        name = name.replace('<span class=H>','')
        name = name.replace('</span>','')
        tmp_list.append(name)

    shop_list = tmp_list

    all_list = zip(product_id_list, zip(product_list, shop_id_list, shop_list))
    all_set  = set(all_list)
    print len(all_set), 'product id was crawled from source.'
    return dict(all_set)

def scratch_list(pages=1):
    d = dict()
    for i in range(pages):
        res = request(SEARCH, q='苹果手机', s=60*i)
        d.update(match(res))
    return d

def scratch_source(product_id, shop_id, pages=1):
    def clean(res):
        """
        convert json text from request(url, **kw) to python list
        """
        def obj_hook(dic):
            """
            delete meaningless attributes anf convert annoying unicode 
            string to utf-8
            """
            o = dict()
            for k, v in dic.iteritems():
                if k in [ u'aliMallSeller', u'appendComment', u'attributes',
                    u'buyCount', u'cmsSource', u'displayUserLink', 
                    u'displayUserNumId', u'displayUserRateLink', u'dsr',
                    u'fromMall', u'fromMemory', u'pics', u'position',
                    u'serviceRateContent', u'tmallSweetPic', u'useful', 
                    u'userIdEncryption', u'userInfo', u'userVipLevel',
                    u'userVipPic']:
                    continue
                if isinstance(v, basestring):
                    v = v.encode('utf-8') if isinstance(v, unicode) else v
                o[k.encode('utf-8')] = v
            return o

        s = re.findall('"rateList":([\S\s]*),"tags"', res)[0]
        l = json.loads(s, object_hook=obj_hook)
        return l

    d = {'itemId':product_id, 'sellerId':shop_id, 'order':1, 'currentPage':1}
    print 'downloading page', 1, '...'
    res   = request(RATE, **d)
    total = re.search('"total":(\d*)', res).groups()[0]
    l = clean(res)
    max_pages = min(pages, int(total)/20+1)
    for i in range(2, max_pages):
        print 'downloading page', i, '...'
        d['currentPage'] = i
        res = request(RATE, **d)
        n   = clean(res)
        if len(n) == 0:
            print 'no more comments, stopped at page', i, '...'
            break
        l = l + n
    return l


# test code:
# ---------

# initial
# ---------
db = MySQLdb.connect("localhost","Suoyuan","jiayuan","test")
cursor = db.cursor()
cursor.execute("set names utf8;")

l = scratch_list(2)
for k in l:
    t = random.randint(1, 5)
    print 'sleep', t, 'second...'
    time.sleep(t)
    print 'scratch product id ', k , 'from', l[k][2], '...'
    product_id = k
    shop_id = l[k][1]
    li = scratch_source(product_id, shop_id, 100)
    for d in li:
        sql = """INSERT INTO comment_list(ID, IS_ANONY, USERNAME, 
        LEVEL, RATE_SUM, CONTENT, REPLY, SWEET, RATE_DATE, MODEL, 
        PRODUCT_ID, SHOP_ID)
        VALUES ('%s',%s,'%s','%s',%s,'%s','%s',%s,'%s','%s','%s','%s') 
        """ % (d['id'], d['anony'], d['displayUserNick'], 
               d['displayRatePic'], d['displayRateSum'], 
               d['rateContent'], d['reply'], d['tamllSweetLevel'],
               d['rateDate'], d['auctionSku'], product_id, shop_id)
        cursor.execute(sql)
        db.commit()

db.close()


# test comment_list
# ------
# l = scratch_source(27465092661, 263726286, 30)
# print len(l)
# 
# db = MySQLdb.connect("localhost","Suoyuan","jiayuan","test")
# cursor = db.cursor()
# cursor.execute("set names utf8;")
# 
# for d in l:
#     sql = """INSERT INTO comment_list(ID, IS_ANONY, USERNAME, 
#     LEVEL, RATE_SUM, CONTENT, REPLY, SWEET, RATE_DATE, MODEL, 
#     PRODUCT_ID, SHOP_ID)
#     VALUES ('%s',%s,'%s','%s',%s,'%s','%s',%s,'%s','%s','%s','%s') 
#     """ % (d['id'], d['anony'], d['displayUserNick'], 
#            d['displayRatePic'], d['displayRateSum'], 
#            d['rateContent'], d['reply'], d['tamllSweetLevel'],
#            d['rateDate'], d['auctionSku'], 41610740393, 713805254)
#     cursor.execute(sql)
#     db.commit()
# 
# db.close()


# test shop_list
# ------
# print l[418]['rateContent']

# db = MySQLdb.connect("localhost","Suoyuan","jiayuan","test")
# cursor = db.cursor()
# cursor.execute("set names utf8;")
# 
# d = scratch_list(2)
# for k in d:
#     sql = """INSERT INTO shop_list(PRODUCT_ID,
#              PRODUCT_NAME, SHOP_ID, SHOP_NAME, SEARCH_KEYWORD)
#              VALUES ('%s', '%s', '%s', '%s', '%s') """ % (k, 
#              d[k][0], d[k][1], d[k][2], '苹果手机')
#     cursor.execute(sql)
#     db.commit()
# 
# db.close()