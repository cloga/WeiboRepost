# -*- coding: cp936 -*-
from __future__ import division
from weibo import APIClient
from urllib2 import HTTPError
from sqlite3 import IntegrityError
import urllib,httplib,urlparse,pickle,sqlite3,random,time,datetime
import json,sys,os,couchdb
import math
#定义供替换的APP Key和Secret
APP_KEYS_SECRETS=[['key1','secret1'],\
                  ['key2','secret2']
                  ]##填入任意个Key Secret对，每对Key Secret是一个List

##随机取出一个app index
current_index=int(random.random()*100 % len(APP_KEYS_SECRETS))
post_id=3528703286207696
edges={}
def access_client(app_index):
    APP_KEY= APP_KEYS_SECRETS[app_index][0] #app key
    APP_SECRET = APP_KEYS_SECRETS[app_index][1] # app secret
    CALLBACK_URL = 'http://www.cloga.info' # callback url
    username=''#填入微博账号
    password=''#填入微博密码
    client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    url = client.get_authorize_url()
    conn = httplib.HTTPSConnection('api.weibo.com')
    postdata = urllib.urlencode({'client_id':APP_KEY,'response_type':'code','redirect_uri':CALLBACK_URL,'action':'submit','userId':username,'passwd':password,'isLoginSina':0,'from':'','regCallback':'','state':'','ticket':'','withOfficalFlag':0})
    conn.request('POST','/oauth2/authorize',postdata,{'Referer':url, 'Content-Type': 'application/x-www-form-urlencoded'})
    res = conn.getresponse()
    page = res.read()
    conn.close()##拿新浪给的code
    code = urlparse.parse_qs(urlparse.urlparse(res.msg['location']).query)['code'][0]
    token = client.request_access_token(code)
    access_token = token.access_token # 新浪返回的token，类似abc123xyz456
    expires_in = token.expires_in # token过期的UNIX时间：http://zh.wikipedia.org/wiki/UNIX%E6%97%B6%E9%97%B4
    # TODO: 在此可保存access token
    client.set_access_token(access_token, expires_in)##生成token
    return client

client=access_client(current_index)

##选取下一个app index
def get_app_index(pre_index):
    if pre_index==len(APP_KEYS_SECRETS)-1:
        return 0
    else:
        return pre_index+1
    
def get_repost_timeline(id,count=200,page=1,max_id=0):
    try:
        return client.statuses.repost_timeline.get(id=id,count=count,page=page,max_id=max_id)
    except Exception,e:
        print e
        global client
        global current_index
        global next_index
        print 'current_index',current_index
        next_index=get_app_index(current_index)
        print 'next_index',next_index
        client=access_client(next_index)
        current_index=next_index
        return get_repost_timeline(id=id,count=count,page=page,max_id=max_id)

def get_show(id):
    try:
        return client.statuses.show.get(id=id)
    except Exception,e:
        print e
        global client
        global current_index
        global next_index
        print 'current_index',current_index
        next_index=get_app_index(current_index)
        client=access_client(next_index)
        current_index=next_index
        print 'next_index',next_index
        return get_show(id=id)

def get_reposts(post_id,max_id=0):
    total_number=get_repost_timeline(id=post_id,count=200)['total_number']
    print total_number
    reposts=[]
    page_reposts=get_repost_timeline(id=post_id,count=200)['reposts']
    reposts+=page_reposts
##    max_id=page_reposts[-1]['id']
##    while len(page_reposts)>0:
##        page_reposts=get_repost_timeline(id=post_id,count=200,max_id=max_id)['reposts']
##        reposts+=page_reposts
##        print len(reposts) 
##        max_id=page_reposts[-1]['id']-1
##        print max_id
    page_number=int(math.ceil(total_number/200))
    print 'total page_numer:',page_number
    if page_number>1:
        for i in range(page_number-1):
            print 'page_numer:',i
            reposts+=get_repost_timeline(id=post_id,count=200,page=i+2)['reposts']
##    reposts=[repost for repost in reposts if repost.has_key('reposts_count')]##有些微博是删除的
    print 'Total Reposts:',len(reposts)
    return reposts

