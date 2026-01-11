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
# 配置层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_config():
    cfg = {
        "lark_id": os.getenv("LARK_APP_ID"),
        "lark_secret": os.getenv("LARK_APP_SECRET"),
        "lark_chat_id": os.getenv("LARK_CHAT_ID"),  # 飞书群 chat_id
        "finnhub_key": os.getenv("FINNHUB_KEY"),
        "gemini_key": os.getenv("GEMINI_KEY"),
        "fred_key": os.getenv("FRED_KEY")
    }
    missing = [k for k, v in cfg.items() if not v and k != "fred_key"]
    if missing:
        raise ValueError(f"缺少环境变量: {missing}")
    return cfg

cfg = get_config()
fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

# 公司名 → Ticker 映射
COMPANY_TICKER_MAP = {
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "alphabet": "GOOGL", "amazon": "AMZN", "meta": "META", "tesla": "TSLA",
    "netflix": "NFLX", "amd": "AMD", "intel": "INTC", "broadcom": "AVGO",
    "salesforce": "CRM", "oracle": "ORCL", "walmart": "WMT", "costco": "COST",
    "jpmorgan": "JPM", "goldman": "GS", "morgan stanley": "MS",
    "boeing": "BA", "exxon": "XOM", "chevron": "CVX", "pfizer": "PFE",
    "disney": "DIS", "uber": "UBER", "airbnb": "ABNB", "openai": "MSFT",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 飞书 API 层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LarkClient:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
        self._token_expire = 0
    
    def get_token(self):
        """获取 tenant_access_token，带缓存"""
        now = datetime.datetime.now().timestamp()
        if self._token and now < self._token_expire - 60:
            return self._token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        try:
            resp = requests.post(url, json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }, timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                self._token = data["tenant_access_token"]
                self._token_expire = now + data.get("expire", 7200)
                return self._token
            else:
                raise Exception(f"飞书认证失败: {data}")
        except Exception as e:
            print(f"获取飞书 Token 失败: {e}")
            return None
    
    def send_card(self, chat_id, card_json):
        """发送交互式卡片"""
        token = self.get_token()
        if not token:
            print("无法发送卡片：Token 获取失败")
            return False
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card_json, ensure_ascii=False)
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            result = resp.json()
            if result.get("code") == 0:
                return True
            else:
                print(f"飞书发送失败: {result}")
                return False
        except Exception as e:
            print(f"飞书请求异常: {e}")
            return False

