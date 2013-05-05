# -*- coding: utf-8 -*-
from __future__ import division
from weibo import APIClient
from urllib2 import HTTPError
import urllib,httplib,urlparse,time,datetime,sqlite3
import json,sys,os
import math,csv
from pandas import DataFrame
import networkx as nx
import matplotlib
from collections import Counter
from sqlite3 import IntegrityError



def access_client():
    client = APIClient(app_key='APP_KEY', app_secret='APP_SECRET', redirect_uri='CALLBACK_URL')
    client.set_access_token('XXXXX','12')##填入获得token,形式为2.00Hk5I5B3mz1gEda51bd5caewXXXYY
    return client

def get_repost_timeline(id,count=200,page=1,max_id=0):
    return client.statuses.repost_timeline.get(id=id,count=count,page=page,max_id=max_id)
def get_comment_show(id,count=200,page=1,max_id=0):
    return client.comments.show.get(id=id,count=count,page=page,max_id=max_id)
def get_user_show(uid=0,screen_name=''):
    if uid:
        return client.users.show.get(uid=uid)
    if screen_name:
        return client.users.show.get(screen_name=screen_name)
def get_tags(uid):
    '''存在uid不存在的情况
    '''
    try:
        return client.tags.get(uid=uid)
    except:
        return []
def get_friends(uid=0,screen_name='',page=1,count=200):
    if uid:
        return client.friendships.friends.get(uid=uid,page=page,count=count)
    if screen_name:
        return client.friendships.friends.get(screen_name=screen_name,page=page,count=count)
def get_user_timeline(uid=0,screen_name='',count=100,page=1):
    if uid:
        return client.statuses.user_timeline.get(uid=uid,count=count,page=page)
    if screen_name:
        return client.statuses.user_timeline.get(screen_name=screen_name,count=count,page=page)
def get_fans_ids(uid,count=5000):
    '''给定uid返回5000个粉丝的uid，list'''
    return client.friendships.followers.ids.get(uid=uid,count=count)['ids']
def generate_dot(file_name,data):
    '''生成Dot文件,get_edges会用到
    '''
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
def generate_word_cloud(prefix,fans_tags):
    head='''<html>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <script src="http://wordcloud.cloga.info/src/wordcloud2.js"></script>
            <div class="span12" id="canvas-container">
                            <canvas width="1024" height="760" id="canvas"></canvas>
                            </div>
            <script >
            WordCloud(document.getElementById('canvas'), {list:'''
    bottom='''});
            </script>
            </html>
            '''
    ##fans_tags是dict of list，需要转换为list of list的字符串形式
    f_tags=''
    for i in fans_tags:
        f_tags+='[\''+i['tag']+'\','+str(i['frequency'])+'],'
    with open(prefix+'_fans_tags.html','wb') as f:
        f.write(head+'['+f_tags+']'+bottom)
    print '当前路径为:'+os.getcwd()
    print prefix+'_fans_tags.html','generated!'

def get_repost_edges(post_id,edges=[],reposts=[]):
    '''获得转发路径，生成Dot文件，CSV及GEXF文件
    '''
    total_number=get_repost_timeline(id=post_id,count=200)['total_number']
    ##print 'Total Number:',total_number
    ##flag参数有问题，翻页获得所有转发,有可能缺失
    page_reposts=get_repost_timeline(id=post_id,count=200)['reposts']
    reposts+=page_reposts
    page_number=int(math.ceil(total_number/200))
    ##print 'Total Page Number:',page_number
    for i in range(1,page_number):
        ##print 'page_number:',i
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
            ##original_content=repost['retweeted_status']['text'].encode('utf-8','ignore'),
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
    '''获得指定微博的所有转发
    '''
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