def get_weibo_id(mid):
    pass

def get_edges(post_id,edeges={},length=1):
    reposts=[]
    total_number=get_repost_timeline(id=post_id,count=200)['total_number']
##    print 'Total Number:',total_number
    page_reposts=get_repost_timeline(id=post_id,count=200)['reposts']
    reposts+=page_reposts
    page_number=int(math.ceil(total_number/200))
##    print 'Total Page Number:',page_number
    if page_number>1:
        for i in range(page_number):
##            print 'page_number:',i
            reposts+=get_repost_timeline(id=post_id,count=200,page=i+2)['reposts']
    if length==1:
        print 'total_number:',total_number
        print 'reposts：',len(reposts)
        generate_csv(post_id,reposts)
##        update_couchdb(reposts)
##        generate_timeline(reposts)
    reposts=[repost for repost in reposts if repost.has_key('reposts_count')]##有些微博是删除的
##    print 'Total Reposts:',len(reposts)
    reposted=get_show(id=post_id)['user']['screen_name']
    if reposted=='':
        reposted=str(get_show(id=post_id)['user']['id'])##存在Screen_name为空的情况
    for repost in reposts:
        if repost['user']['screen_name']=='':
            edges[repost['id']]={'poster':str(repost['user']['id']),'reposted':reposted,'content':repost['text'],'created_at':repost['created_at'],'reposts':repost['reposts_count'],'comments':repost['comments_count']}
        else:
            edges[repost['id']]={'poster':repost['user']['screen_name'],'reposted':reposted,'content':repost['text'],'created_at':repost['created_at'],'reposts':repost['reposts_count'],'comments':repost['comments_count']}##存在Screen_name为空的情况
    reposts=[repost for repost in reposts if repost['reposts_count']>0]
    for repost in reposts:
        length+=1
        get_edges(post_id=repost['id'],length=length)        
    return edges,length

def generate_dot(file_name,data):
    OUT = file_name+".dot"
    dot = ['"%s" -> "%s" [weibo_id=%s]' % ( edges[weibo_id]['reposted'].encode('gbk','ignore'),edges[weibo_id]['poster'].encode('gbk','ignore'), weibo_id) for weibo_id in edges.keys()]
    with open(OUT,'w') as f:
        f.write('strict digraph {\nnode [fontname="FangSong"]\n%s\n}' % (';\n'.join(dot),))
        print file_name,'dot file export'
        
def generate_csv(post_id,reposts):
    OUT = str(post_id)+".csv"
    reposts0 = ['%s,%s,%s,%s,%i,%i,%s,%s' % ('\''+str(repost['id']),'http://api.t.sina.com.cn/'+str(repost['user']['id'])+'/statuses/'+str(repost['id']),repost['retweeted_status']['user']['screen_name'].encode('gbk','ignore'),repost['user']['screen_name'].encode('gbk','ignore'),repost['reposts_count'],repost['comments_count'], time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(repost['created_at'].encode('gbk','ignore'),'%a %b %d %H:%M:%S +0800 %Y')),repost['text'].encode('gbk','ignore')) for repost in reposts if repost.has_key('reposts_count')]
    reposts00= ['%s,%s,%s,%s,%i,%i,%s,%s' % ('\''+str(repost['id']),'','','',0,0,time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(repost['created_at'].encode('gbk','ignore'),'%a %b %d %H:%M:%S +0800 %Y')),repost['text'].encode('gbk','ignore')) for repost in reposts if not repost.has_key('reposts_count')]
    with open(OUT,'w') as f:
        f.write('id,url,reposted,poster,reposts,comments,creat_at,text\n%s\n' % ('\n'.join(reposts0+reposts00),))
        print str(post_id),'csv file export'


        
##reposts=get_reposts(post_id)
##generate_csv(post_id,reposts)
edges,length=get_edges(post_id)
print 'edges获取完毕'
print 'edges:',len(edges.keys())
print 'length:',length
##print 'edges:',len(edges.keys())
generate_dot(str(post_id),edges)
##generate_csv(str(post_id))
