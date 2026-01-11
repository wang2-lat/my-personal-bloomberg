import os
import datetime
import requests
import json
import re
import feedparser
import finnhub
from google import genai
from zoneinfo import ZoneInfo

# 配置
cfg = {
    "lark_id": os.getenv("LARK_APP_ID"),
    "lark_secret": os.getenv("LARK_APP_SECRET"),
    "chat_id": os.getenv("LARK_CHAT_ID"),
    "finnhub_key": os.getenv("FINNHUB_KEY"),
    "gemini_key": os.getenv("GEMINI_KEY"),
    "fred_key": os.getenv("FRED_KEY")
}

missing = [k for k, v in cfg.items() if not v and k != "fred_key"]
if missing:
    raise ValueError(f"缺少环境变量: {missing}")

fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

COMPANY_MAP = {
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "amazon": "AMZN", "meta": "META", "tesla": "TSLA", "netflix": "NFLX",
    "amd": "AMD", "intel": "INTC", "walmart": "WMT", "target": "TGT",
    "jpmorgan": "JPM", "goldman": "GS", "boeing": "BA", "disney": "DIS",
    "nike": "NKE", "starbucks": "SBUX", "uber": "UBER", "airbnb": "ABNB",
}

EXCLUDE = {'THE', 'AND', 'FOR', 'CEO', 'IPO', 'SEC', 'FDA', 'AI', 'US', 'UK', 'DEI', 'ESG'}


def get_lark_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    res = requests.post(url, json={"app_id": cfg["lark_id"], "app_secret": cfg["lark_secret"]}, timeout=10)
    data = res.json()
    if data.get("code") == 0:
        return data["tenant_access_token"]
    print(f"Token error: {data}")
    return None


def send_card(card):
    token = get_lark_token()
    if not token:
        return False
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"receive_id": cfg["chat_id"], "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)}
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    return resp.json().get("code") == 0


def extract_ticker(text):
    text_lower = text.lower()
    for company, ticker in COMPANY_MAP.items():
        if company in text_lower:
            return ticker
    matches = re.findall(r'\b([A-Z]{2,5})\b', text)
    for m in matches:
        if m not in EXCLUDE:
            return m
    return "SPY"


def get_stock_data(ticker):
    try:
        q = fh_client.quote(ticker.upper())
        if q.get('c') and q.get('pc'):
            price = q['c']
            change = ((price - q['pc']) / q['pc']) * 100
            return {"ticker": ticker.upper(), "price": price, "change": change}
    except:
        pass
    return None


def get_market_overview():
    results = []
    for t, n in [("SPY", "S&P500"), ("QQQ", "纳指")]:
        try:
            q = fh_client.quote(t)
            if q.get('c') and q.get('pc'):
                chg = ((q['c'] - q['pc']) / q['pc']) * 100
                e = "🟢" if chg > 0 else "🔴"
                results.append(f"{e} {n} {chg:+.2f}%")
        except:
            pass
    return " | ".join(results) if results else "数据加载中"


def analyze_news(title, ticker, stock_data):
    ctx = f"\n数据: {ticker} ${stock_data['price']:.2f} ({stock_data['change']:+.2f}%)" if stock_data else ""
    prompt = f"""分析新闻对市场影响。
新闻: {title}
标的: {ticker}{ctx}

输出格式:
分数: [1-10]
观点: [不超过18字的完整句子]"""
    
    try:
        resp = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = resp.text
        score = 5
        m = re.search(r'分数:\s*(\d+)', text)
        if m:
            score = max(1, min(10, int(m.group(1))))
        analysis = "影响待观察"
        m = re.search(r'观点:\s*(.+)', text)
        if m:
            analysis = m.group(1).strip()[:20]
        return score, analysis
    except:
        return 5, "分析暂不可用"


def build_header_card(market):
    now = datetime.datetime.now(ZoneInfo("America/New_York"))
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "🏛 Bloomberg V5.1"}, "template": "blue"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"📅 **{now.strftime('%Y-%m-%d %H:%M')}** | Philadelphia"}},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"📈 **大盘**: {market}"}}
        ]
    }


def build_news_card(title, ticker, stock_data, score, analysis):
    theme = "green" if score >= 7 else "red" if score <= 4 else "wathet"
    emoji = "🟢" if score >= 7 else "🔴" if score <= 4 else "⚪"
    short_title = title[:30] + "..." if len(title) > 30 else title
    
    if stock_data:
        price_str = f"${stock_data['price']:.2f}"
        change_str = f"{stock_data['change']:+.2f}%"
    else:
        price_str, change_str = "--", "--"
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"📰 {short_title}"}, "template": theme},
        "elements": [
            {"tag": "div", "fields": [
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**代码:** {ticker}\n**价格:** {price_str}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**涨跌:** {change_str}"}}
            ]},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**🎯 观点:** {analysis}"}},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": f"{emoji} 评分 {score}/10 | WSJ"}]}
        ]
    }


def run():
    print("🚀 Bloomberg V5.1 启动...")
    
    market = get_market_overview()
    print(f"📈 {market}")
    
    header = build_header_card(market)
    if send_card(header):
        print("✅ 头部卡片已发送")
    
    print("📰 抓取新闻...")
    feed = feedparser.parse("https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml")
    
    if not feed.entries:
        print("⚠️ 无新闻")
        return
    
    count = 0
    for i, entry in enumerate(feed.entries[:4]):
        title = entry.get('title', 'No Title')
        print(f"\n[{i+1}/4] {title[:40]}...")
        
        ticker = extract_ticker(title + " " + entry.get('summary', ''))
        print(f"   标的: {ticker}")
        
        stock_data = get_stock_data(ticker)
        if stock_data:
            print(f"   价格: ${stock_data['price']:.2f}")
        
        score, analysis = analyze_news(title, ticker, stock_data)
        print(f"   评分: {score}/10 | {analysis}")
        
        card = build_news_card(title, ticker, stock_data, score, analysis)
        if send_card(card):
            count += 1
            print("   ✅ 已发送")
        else:
            print("   ❌ 失败")
    
    print(f"\n🏁 完成！{count + 1}/5 条卡片")


if __name__ == "__main__":
    run()
