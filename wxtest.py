# -*- coding = utf-8 -*-

import itchat, requests
import re
import time
import os
import threading
from itchat.content import *

tmp_dict = {}
tmp_dir = r"C:\Users\JOph\Documents\wxpy\\"
msg_type =[ ['Text', 'Friends'], ['Picture','Recording', 'Attachment', 'Video'], ["card"], ['Map'], ["Sharing"]]
if not os.path.exists(tmp_dir): os.mkdir(tmp_dir)
face_bug = None

#auto_reply_switch
SWITCH_REPLY = True
SWITCH_DELAY = True
DELAY_TIME = 120
SWITCH_PREFIX = True
PREFIX_CONTENT = "[ART] "
REPLY_DICT = {}
DELAY_REPLY_DICT = {}
REPLY_ALIVE = True


def check():
    while REPLY_ALIVE:
        #time.sleep(120)
        time.sleep(30)
        print('checking...')
        to_del = []
        #global DELAY_REPLY_DICT
        if len(DELAY_REPLY_DICT) > 0:
            for i in DELAY_REPLY_DICT:
                if DELAY_REPLY_DICT[i][1] and int(time.time() - DELAY_REPLY_DICT[i][0]) > 120:
                    itchat.send(r"[ART] 对方不在手机旁，留言已收到。", toUserName=itchat.search_friends(nickName=i)[0]['UserName'])
                    print('replied %s' %i)
                    to_del.append(i)
        if len(to_del) != 0:
            for j in to_del:
                DELAY_REPLY_DICT.pop(j)
    print('stopped.\n')


def print_content(msg):
    print(msg['Text'])
    return msg.text + '!'



def simple_reply(msg):
    if msg['Type'] == itchat.content.TEXT:
        req = msg['Content']
        return 'I receiverd: %s' %msg['Content']


@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO])
def handle_received_msg(msg):
    myUserName = (itchat.search_friends())['UserName']
    if msg['FromUserName'] == myUserName and msg['ToUserName'] in DELAY_REPLY_DICT:
        DELAY_REPLY_DICT.pop(msg['ToUserName'])
    if msg['ToUserName'] == 'filehelper' and msg.text == '/STOP':
        global REPLY_ALIVE
        REPLY_ALIVE = False
        print('exiting!')
    clear_dict()
    global face_bug
    #msg_type =[ ['Text', 'Friends'], ['Picture','Recording', 'Attachment', 'Video'], ["card"], ['Map'], ["Sharing"]]
    #msg receive time
    msg_revtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    #msg id
    msg_id = msg['MsgId']
    #msg create time
    msg_creatime = msg['CreateTime']
    msg_from = (itchat.search_friends(userName=msg['FromUserName']))['NickName']
    msg_content = None
    msg_share_url = None

    if msg["Type"] in msg_type[0]:
        msg_content = msg['Text']
    elif msg['Type'] in msg_type[1]:
        msg_content = r"" + msg['FileName']
        msg['Text'](tmp_dir + msg['FileName'])
    elif msg['Type'] in msg_type[2]:
        msg_content = msg['RecommendInfo']['NickName'] + r"的名片"
    elif msg['Type'] in msg_type[3]:
        x,y,location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*", msg['DriContent']).group(1,2,3)
        if location is None:
            msg_content = r"纬度:" + x.__str__() + "经度:" + y.__str__()
        else:
            msg_content = r"" + location
    elif msg['Type'] in msg_type[4]:
        msg_content = msg["Text"]
        msg_share_url = msg["Url"]
    face_bug = msg_content

    tmp_dict.update(
        {
            msg_id: {
                "msg_from": msg_from, "msg_creatime": msg_creatime, "msg_revtime": msg_revtime ,
                "msg_type": msg['Type'], "msg_content": msg_content, "msg_share_url": msg_share_url
            }
        }
    )

    if msg['FromUserName'] != myUserName and msg_from not in REPLY_DICT:
        REPLY_DICT[msg_from] = "微信不在线上，有事请打电话或发短信。"
    if msg['FromUserName'] != myUserName and msg['FromUserName'] != 'filehelper':
        DELAY_REPLY_DICT[msg_from] = [msg_creatime, SWITCH_REPLY]
        #auto_reply(DELAY_REPLY_DICT,msg['FromUserName'])
    if len(DELAY_REPLY_DICT) != 0:
        print(REPLY_ALIVE, DELAY_REPLY_DICT.keys())




def clear_dict():
    curtime = time.time()
    todellist = []
    if len(tmp_dict) > 0:
        for i in tmp_dict:
            if curtime - tmp_dict[i].get("msg_creatime") > 121:
                todellist.append(i)
    for j in todellist:
        try:
            tmp_dict.pop(j)
        finally:
            pass


def auto_reply(reply_dict, msg_from):
    if len(reply_dict) > 0:
        for i in reply_dict:
            if reply_dict[i][1] and time.time() > reply_dict[i][0]:
                itchat.send(r"[ART] 对方不在手机旁，留言已收到。", toUserName=msg_from)
                reply_dict.pop(i)




def test_reply2(msg):
    target_friend = itchat.search_friends(userName = msg["FromUserName"])
    if target_friend:
        nickName = target_friend['NickName']
        if nickName not in REPLY_DICT:
            REPLY_DICT[nickName] = "微信不在线上，有事请打电话或发短信。"
        reply_content = REPLY_DICT[nickName]
        if SWITCH_REPLY:
            if SWITCH_DELAY:
                time.sleep(121)

            else:
                if SWITCH_PREFIX:
                    reply_content = PREFIX_CONTENT + REPLY_DICT[nickName]
                else:
                    reply_content = REPLY_DICT[nickName]
                itchat.send(reply_content, toUserName=msg['FromUserName'])



def test_reply_delay(msg):
    if msg['FromUserName'] == (itchat.search_friends())['UserName']:
        itchat.send(msg['Content'], toUserName="filehelper")


@itchat.msg_register([NOTE])
def send_msg_helper(msg):
    global  face_bug
    if re.search(r"\<\!\[CDATA\[.*撤回了一条消息\]\]\>", msg['Content']) is not None:
        old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg["Content"]).group(1)
        old_msg = tmp_dict.get(old_msg_id, {})
        if len(old_msg_id) < 11:
            itchat.send_file(tmp_dir + face_bug, toUserName = 'filehelper')
            os.remove(tmp_dir + face_bug)
        else:
            msg_body = old_msg.get("msg_from") + "撤回了一条" + old_msg.get("msg_type") + "消息:" + '\n' \
                       + r"" + old_msg.get("msg_content")
            if old_msg["msg_type"] in msg_type[4]:
                msg_body = "\n撤回链接:" + old_msg.get('msg_share_url')

            if old_msg["msg_type"] in msg_type[0]:
                itchat.send(msg_body, toUserName='filehelper')

            if old_msg["msg_type"] in msg_type[1]:
                file = '@fil@%s' %(tmp_dir + old_msg["msg_content"])
                itchat.send(msg=file, toUserName='filehelper')
                #os.remove(tmp_dir + old_msg["msg_content"])

            tmp_dict.pop(old_msg_id)


def get_weather(city = 'suzhou'):
    pass

def pinyin(word):
    pass

#@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO])
def file_helper(msg):
    if msg['ToUserName'] == 'filehelper' and msg['FromUserName'] == (itchat.search_friends())['UserName']:
        message = msg.text
        print(message)
        return message



# itchat.auto_login(enableCmdQR=True)
itchat.auto_login()
itchat.dump_login_status()
#itchat.run()
threading.Thread(target = itchat.run).start()
threading.Thread(target = check).start()
