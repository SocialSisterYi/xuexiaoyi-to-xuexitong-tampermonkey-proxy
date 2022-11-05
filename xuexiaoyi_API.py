from typing import List

import requests

WXAPI_SEARCH = "https://xxy.51xuexiaoyi.com/el/wx/sou/search"
WXAPI_TOKEN = "https://xxy.51xuexiaoyi.com/el/wx/app/code2session"
WXAPI_UA = "Mozilla/5.0 (Linux; Android 12; M2102K1C Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4317 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/6294 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/5G Language/zh_CN ABI/arm64 MiniProgramEnv/android"


class APIError(Exception):
    def __init__(self, code, msg) -> None:
        self.code = code
        self.msg = msg
        super().__init__()

    def __str__(self) -> str:
        return f"{self.code}:{self.msg}"


class XxyWxAPI:
    """学小易-微信小程序API调用"""
    session: requests.Session
    items: List[dict]
    open_id: str

    def __init__(self, open_id: str = "") -> None:
        self.session = requests.Session()
        self.open_id = open_id
        self.session.headers.update(
            {
                "User-Agent": WXAPI_UA,
                "Referer": "https://servicewechat.com/wx7436885f6e1ba040/6/page-frame.html",
            }
        )

    def code2session(self, code: str) -> bool:
        """获取/刷新session"""
        resp = self.session.get(
            WXAPI_TOKEN,
            params={"mp_id": 1, "js_code": code},
            headers={"wx-open-id": self.open_id, "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        resp_json = resp.json()
        code = resp_json["err_no"]
        if code != 0:
            raise APIError(code, resp_json["err_tips"])
        if d := resp_json.get("data"):
            self.open_id = d["open_id"]
            return True
        return False

    def search(self, question: str) -> bool:
        """搜题"""
        resp = self.session.post(
            WXAPI_SEARCH,
            headers={"wx-open-id": self.open_id},
            json={"query": question, "channel": 1},
        )
        resp.raise_for_status()
        resp_json = resp.json()
        code = resp_json["err_no"]
        if code != 0:
            raise APIError(code, resp_json["err_tips"])
        self.items = resp_json["data"]["result"]["items"]
        return len(self.items) >= 1

    def get(self, index: int = 0) -> tuple[str, str]:
        """获取搜题结果"""
        question_info = self.items[index]
        return (
            question_info["question_answer"]["question_plain_text"],
            question_info["question_answer"]["answer_plain_text"],
        )


if __name__ == "__main__":
    patten = "国防是阶级斗争的产物,它伴随着()的形成而产生。"
    xxy = XxyWxAPI("oKtmq5YGlp26rm6eL-aRKew1ZRHs")
    xxy.search(patten)
    q, a = xxy.get(0)
    print("题 --- ", q)
    print("答 --- ", a)
