import json
import re
import traceback
from pathlib import Path
from typing import Optional

import yaml
from colorama import Fore
from flask import Flask, request

import cxsecret_font
from xuexiaoyi_API import XxyWxAPI

app = Flask(__name__)

with open("config.yaml", "r", encoding="utf8") as fp:
    CONFIG = yaml.load(fp, yaml.FullLoader)

ENABLE_CACHE = CONFIG["enable_cache"]


class CacheDAO:
    def __init__(self, file: str = "cache.json"):
        self.cacheFile = Path(file)
        if not self.cacheFile.is_file():
            self.cacheFile.open("w").write("{}")
        self.fp = self.cacheFile.open("r+", encoding="utf8")

    def getCache(self, question: str) -> Optional[str]:
        self.fp.seek(0)
        data = json.load(self.fp)
        if isinstance(data, dict):
            return data.get(question)

    def addCache(self, question: str, answer: str):
        self.fp.seek(0)
        data: dict = json.load(self.fp)
        data[question] = answer
        self.fp.seek(0)
        json.dump(data, self.fp, ensure_ascii=False, indent=4)


cache = CacheDAO()
xxy = XxyWxAPI(open_id=CONFIG["xxy_open_id"])


def searchXuexiaoyi(question: str) -> str:
    xxy.search(question)
    q_options, answer_plain_text = xxy.get()  # 选项, 正确答案
    # 处理答案是字母的情况
    if re.search(r"^[ ABCDEF]+$", answer_plain_text):
        answer_text = []
        for option in answer_plain_text:
            # 遍历并搜索选项
            temp1 = q_options.split(option)[1]
            # 切分选项以提取正确答案
            for alpha in "ABCDEF":
                if (len(temp2 := temp1.rsplit(f"{alpha} ")) > 1) | (alpha == "F"):
                    answer_text.append(temp2[0].strip("．.、 "))
                    break
        # 多选题情况 选项之间补 '#'
        if len(answer_text) >= 1:
            answer_text = "#".join(answer_text)
        # 单选题情况
        else:
            answer_text = answer_text[0]
    # 处理答案不是字母的情况
    else:
        answer_text = answer_plain_text

    # 处理和替换答案文本
    answer_text = (
        answer_text.replace("正确答案：", "")
        .replace("参考答案：", "")
        .replace("答案：", "")
        .replace("参考", "")
        .replace("</p>", "")
        .replace("<p>", "")
        .replace("&nbsp;", "")
        .replace("\n", "")
        .replace("\r", "")
        .strip(";；")
        .replace("√", "正确")
        .replace("×", "错误")
    )
    return answer_text


@app.route("/v1/cx", methods=("POST",))
def searchView():
    try:
        # 过滤请求问题
        question = (
            request.form.get("question")
            .replace("题型说明：请输入题型说明", "")
            .replace("【单选题】", "")
            .replace("【判断题】", "")
            .strip("\x0a\x09")
            .strip("")
        )

        # 题库缓存处理
        hit = False
        if ENABLE_CACHE:
            answer = cache.getCache(question)
            if answer is not None:
                hit = True
            else:
                answer = searchXuexiaoyi(question)  # 进行搜题
                cache.addCache(question, answer)
        else:
            answer = searchXuexiaoyi(question)  # 进行搜题

        print(f"{Fore.BLUE}题目: {question}{Fore.RESET}")
        print(
            f"{Fore.GREEN + '命中答案' if hit else Fore.YELLOW + '搜索答案'}: {answer}{Fore.RESET}"
        )

        return {
            "code": 1,
            "messsage": "",
            "data": answer,
            "hit": hit,
        }
    except Exception as err:
        traceback.print_exc()
        return {"code": -1, "messsage": err.__str__(), "data": "服务器酱被玩坏了耶！"}


@app.route("/decrypt", methods=("POST",))
def decryptView():
    args = json.loads(request.data)
    key_font_b64 = args["secFont"]
    dst_text = args["dstText"]
    font_hashmap = cxsecret_font.font2map(key_font_b64)  # 创建加密字体hash map
    src_text = cxsecret_font.decrypt(font_hashmap, dst_text)  # 解密目标文本
    print(
        f"{Fore.GREEN}解密成功{Fore.RESET}: {Fore.YELLOW}{dst_text}{Fore.RESET} -> {Fore.GREEN}{src_text}{Fore.RESET}"
    )
    return {"srcText": src_text}


if __name__ == '__main__':
    app.run(CONFIG["host"], CONFIG["port"])
