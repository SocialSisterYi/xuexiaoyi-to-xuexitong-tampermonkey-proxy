import base64
import hashlib
import re
import sqlite3
import struct
from io import BytesIO
from pathlib import Path
from typing import IO, Dict, Union

from colorama import Back, Fore, Style
from fontTools.ttLib.ttFont import TTFont


class FontHashDAO:
    def __init__(self, file='font_hashmap.db'):
        self.conn = sqlite3.connect(file)

    def findChar(self, fontHash: str) -> str:
        cur = self.conn.execute("SELECT cn_char FROM hashmap WHERE hash=(?)", (fontHash,))
        if resp := cur.fetchone():
            return resp[0]
    
    def findHash(self, char: str) -> str:
        cur = self.conn.execute("SELECT hash FROM hashmap WHERE cn_char=(?)", (char,))
        if resp := cur.fetchone():
            return resp[0]

def secFont2Map(file: Union[IO, Path, str]) -> Dict[str, str]:
    '以加密字体计算hashMap'
    fontHashMap = {}
    if isinstance(file, str):
        file = BytesIO(base64.b64decode(file[47:]))
    with TTFont(file) as fontFile:
        glyphs = fontFile.getGlyphSet()
        for code, font in dict(glyphs).items():
            if not code.startswith('uni'):
                continue
            fontHash = hashlib.sha256()
            for pos in font._glyph.coordinates:
                fontHash.update(struct.pack('>2i', *pos))
            fontHashMap[code] = fontHash.hexdigest()
    return fontHashMap

def secFontDec(hashMap, source) -> str:
    '解码字体加密'
    dao = FontHashDAO()
    resultStr = ''
    for char in source:
        unicodeID = f'uni{ord(char):X}'
        if (fontHash := hashMap.get(unicodeID)):
            originChar = dao.findChar(fontHash)
            if originChar is not None:
                resultStr += originChar
            else:
                print(Fore.RED+f'解码失败: {char}({fontHash})'+Fore.RESET)
        else:
            resultStr += char
    print(Fore.GREEN+f'字体加密解码: {source} -> {resultStr}'+Fore.RESET)
    return resultStr
    

def secFontEnc(hashMap, source) -> str:
    '编码字体加密'
    dao = FontHashDAO()
    hashMap = dict(zip(hashMap.values(), hashMap.keys()))
    resultStr = ''
    for char in source:
        if (fontHash := dao.findHash(char)):
            if (unicodeID := hashMap.get(fontHash)):
                if (result := re.match(r'^uni([0-9A-Z]{4})$', unicodeID)):
                    encChar = chr(int(result.group(1), 16))
                    resultStr += encChar
            else:
                resultStr += char
        else:
            resultStr += char
    print(Fore.GREEN+f'字体加密编码: {source} -> {resultStr}'+Fore.RESET)
    return resultStr

if __name__ == "__main__":
    import rich
    fontHashMap=secFont2Map(Path('../../../Desktop/Source Han Sans CN Normal.pfb.ttf'))
    rich.print(fontHashMap)
