#!/bin/python3

import requests
import time
from xuexiaoyi_pb2 import ReqOfSearch, RespOfSearch
import re
from flask import Flask, request
app = Flask(__name__)

def search_question(question_text):
    url = 'https://xxy.51xuexiaoyi.com/el/v0/sou/search'
    headers = {
        'User-Agent': 'com.xuexiaoyi.xxy/10401 (Linux; U; Android 11; zh_CN; M2002J9E; Build/RKQ1.200826.002; Cronet/TTNetVersion:921ec9e4 2021-07-19 QuicVersion:6ad2ee95 2021-04-06)',
        'Content-Type': 'application/x-protobuf'
    }
    obj_req=ReqOfSearch(
        search_type=3,
        query=question_text,
        channel=1,
        trace_id=f'0-{int(time.time()*1000)}'
    )
    resp = requests.post(url,data=obj_req.SerializeToString(),headers=headers)
    resp.raise_for_status()
    assert resp.headers.get('Content-Type') == 'application/x-protobuf'
    obj_resp = RespOfSearch()
    obj_resp.ParseFromString(resp.content)
    return obj_resp.result.items

@app.route('/hashTopic', methods=['GET'])
def search():
    try:
        # 过滤请求问题
        question = (
            request.args['question']
            .replace('题型说明：请输入题型说明','')
            .strip('\x0a\x09')
        )
        # 进行搜题
        answer = search_question(question)[0]
        answer_plain_text = answer.question_answer.answer_plain_text # 正确答案
        q_title = answer.question_answer.q_title                     # 题目
        q_options = answer.question_answer.q_options                 # 选项
        # 处理答案是字母的情况
        if re.search(r'^[ ABCDEF]+$', answer_plain_text):
            answer_text = []
            for option in answer_plain_text:
                # 遍历并搜索选项
                temp1 = q_options.split(option)[1]
                # 切分选项以提取正确答案
                for alpha in 'ABCDEF':
                    if (len(temp2 := temp1.rsplit(f'{alpha} ')) > 1) | (alpha == 'F'):
                        answer_text.append(temp2[0].strip('．.、 '))
                        break
            # 多选题情况 选项之间补 '#'
            if len(answer_text) >= 1:
                answer_text = '#'.join(answer_text)
            # 单选题情况
            else:
                answer_text = answer_text[0]
        # 处理答案不是字母的情况
        else:
            answer_text = answer_plain_text
        
        # 处理和替换答案文本
        answer_text = (
            answer_text
            .replace('答案：', '')
            .replace('参考答案：', '')
            .replace('正确答案：', '')
            .replace('×', '错误')
            .replace('√', '正确')
            .replace('</p>', '')
            .replace('<p>', '')
            .replace('参考', '')
            .strip()
        )
    except Exception as err:
        return {
            "code": -1,
            "messsage": err.__str__(),
            "data": "🙌没有人 👐比我 ☝️更懂 👌做题"
        }
    else:
        return {
            "code": 1,
            "messsage": "",
            "data": answer_text,
            "debug": {
                "question_text": q_title,
                "answers_text": q_options,
                "answer": answer_plain_text
            }
        }

app.run('0.0.0.0',88)