lark_client = LarkClient(cfg["lark_id"], cfg["lark_secret"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据抓取层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_stock_data(ticker):
    """获取个股数据"""
    try:
        ticker = ticker.upper().strip()
        if not re.match(r'^[A-Z]{1,5}$', ticker):
            return None
        
        q = fh_client.quote(ticker)
        if not (q.get('c') and q.get('pc')):
            return None
        
        price = q['c']
        change = ((price - q['pc']) / q['pc']) * 100
        
        # 计算 200 日均线位置
        ma_200 = calculate_ma_position(ticker, price, 200)
        
        # 52 周位置
        w52 = get_52_week_position(ticker, price)
        
        return {
            "ticker": ticker,
            "price": price,
            "change": change,
            "ma_200": ma_200,
            "week_52": w52
        }
    except:
        return None


def calculate_ma_position(ticker, current_price, days):
    """计算相对均线位置"""
    try:
        end = int(datetime.datetime.now().timestamp())
        start = end - (days + 30) * 86400
        candles = fh_client.stock_candles(ticker, 'D', start, end)
        if candles.get('s') != 'ok' or len(candles.get('c', [])) < days:
            return None
        closes = candles['c'][-days:]
        ma = sum(closes) / len(closes)
        return round(((current_price - ma) / ma) * 100, 1)
    except:
        return None


def get_52_week_position(ticker, current_price):
    """52周位置百分比"""
    try:
        end = int(datetime.datetime.now().timestamp())
        start = end - 365 * 86400
        candles = fh_client.stock_candles(ticker, 'D', start, end)
        if candles.get('s') != 'ok':
            return None
        high = max(candles.get('h', [current_price]))
        low = min(candles.get('l', [current_price]))
        if high == low:
            return 50
        return round(((current_price - low) / (high - low)) * 100, 1)
    except:
        return None


def get_market_indices():
    """获取大盘指数"""
    indices = [
        ("SPY", "S&P500"),
        ("QQQ", "纳指100"),
        ("VXX", "VIX恐慌"),
    ]
    results = []
    for ticker, name in indices:
        try:
            q = fh_client.quote(ticker)
            if q.get('c') and q.get('pc'):
                chg = ((q['c'] - q['pc']) / q['pc']) * 100
                emoji = "🟢" if chg > 0 else "🔴"
                results.append(f"{emoji}{name} {chg:+.1f}%")
        except:
            continue
    return " | ".join(results) if results else "数据暂不可用"


def get_philly_fed():
    """获取费城联储制造业指数"""
    if not cfg.get("fred_key"):
        return "费城联储: 关注制造业PMI"
    
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "GACDFSA066MSFRBPHI",  # 费城联储制造业指数
            "api_key": cfg["fred_key"],
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.ok:
            obs = resp.json().get("observations", [{}])[0]
            value = obs.get("value", "N/A")
            date = obs.get("date", "")
            return f"费城联储指数: {value} ({date})"
    except:
        pass
    return "费城联储: 数据获取中"


def fetch_news():
    """抓取新闻"""
    sources = {
        "WSJ": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        "NYT": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    }
    pool = []
    for name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                pool.append({
                    "title": entry.get("title", "")[:100],
                    "summary": entry.get("summary", "")[:300],
                    "source": name
                })
        except:
            continue
    return pool[:6]


def extract_ticker(text):
    """从文本识别 Ticker"""
    text_lower = text.lower()
    for company, ticker in COMPANY_TICKER_MAP.items():
        if company in text_lower:
            return ticker
    # 正则匹配
    match = re.search(r'\b([A-Z]{2,4})\b', text)
    if match:
        candidate = match.group(1)
        if candidate not in {'THE', 'AND', 'FOR', 'CEO', 'IPO', 'SEC', 'FDA', 'GDP', 'AI'}:
            return candidate
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI 分析层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze_news(news, stock_data):
    """AI 生成极简分析"""
    stock_context = ""
    if stock_data:
        stock_context = f"""
相关股票数据：
- 代码: {stock_data['ticker']}
- 价格: ${stock_data['price']:.2f}
- 涨跌: {stock_data['change']:+.2f}%
- MA200位置: {stock_data['ma_200']}%
- 52周位置: {stock_data['week_52']}%
"""
    
    prompt = f"""
你是 Citadel 首席策略师。用一句话（不超过35字）穿透这条新闻的本质。
同时给出情绪分（1-10，1=极度利空，10=极度利好）。

新闻标题：{news['title']}
新闻摘要：{news['summary']}
{stock_context}

输出格式（严格遵守）：
分数: [数字]
观点: [一句话]
"""
    
    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = resp.text.strip()
        
        # 解析
        score = 5
        analysis = "暂无分析"
        
        score_match = re.search(r'分数:\s*(\d+)', text)
        if score_match:
            score = int(score_match.group(1))
            score = max(1, min(10, score))
        
        view_match = re.search(r'观点:\s*(.+)', text)
        if view_match:
            analysis = view_match.group(1).strip()[:40]
        
        return score, analysis
    except Exception as e:
        print(f"AI 分析失败: {e}")
        return 5, "分析暂不可用"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 飞书卡片构建
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_header_card(market_data, philly_fed):
    """构建市场概览卡片"""
    philly_time = datetime.datetime.now(ZoneInfo("America/New_York"))
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "🏛 王同学的决策终端 V5.0"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📅 **{philly_time.strftime('%Y-%m-%d %H:%M')}** | Philadelphia"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📈 **市场脉搏**: {market_data}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"🏭 **{philly_fed}**"
                }
            }
        ]
    }