def get_posts(uid=0,screen_name='',posts=[],contents=[]):
    '''获得指定作者的所有微博，输入微博名称和uid都可以
    '''
    total_number=get_user_timeline(uid,screen_name)['total_number']
    page_number=int(math.ceil(total_number/200))
    for i in range(1,page_number+1):
        contents+=get_user_timeline(uid,screen_name,page=i)['statuses']
    for c in contents:
        post=dict(
            post_content=c['text'].encode('utf-8','ignore'),
            post_created_at=c['created_at'],
            post_mid=c['mid'],
            post_source=c['source'].encode('utf-8','ignore'),
            post_user_screen_name=c['user']['screen_name'].encode('utf-8','ignore'),
            post_user_id=c['user']['id'],
            reposts=c['reposts_count'],
            comments=c['comments_count'])
        posts.append(post)
    DataFrame(posts).to_csv(posts[0]['post_user_screen_name']+'_repost_utf8.csv',index=False)
    print 'generated',posts[0]['post_user_screen_name'],'posts csv completed!'
    return posts

def count_tags(uids,topN=0,tags=[],t=[]):
    '''给定一组uid，计算用户tag的频率
    '''
    for uid in uids:
        for i in get_tags(uid):##返回一个list，其中每个元素为一个字典
            t+=[i[m] for m in i.keys() if m!='weight']
    if topN:#用topN决定返回的标签数
        c=Counter(t).most_common(topN)
    else:
        c=Counter(t).most_common()
    tags=[dict(tag=i[0].encode('utf-8','ignore'),frequency=i[1]) for i in c]
    #返回一个list，形式为[('a', 5), ('r', 2), ('b', 2)]
    #与上面代码的作用一样
    #        for i in set(t):
    #         tags.append(dict(
    #             tag=i.encode('utf-8','ignore'),
    #             frequency=t.count(i)
    #         ))
    #     tags.sort(key = lambda i: i['frequency'],reverse=True)##处理为按照frequency降序排列的list
    return tags
def get_fans_tags(uid=0,screen_name=''):
    if screen_name:
        print 'screen_name',screen_name
        uid=get_user_show(screen_name=screen_name)['id']
    if uid:
        print 'uid',uid
        screen_name=get_user_show(uid=uid)['screen_name']
    print screen_name
    fans_ids=get_fans_ids(uid)
    print 'fans:',len(fans_ids)
    tags=count_tags(fans_ids)
    DataFrame(tags).to_csv(screen_name+'_fans_tags_utf8.csv',index=False)
    print screen_name,'fans tags generated!'
    print '当前路径为:'+os.getcwd()
    return tags
def get_all_friends(uid):
    '''给定一个uid，返回所有关注的list,每个元素是一个dict
    '''
    friends=[]
    total_number=get_friends(uid=uid)['total_number']
    ##flag参数有问题，翻页获得所有转发,有可能缺失
    page_number=int(math.ceil(total_number/200))
    for i in range(0,page_number):
        friends+=get_friends(uid=uid,count=200,page=i+1)['users']
    print uid,'get_all_friends done!'
    return friends
def store_users_in_db(users,crawled=0):
    query='INSERT INTO users VALUES(?,?,?)'    
    data=[[u['id'],u['screen_name'],crawled] for u in users]
    curs.executemany(query,data)
def store_following_edges_in_db(edges):
    query='INSERT INTO following_edges VALUES(?,?)'    
    data=[[e[0],e[1]] for e in edges]
    curs.executemany(query,data)
def get_uncrawled_users():
    query='SELECT user_uid FROM users WHERE crawled=0'
    curs.execute(query)
    users=curs.fetchall()
    print '还有',len(users),'用户需抓取'
    return users
def get_all_users():
    query='SELECT user_uid FROM users'
    curs.execute(query)
    users=curs.fetchall()
    print '共有',len(users),'用户'
    return users
def update_fans_crawled(uid):
    update='''UPDATE users SET crawled=1 WHERE user_uid=?'''
    curs.execute(update,(uid,))
    conn.commit()
def db_con(db):
    global conn
    global curs
    conn = sqlite3.connect(db)
    curs = conn.cursor()
    return conn,curs
def clear_db():
    q='''DELETE FROM users'''
    curs.execute(q)
    q='''DELETE FROM following_edges'''
    curs.execute(q)
    conn.commit()
