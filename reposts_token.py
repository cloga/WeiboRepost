# -*- coding: utf-8 -*-
from __future__ import division
from weibo import APIClient
from urllib2 import HTTPError
from sqlite3 import IntegrityError
import urllib,httplib,urlparse,pickle,sqlite3,random,time,datetime
import json,sys,os
import math

post_id=3552242097011889##替换为需要查找微博的MID
edges={}
def access_client():
    client = APIClient(app_key='APP_KEY', app_secret='APP_SECRET', redirect_uri='CALLBACK_URL')
    client.set_access_token('2.00Hk5I5B3mz1gE5d178ada323SS3HB','12')##填入获得token
    return client

client=access_client()

def get_repost_timeline(id,count=200,page=1,max_id=0):
    return client.statuses.repost_timeline.get(id=id,count=count,page=page,max_id=max_id)

def get_show(id):
    return client.statuses.show.get(id=id)
    
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
    OUT1 = file_name+'_edges'+".csv"
    dot = ['"%s" -> "%s" [weibo_id=%s]' % ( edges[weibo_id]['reposted'].encode('gbk','ignore'),edges[weibo_id]['poster'].encode('gbk','ignore'), weibo_id) for weibo_id in edges.keys()]
    dot1 = ['%s,%s,%s' % ( edges[weibo_id]['reposted'].encode('gbk','ignore'),edges[weibo_id]['poster'].encode('gbk','ignore'), weibo_id) for weibo_id in edges.keys()]
    with open(OUT,'w') as f:
        f.write('strict digraph {\nnode [fontname="FangSong"]\n%s\n}' % (';\n'.join(dot),))
        print file_name,'dot file export'
    with open(OUT1,'w') as f:    
        f.write('poster,reposter,weiboid\n'+'\n'.join(dot1))
        print file_name,'edge file export'
        
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
print '当前路径为:'+os.getcwd()
