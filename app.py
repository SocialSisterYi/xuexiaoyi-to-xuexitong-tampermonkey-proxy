#!/bin/python3

import json
import re
import time
import traceback
import urllib.parse
from pathlib import Path
import difflib

import requests
from flask import Flask, request

from sec_font import secFont2Map, secFontDec, secFontEnc
from xuexiaoyi_pb2 import ReqOfSearch, RespOfSearch

app = Flask(__name__)

API_XUEXIAOYI_SEARCH = 'https://xxy.51xuexiaoyi.com/el/v0/sou/search'


class CacheDAO:
    def __init__(self, file='cache.json'):
        self.cacheFile = Path(file)
        if not self.cacheFile.is_file():
            self.cacheFile.open('w').write('{}')
        self.fp = self.cacheFile.open('r+', encoding='utf8')

    def getCache(self, question):
        self.fp.seek(0)
        data = json.load(self.fp)
        if isinstance(data, dict):
            return data.get(question)

    def addCache(self, question, answer):
        self.fp.seek(0)
        data: dict = json.load(self.fp)
        data.update({question: answer})
        self.fp.seek(0)
        json.dump(data, self.fp, ensure_ascii=False, indent=4)


cache = CacheDAO()

def fetchXuexiaoyi(question_text):
    headers = {
        'User-Agent': 'com.xuexiaoyi.xxy/10401 (Linux; U; Android 11; zh_CN; M2002J9E; Build/RKQ1.200826.002; Cronet/TTNetVersion:921ec9e4 2021-07-19 QuicVersion:6ad2ee95 2021-04-06)',
        'Content-Type': 'application/x-protobuf'
    }
    obj_req = ReqOfSearch(
        search_type=3,
        query=question_text,
        channel=1,
        trace_id=f'0-{int(time.time()*1000)}'
    )
    resp = requests.post(API_XUEXIAOYI_SEARCH, data=obj_req.SerializeToString(), headers=headers)
    resp.raise_for_status()
    assert resp.headers.get('Content-Type') == 'application/x-protobuf'
    obj_resp = RespOfSearch()
    obj_resp.ParseFromString(resp.content)
    return obj_resp.result.items

def searchXuexiaoyi(question):
    answer = fetchXuexiaoyi(question)[0]
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
    return (
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

def searchView():
    try:
        # 过滤请求问题
        if request.method == 'GET':
            question = request.args['question']
            fontHashMap = None
        elif request.method == 'POST':
            formData = dict(urllib.parse.parse_qsl(request.data.decode()))
            question = formData['question']
            if (targetAnswers := formData.get('answers')):
                targetAnswers = targetAnswers.split('#')[1:]
            else:
                targetAnswers = None
            if (secFontB64 := formData.get('secFont')):
                fontHashMap = secFont2Map(secFontB64) # 计算加密字体hashMap
                question = secFontDec(fontHashMap, question) # 解码加密字体
            else:
                fontHashMap = None
        question = (
            question
            .replace('题型说明：请输入题型说明','')
            .strip('\x0a\x09')
        )
        answer = cache.getCache(question)
        hit = True
        if answer is None:
            answer = searchXuexiaoyi(question)  # 进行搜题
            cache.addCache(question, answer)
            hit = False

        print(f'原始答案: {answer}')
        # 直接命中原目标答案
        if answer != '错误' and answer != '正确':
            if targetAnswers is not None:
                for originAnswer in targetAnswers:
                    if difflib.SequenceMatcher(
                        None,
                        secFontDec(fontHashMap, originAnswer) if (fontHashMap is not None) else originAnswer,
                        answer
                    ).quick_ratio() >= 0.95: # 比较答案相似度
                        answer = originAnswer
                        break
            # 编码答案文本 (可能不一一对应)
            else:
                answer = secFontEnc(fontHashMap, answer)

        return {
            "code": 1,
            "messsage": "",
            "data": answer,
            "hit": hit,
            "encryption": (fontHashMap is not None)
        }
    except Exception as err:
        traceback.print_exc()
        return {
            "code": -1,
            "messsage": err.__str__(),
            "data": "🙌没有人 👐比我 ☝️更懂 👌做题"
        }


app.add_url_rule('/hashTopic', 'search', searchView, methods=['GET', 'POST'])

app.run('0.0.0.0', 88)