def get_following_edges(uid=0,screen_name=''):
    '''给定一个uid获得相关user的following关系，用SQLite做中介,只抓取一层，广度优先的话量实在太大
    '''
    if not screen_name:
        screen_name=get_user_show(uid)['screen_name']
    user_o=get_all_friends(uid)#dict of list
    user_a=[i[0] for i in get_all_users()]# turple of list
    store_users_in_db([u for u in user_o if u['id'] not in user_a])
    edges=[[uid,u['id']]for u in user_o]
    store_following_edges_in_db(edges)
    if uid not in user_a:
        store_users_in_db([{'id':uid,'screen_name':screen_name}],1)
    for u in user_o:
        print len(user_o),' of ' ,user_o.index(u)
        user_c=get_all_friends(u['id'])#dict of list
        user_a=[i[0] for i in get_all_users()]# turple of list
        store_users_in_db([u for u in user_c if u['id'] not in user_a])
        edges=[[u['id'],i['id']]for i in user_c]
        store_following_edges_in_db(edges)
        update_fans_crawled(u['id'])
    print 'fetch users completed!'
        
##    while len(get_uncrawled_users())>0:
##        user_u=get_uncrawled_users()
##        uid=user_u[0][0]
##        user_c=get_all_friends(uid)
####        user_a=[i[0] for i in get_all_users()]
####        users=[u for u in user_c if u['id'] not in user_a]
####        store_users_in_db(users)
##        edges=[[uid,u['id']]for u in user_c]
##        store_following_edges_in_db(edges)
##        update_fans_crawled(uid)
       
##def get_following_edges(uid,edges=[],users_ids=set(),screen_name=''):
##    '''给定一个uid获得相关user的following关系
##    '''
##    if not screen_name:
##        screen_name=get_user_show(uid)['screen_name']
##    users_o=get_all_friends(uid)
##    users_c={i['id']:i['screen_name'] for i in users_o}
##    users_ids.update(set([i['id'] for i in users_o]))
##    edges+=[dict(
##            user_uid=uid,
##            user=screen_name,
##            following_uid=k,
##            following=users_c[k]
##            ) for k in users_c]
##    for i in users_ids:
##        print 'uid:',i
##        print 'users length:',len(users_ids)
##        print 'edges length:',len(edges)
##        get_following_edges(i,edges=edges,users_ids=users_ids)
##    return users_ids,edges
def get_following_edges_from_db():
    q='''SELECT source_uid,target_uid FROM following_edges
    '''
    q2='''SELECT user_uid,user_screen_name FROM users
    '''
    users=curs.execute(q).fetchall()
    edges=curs.execute(q2).fetchall()
    return users,edges
def generate_dot_following(users,edges,file_name,encode='utf-8'):
    '''生成Dot文件
    '''
    OUT = file_name.decode('utf-8','ignore')+'_following_'+encode+'.dot'##中文需为unicode编码
    dot = ['"%s" -> "%s" ' % ( e[0],e[1]) for e in edges]
    label=['"%s" [label="%s"];' % (u[0],u[1].encode(encode,'ignore')) for u in users]
    with open(OUT,'wb') as f:
        f.write('strict digraph {\nnode [fontname="FangSong"]\n%s;\n' % (';\n'.join(dot),))
        f.write('\n'.join(label))
        ##输出原帖作者
        f.write('\n}')
        print OUT,'exported'
    DG=nx.DiGraph(nx.read_dot(OUT))
    nx.write_gexf(DG, file_name+"_following_utf-8.gexf")
    print 'generated GEXF complete!'


client=access_client()
screen_name='cloga在路上'
##post_id=3572508797738487##替换为需要查找微博的MID
uid=get_user_show(screen_name=screen_name)['id']
db_con('weibo.db')
users,edges=get_following_edges_from_db()
generate_dot_following(edges,users,screen_name,'utf-8')
##clear_db()
##users=get_all_friends(uid)
##fans_tags=get_fans_tags(uid)
#print fans_tags[0]
##get_following_edges(uid)
##print len(get_all_friends(2684405230))
##print len(get_all_friends(2684405230))
##generate_word_cloud('cloga在路上',fans_tags=fans_tags)
##comment_list=get_comments(post_id)
##edges=get_edges(post_id)
##posts=get_posts(screen_name='M豆-红豆')
