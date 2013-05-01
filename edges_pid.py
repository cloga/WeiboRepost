# -*- coding: utf-8 -*-
from __future__ import division
from weibo import APIClient
from urllib2 import HTTPError
import urllib,httplib,urlparse,time,datetime
import json,sys,os
import math,csv
from pandas import DataFrame
import networkx as nx
import matplotlib


post_id=3572508797738487##替换为需要查找微博的MID

def access_client():
    client = APIClient(app_key='APP_KEY', app_secret='APP_SECRET', redirect_uri='CALLBACK_URL')
    client.set_access_token('2.00Hk5I5B3mz1gEda51bd5caewZ5BMC','12')##填入获得token,形式为2.00Hk5I5B3mz1gEda51bd5caewZ5BMC
    return client
client=access_client()
def get_repost_timeline(id,count=200,page=1,max_id=0):
    return client.statuses.repost_timeline.get(id=id,count=count,page=page,max_id=max_id)
def get_comment_show(id,count=200,page=1,max_id=0):
    return client.comments.show.get(id=id,count=count,page=page,max_id=max_id)
def get_show(id):
    return client.statuses.show.get(id=id)
def get_edges(post_id,edges=[],reposts=[]):
##repost:weibo_mid,pid,weibo_url,original_mid,original_poster,original_poster_id,original_weibo_url,original_content,poster,poster_id,content,created_at,repost,comment
    total_number=get_repost_timeline(id=post_id,count=200)['total_number']
##    print 'Total Number:',total_number
    ##flag参数有问题，翻页获得所有转发,有可能缺失
    page_reposts=get_repost_timeline(id=post_id,count=200)['reposts']
    reposts+=page_reposts
    page_number=int(math.ceil(total_number/200))
##    print 'Total Page Number:',page_number
    for i in range(1,page_number):
##            print 'page_number:',i
        reposts+=get_repost_timeline(id=post_id,count=200,page=i+1)['reposts']
    for repost in reposts:
        edge=dict(
            weibo_mid=repost['id'],
            weibo_url='http://api.t.sina.com.cn/'+str(repost['user']['id'])+'/statuses/'+str(repost['id']),
            original_mid=repost['retweeted_status']['id'],
            pid=repost.get('pid',repost['retweeted_status']['id']),
            original_poster_id=repost['retweeted_status']['user']['id'],
            original_poster=repost['retweeted_status']['user']['screen_name'].encode('utf-8','ignore'),
            original_weibo_url='http://api.t.sina.com.cn/'+str(repost['retweeted_status']['user']['id'])+'/statuses/'+str(repost['retweeted_status']['id']),
##            original_content=repost['retweeted_status']['text'].encode('utf-8','ignore'),
            poster=repost['user']['screen_name'].encode('utf-8','ignore'),
            poster_id=repost['user']['id'],
            content=repost['text'].encode('utf-8','ignore'),
            created_at=repost['created_at'],
            repost=repost['reposts_count'],
            comment=repost['comments_count'])
        edges.append(edge)
    DataFrame(edges).to_csv(str(post_id)+'_edges_utf8.csv',index=False)
    print '当前路径为:'+os.getcwd()
    print 'edges获取完毕'
    generate_dot(str(post_id),edges)
    DG=nx.DiGraph(nx.read_dot(str(post_id)+"_utf8.dot"))
    nx.write_gexf(DG, str(post_id)+".gexf")
    print 'generated GEXF complete!'
    return edges
def get_comments(post_id,comments_list=[],comments=[]):
    total_number=get_comment_show(post_id)['total_number']
    page_number=int(math.ceil(total_number/200))
    for i in range(1,page_number+1):
        comments+=get_comment_show(post_id,page=i)['comments']
    for c in comments:
        comment=dict(
            comment_content=c['text'].encode('utf-8','ignore'),
            comment_created_at=c['created_at'],
            comment_mid=c['mid'],
            comment_source=c['source'].encode('utf-8','ignore'),
            comment_user_screen_name=c['user']['screen_name'].encode('utf-8','ignore'),
            comment_user_id=c['user']['id'],
            original_mid=c['status']['mid'],
            original_content=c['status']['text'].encode('utf-8','ignore'),
            original_screen_name=c['status']['user']['screen_name'].encode('utf-8','ignore'))
        comments_list.append(comment)
    DataFrame(comment_list).to_csv(str(post_id)+'_comments_utf8.csv',index=False)
    print 'generated comments csv completed!'
    return comments_list

def generate_dot(file_name,data):
    OUT = file_name+"_utf8.dot"
    dot = ['"%s" -> "%s" ["weibo_id"="%s"]' % ( edge['pid'],edge['weibo_mid'], edge['weibo_mid']) for edge in edges]
    label=['"%s" [label="%s"];' % ( edge['weibo_mid'],edge['poster']) for edge in edges]
    with open(OUT,'wb') as f:
        f.write('strict digraph {\nnode [fontname="FangSong"]\n%s;\n' % (';\n'.join(dot),))
        f.write('\n'.join(label))
        f.write('\n"'+str(post_id)+'"'+' [label="'+get_show(post_id)['user']['screen_name'].encode('utf-8','ignore')+'"];')
        ##输出原帖作者
        f.write('\n}')
        print file_name,'dot file export'

comment_list=get_comments(post_id)
##edges=get_edges(post_id)
