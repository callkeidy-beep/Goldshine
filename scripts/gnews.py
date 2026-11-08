"""구글뉴스 링크(news.google.com/rss/articles/...)를 언론사 원문 주소로 바꿉니다.

구글뉴스 RSS 링크는 원문으로 바로 넘어가지 않습니다. 기사 페이지에 든 서명과 시각을
구글뉴스 내부 주소(batchexecute)에 보내 원문 주소를 받아 옵니다. 실패하면 빈 문자열을 돌려줍니다.
구글이 방식을 바꾸면 이 파일만 고치면 됩니다.
"""
import json
import re
import urllib.parse

import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}


def _article_id(url: str) -> str:
    m = re.search(r"news\.google\.com/(?:rss/)?articles/([^?/#]+)", url)
    return m.group(1) if m else ""


def resolve(url: str, timeout: int = 10) -> str:
    aid = _article_id(url)
    if not aid:
        return ""
    try:
        page = requests.get(f"https://news.google.com/articles/{aid}", headers=UA, timeout=timeout).text
        sig = re.search(r'data-n-a-sg="([^"]+)"', page)
        ts = re.search(r'data-n-a-ts="([^"]+)"', page)
        if not (sig and ts):
            return ""
        inner = ('["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
                 '"X","X",1,[1,1,1],1,1,null,0,0,null,0],"%s",%s,"%s"]' % (aid, ts.group(1), sig.group(1)))
        req = json.dumps([[["Fbv4je", inner, None, "generic"]]])
        r = requests.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            headers={**UA, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
            data="f.req=" + urllib.parse.quote(req), timeout=timeout,
        )
        body = r.text.split("\n\n", 1)[1]
        outer = json.loads(body)[:-2]
        decoded = json.loads(outer[0][2])[1]
        return decoded if isinstance(decoded, str) and decoded.startswith("http") else ""
    except Exception:
        return ""