def build_news_card(title, source, score, analysis, stock_data):
    """构建单条新闻卡片"""
    # 颜色主题
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
    short_title = title[:25] + "..." if len(title) > 25 else title
    
    elements = []
    
    # 如果有股票数据，显示分栏
    if stock_data:
        ma_str = f"{stock_data['ma_200']:+.1f}%" if stock_data['ma_200'] else "N/A"
        w52_str = f"{stock_data['week_52']:.0f}%" if stock_data['week_52'] else "N/A"
        
        elements.append({
            "tag": "column_set",
            "flex_mode": "bisect",
            "background_style": "default",
            "columns": [
                {
                    "tag": "column",
                    "width": "weighted",
                    "weight": 1,
                    "elements": [{
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{stock_data['ticker']}** ${stock_data['price']:.2f}\n涨跌 {stock_data['change']:+.2f}%"
                        }
                    }]
                },
                {
                    "tag": "column",
                    "width": "weighted",
                    "weight": 1,
                    "elements": [{
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"MA200: {ma_str}\n52周: {w52_str}"
                        }
                    }]
                }
            ]
        })
        elements.append({"tag": "hr"})
    
    # 分析观点
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**🎯 穿透观点**: {analysis}"
        }
    })
    
    # 底部标注
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": f"{emoji} 情绪分 {score}/10 | 来源: {source}"
        }]
    })
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": short_title},
            "template": theme
        },
        "elements": elements
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主程序
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_v5():
    print("🚀 Bloomberg V5.0 飞书版启动...")
    
    # 1. 获取市场数据
    print("📈 抓取市场指数...")
    market_data = get_market_indices()
    philly_fed = get_philly_fed()
    
    # 2. 发送头部卡片
    header_card = build_header_card(market_data, philly_fed)
    lark_client.send_card(cfg["lark_chat_id"], header_card)
    
    # 3. 抓取新闻
    print("📰 抓取新闻...")
    news_list = fetch_news()
    if not news_list:
        print("⚠️ 无新闻")
        return
    
    # 4. 逐条处理
    for i, news in enumerate(news_list):
        print(f"   处理 [{i+1}/{len(news_list)}]: {news['title'][:30]}...")
        
        # 识别 Ticker
        ticker = extract_ticker(news['title'] + " " + news['summary'])
        
        # 获取股票数据
        stock_data = None
        if ticker:
            stock_data = get_stock_data(ticker)
        
        # AI 分析
        score, analysis = analyze_news(news, stock_data)
        
        # 构建并发送卡片
        card = build_news_card(
            title=news['title'],
            source=news['source'],
            score=score,
            analysis=analysis,
            stock_data=stock_data
        )
        lark_client.send_card(cfg["lark_chat_id"], card)
    
    print("✅ V5.0 报告已发送至飞书")


if __name__ == "__main__":
    run_v5()
```

---

## 📋 V5.0 对比 Gemini 原版

| 问题 | Gemini 原版 | 修复版 |
|:-----|:-----------|:-------|
| 数据源 | Mock 假数据 | 完整接入 RSS + Finnhub |
| Token 管理 | 无缓存，每次重新获取 | 带过期缓存 |
| 错误处理 | 几乎没有 | 全链路 try-except |
| 费城联储 | 只写了字符串 | 真实调用 FRED API |
| 分栏排版 | 用 fields | 用 column_set（更稳定） |
| AI 分析 | 没有 | 完整 Gemini 调用 + 解析 |
| 批量发送 | 没设计 | 头部卡片 + 逐条新闻卡片 |

---

## 🔧 部署 Checklist

### 新增 GitHub Secrets:
```
LARK_APP_ID=cli_xxxxx
LARK_APP_SECRET=xxxxx
LARK_CHAT_ID=oc_xxxxx   # 飞书群的 chat_id
FRED_KEY=xxxxx          # 可选
