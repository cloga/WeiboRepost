# -*- coding: utf-8 -*-
from __future__ import division
from weibo import APIClient
from urllib2 import HTTPError
from sqlite3 import IntegrityError
import urllib,httplib,urlparse,pickle,sqlite3,random,time,datetime
import json,sys,os
import math,csv

post_id=3564503352172330##替换为需要查找微博的MID
edges={}

def access_client():
    client = APIClient(app_key='APP_KEY', app_secret='APP_SECRET', redirect_uri='CALLBACK_URL')
    client.set_access_token('XXXXXXXX','12')##填入获得token
    return client
client=access_client()
def get_repost_timeline(id,count=200,page=1,max_id=0):
    return client.statuses.repost_timeline.get(id=id,count=count,page=page,max_id=max_id)
def get_show(id):
    return client.statuses.show.get(id=id)    

def get_edges(post_id,edeges={},length=1,reposts_length={}):
    reposts=[]
    total_number=get_repost_timeline(id=post_id,count=200)['total_number']
##    print 'Total Number:',total_number
    ##flag参数有问题，翻页获得所有转发
    page_reposts=get_repost_timeline(id=post_id,count=200)['reposts']
    reposts+=page_reposts
    page_number=int(math.ceil(total_number/200))
##    print 'Total Page Number:',page_number
    if page_number>1:
        for i in range(1,page_number):
##            print 'page_number:',i
            reposts+=get_repost_timeline(id=post_id,count=200,page=i+1)['reposts']
    if length==1:
        print 'total_number:',total_number
        print 'reposts：',len(reposts)
        generate_csv(post_id,reposts)##输出转发的CSV,不包含层次关系
    ##生成一个字典记录微博对应的转发层级
        reposts_length={repost['id']:1 for repost in reposts}
        print len(reposts_length)
    reposts=[repost for repost in reposts if repost.has_key('reposts_count')]##有些微博是删除的
##    print 'Total Reposts:',len(reposts)
    reposted=get_show(id=post_id)['user']['screen_name']
    if reposted=='':
        reposted=str(get_show(id=post_id)['user']['id'])##存在Screen_name为空的情况
    for repost in reposts:
        if repost['user']['screen_name']=='':
            edges[repost['id']]={'id':repost['id'],'pid':post_id,'poster':str(repost['user']['id']),'reposted':reposted,'content':repost['text'],'created_at':repost['created_at'],'reposts':repost['reposts_count'],'comments':repost['comments_count'],'length':length}
        else:
            edges[repost['id']]={'id':repost['id'],'pid':post_id,'poster':repost['user']['screen_name'],'reposted':reposted,'content':repost['text'],'created_at':repost['created_at'],'reposts':repost['reposts_count'],'comments':repost['comments_count'],'length':length}##存在Screen_name为空的情况
    reposts=[repost for repost in reposts if repost['reposts_count']>0]
    for repost in reposts:
        reposts_length[repost['id']]+=1##更新微博的层次关系
##        print reposts_length[repost['id']]
        length+=1
        get_edges(post_id=repost['id'],length=length,reposts_length=reposts_length)
    return edges,length,reposts_length

def generate_dot(file_name,data,reposts_length):
    OUT = file_name+"_utf8.dot"
    OUT1 = file_name+'_edges_utf8'+".csv"
    dot = ['"%s" -> "%s" ["weibo_id"="%s"]' % ( edges[weibo_id]['pid'],edges[weibo_id]['id'], weibo_id) for weibo_id in edges.keys()]
    label0=['"%s" [label="%s"];' % ( edges[weibo_id]['id'],edges[weibo_id]['poster'].encode('utf-8','ignore')) for weibo_id in edges.keys()]
    dot1 = ['%s,%s,\'%s,%s' % ( edges[weibo_id]['reposted'].encode('utf-8','ignore'),edges[weibo_id]['poster'].encode('utf-8','ignore'), weibo_id,reposts_length[weibo_id]) for weibo_id in edges.keys()]
    with open(OUT,'wb') as f:
        f.write('strict digraph {\nnode [fontname="FangSong"]\n%s;\n' % (';\n'.join(dot),))
        f.write('\n'.join(label0))
        f.write('\n"'+str(post_id)+'"'+' [label="'+get_show(post_id)['user']['screen_name'].encode('utf-8','ignore')+'"];')
        f.write('\n}')
        print file_name,'dot file export'
    with open(OUT1,'wb') as f:    
        f.write('poster,reposter,weiboid,length\n'+'\n'.join(dot1))
        print file_name,'edge file export'
        
def generate_csv(post_id,reposts):
    OUT = str(post_id)+".csv"
    reposts0 = [['\''+str(repost['id']),'http://api.t.sina.com.cn/'+str(repost['user']['id'])+'/statuses/'+str(repost['id']),repost['retweeted_status']['user']['screen_name'].encode('utf-8','ignore'),repost['user']['screen_name'].encode('utf-8','ignore'),repost['reposts_count'],repost['comments_count'], time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(repost['created_at'].encode('utf-8','ignore'),'%a %b %d %H:%M:%S +0800 %Y')),repost['text'].encode('utf-8','ignore')] for repost in reposts if repost.has_key('reposts_count')]
    reposts00= [['\''+str(repost['id']),'','','',0,0,time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(repost['created_at'].encode('utf-8','ignore'),'%a %b %d %H:%M:%S +0800 %Y')),repost['text'].encode('utf-8','ignore')] for repost in reposts if not repost.has_key('reposts_count')]
    with open(OUT,'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['id','url','reposted','poster','reposts','comments','creat_at','text'])
        writer.writerows(reposts0+reposts00)
        print str(post_id),'csv file export'


        
edges,length,reposts_length=get_edges(post_id)
##print 'edges获取完毕'
##print 'edges:',len(edges.keys())
##print 'length:',length
####print 'edges:',len(edges.keys())
generate_dot(str(post_id),edges,reposts_length)
##print '当前路径为:'+os.getcwd()
