import os
import datetime
import requests
import json
import re
import feedparser
import finnhub
from google import genai
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 配置初始化
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cfg = {
    "lark_id": os.getenv("LARK_APP_ID"),
    "lark_secret": os.getenv("LARK_APP_SECRET"),
    "chat_id": os.getenv("LARK_CHAT_ID"),
    "finnhub_key": os.getenv("FINNHUB_KEY"),
    "gemini_key": os.getenv("GEMINI_KEY"),
    "fred_key": os.getenv("FRED_KEY")
}

# 验证必要配置
missing = [k for k, v in cfg.items() if not v and k != "fred_key"]
if missing:
    raise ValueError(f"❌ 缺少环境变量: {missing}")

fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

# 公司名 → Ticker 映射表
COMPANY_TICKER_MAP = {
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "alphabet": "GOOGL", "amazon": "AMZN", "meta": "META", "facebook": "META",
    "tesla": "TSLA", "netflix": "NFLX", "amd": "AMD", "intel": "INTC",
    "broadcom": "AVGO", "salesforce": "CRM", "oracle": "ORCL", "ibm": "IBM",
    "walmart": "WMT", "costco": "COST", "jpmorgan": "JPM", "goldman": "GS",
    "boeing": "BA", "exxon": "XOM", "chevron": "CVX", "pfizer": "PFE",
    "disney": "DIS", "uber": "UBER", "airbnb": "ABNB", "openai": "MSFT",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 飞书卡片引擎
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LarkClient:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
        self._token_expire = 0

    def get_token(self):
        """获取 Token，带缓存"""
        now = datetime.datetime.now().timestamp()
        if self._token and now < self._token_expire - 60:
            return self._token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        try:
            res = requests.post(url, json={
                "app_id": self.app_id, 
                "app_secret": self.app_secret
            }, timeout=10)
            data = res.json()
            if data.get("code") == 0:
                self._token = data["tenant_access_token"]
                self._token_expire = now + data.get("expire", 7200)
                return self._token
            else:
                print(f"❌ Token 获取失败: {data}")
                return None
        except Exception as e:
            print(f"❌ Token 请求异常: {e}")
            return None

    def send_card(self, card_json):
        """发送卡片"""
        token = self.get_token()
        if not token:
            return False
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {token}", 
            "Content-Type": "application/json"
        }
        payload = {
            "receive_id": cfg["chat_id"], 
            "msg_type": "interactive", 
            "content": json.dumps(card_json, ensure_ascii=False)
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            result = resp.json()
            if result.get("code") == 0:
                return True
            else:
                print(f"❌ 卡片发送失败: {result}")
                return False
        except Exception as e:
            print(f"❌ 发送异常: {e}")
            return False

lark = LarkClient(cfg["lark_id"], cfg["lark_secret"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Ticker 识别（V4 核心逻辑）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_ticker(text):
    """从新闻文本识别股票代码"""
    text_lower = text.lower()
    
    # 方法1: 查表匹配公司名
    for company, ticker in COMPANY_TICKER_MAP.items():
        if company in text_lower:
            return ticker
    
    # 方法2: 正则匹配大写字母（可能是 Ticker）
    exclude = {'THE', 'AND', 'FOR', 'CEO', 'IPO', 'SEC', 'FDA', 'GDP', 'AI', 'US', 'UK', 'EU'}
    matches = re.findall(r'\b([A-Z]{2,5})\b', text)
    for m in matches:
        if m not in exclude:
            return m
    
    # 默认返回 SPY（大盘 ETF）
    return "SPY"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 量化数据获取
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_stock_data(ticker):
    """获取股票实时数据 + MA200"""
    try:
        ticker = ticker.upper().strip()
        
        # 实时报价
        q = fh_client.quote(ticker)
        if not q.get('c') or not q.get('pc'):
            return None
        
        price = q['c']
        change = ((price - q['pc']) / q['pc']) * 100
        
        # 计算 MA200
        ma_200 = calculate_ma200(ticker, price)
        
        return {
            "ticker": ticker,
            "price": price,
            "change": change,
            "ma_200": ma_200
        }
    except Exception as e:
        print(f"⚠️ 获取 {ticker} 数据失败: {e}")
        return None


def calculate_ma200(ticker, current_price):
    """计算 MA200 偏离度"""
    try:
        end = int(datetime.datetime.now().timestamp())
        start = end - 300 * 86400  # 300 天数据
        
        res = fh_client.stock_candles(ticker, 'D', start, end)
        
        if res.get('s') != 'ok':
            return None
        
        closes = res.get('c', [])
        if len(closes) < 200:
            return None
        
        ma200 = sum(closes[-200:]) / 200
        position = ((current_price - ma200) / ma200) * 100
        return round(position, 1)
    except:
        return None


def get_philly_fed():
    """获取费城联储制造业指数"""
    if not cfg.get("fred_key"):
        return "Philly Fed: 关注制造业动态"
    
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "GACDFSA066MSFRBPHI",
            "api_key": cfg["fred_key"],
            "file_type": "json",
            "limit": 1,
            "sort_order": "desc"
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.ok:
            val = resp.json().get('observations', [{}])[0].get('value', 'N/A')
            return f"Philly Fed Index: {val}"
    except:
        pass
    return "Philly Fed: Loading..."

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. AI 分析（真正解析评分）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze_with_ai(news_title, ticker, stock_data):
    """AI 分析新闻，返回 (评分, 观点)"""
    
    # 构建带数据的 prompt
    data_context = ""
    if stock_data:
        ma_str = f"{stock_data['ma_200']:+.1f}%" if stock_data['ma_200'] else "N/A"
        data_context = f"\n当前数据: {ticker} ${stock_data['price']:.2f} ({stock_data['change']:+.2f}%), MA200偏离: {ma_str}"
    
    prompt = f"""你是 Citadel 首席策略师。分析这条新闻。

新闻: {news_title}
相关标的: {ticker}{data_context}

严格按此格式输出（不要多余内容）:
分数: [1-10的数字，1=极度利空，10=极度利好]
观点: [不超过25字的穿透分析]
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        text = response.text.strip()
        
        # 解析评分
        score = 5  # 默认中性
        score_match = re.search(r'分数:\s*(\d+)', text)
        if score_match:
            score = int(score_match.group(1))
            score = max(1, min(10, score))  # 限制在 1-10
        
        # 解析观点
        analysis = "市场影响待观察"
        view_match = re.search(r'观点:\s*(.+)', text)
        if view_match:
            analysis = view_match.group(1).strip()[:30]
        
        return score, analysis
    except Exception as e:
        print(f"⚠️ AI 分析失败: {e}")
        return 5, "分析暂不可用"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 卡片构建
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_news_card(title, source, ticker, stock_data, score, analysis, philly_fed):
    """构建新闻卡片"""
    
    # 根据评分选颜色
    if score >= 7:
        theme = "green"
        emoji = "🟢"
    elif score <= 4:
        theme = "red"
        emoji = "🔴"
    else:
        theme = "grey"
        emoji = "⚪"
    
    # 标题截断
    short_title = title[:28] + "..." if len(title) > 28 else title
    
    # 股票数据显示
    if stock_data:
        price_str = f"${stock_data['price']:.2f}"
        change_str = f"{stock_data['change']:+.2f}%"
        ma_str = f"{stock_data['ma_200']:+.1f}%" if stock_data['ma_200'] else "N/A"
    else:
        price_str = "N/A"
        change_str = "N/A"
        ma_str = "N/A"
    
    now = datetime.datetime.now(ZoneInfo("America/New_York"))
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"🚨 {short_title}"},
            "template": theme
        },
        "elements": [
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**代码:** {ticker}\n**价格:** {price_str}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**涨跌:** {change_str}\n**MA200:** {ma_str}"
                        }
                    }
                ]
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**🎯 穿透观点:** {analysis}"
                }
            },
            {
                "tag": "note",
                "elements": [{
                    "tag": "plain_text",
                    "content": f"{emoji} 评分 {score}/10 | {source} | {now.strftime('%H:%M')} | 🏛 {philly_fed}"
                }]
            }
        ]
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 主程序
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_v5():
    print("🚀 Bloomberg V5.0 Production 启动...")
    
    # 获取费城联储数据
    philly_fed = get_philly_fed()
    print(f"🏛 {philly_fed}")
    
    # 抓取新闻
    print("📰 抓取 WSJ 新闻...")
    feed = feedparser.parse("https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml")
    
    if not feed.entries:
        print("⚠️ 无新闻可用")
        return
    
    # 处理前 4 条新闻
    success_count = 0
    for i, entry in enumerate(feed.entries[:4]):
        title = entry.get('title', 'No Title')
        print(f"\n📄 [{i+1}/4] {title[:40]}...")
        
        # 识别 Ticker
        ticker = extract_ticker(title + " " + entry.get('summary', ''))
        print(f"   🔍 识别标的: {ticker}")
        
        # 获取股票数据
        stock_data = get_stock_data(ticker)
        if stock_data:
            print(f"   📊 价格: ${stock_data['price']:.2f} ({stock_data['change']:+.2f}%)")
        
        # AI 分析
        score, analysis = analyze_with_ai(title, ticker, stock_data)
        print(f"   🤖 评分: {score}/10 | {analysis}")
        
        # 构建并发送卡片
        card = build_news_card(
            title=title,
            source="WSJ",
            ticker=ticker,
            stock_data=stock_data,
            score=score,
            analysis=analysis,
            philly_fed=philly_fed
        )
        
        if lark.send_card(card):
            success_count += 1
            print(f"   ✅ 已发送")
        else:
            print(f"   ❌ 发送失败")
    
    print(f"\n🏁 完成！成功发送 {success_count}/4 条卡片")


if __name__ == "__main__":
    run_v5()
