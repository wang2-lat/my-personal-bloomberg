"""
Bloomberg V7.0 Pro - 专业级金融终端
=====================================
功能：
1. 市场概览晨报（SPY/QQQ/VIX）
2. 分析师评级 + 目标价
3. P/E 估值对比
4. AI 因果链分析
5. 历史参照
6. 风险量化
"""

import os
import datetime
import requests
import json
import re
import feedparser
import finnhub
import yfinance as yf
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
    "fred_key": os.getenv("FRED_KEY"),
    "alpha_key": os.getenv("ALPHA_VANTAGE_KEY"),
}

required = ["lark_id", "lark_secret", "chat_id", "finnhub_key", "gemini_key"]
missing = [k for k in required if not cfg.get(k)]
if missing:
    raise ValueError(f"❌ 缺少必需环境变量: {missing}")

fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

# 公司名 → Ticker 映射
COMPANY_MAP = {
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "alphabet": "GOOGL", "amazon": "AMZN", "meta": "META", "facebook": "META",
    "tesla": "TSLA", "netflix": "NFLX", "amd": "AMD", "intel": "INTC",
    "walmart": "WMT", "target": "TGT", "costco": "COST", "home depot": "HD",
    "jpmorgan": "JPM", "goldman": "GS", "morgan stanley": "MS",
    "bank of america": "BAC", "wells fargo": "WFC", "citigroup": "C",
    "boeing": "BA", "exxon": "XOM", "chevron": "CVX",
    "disney": "DIS", "nike": "NKE", "starbucks": "SBUX",
    "uber": "UBER", "airbnb": "ABNB", "doordash": "DASH",
    "coca-cola": "KO", "pepsi": "PEP", "mcdonald": "MCD",
    "pfizer": "PFE", "johnson": "JNJ", "unitedhealth": "UNH",
}

EXCLUDE_TICKERS = {
    'THE', 'AND', 'FOR', 'CEO', 'IPO', 'SEC', 'FDA', 'GDP', 'AI', 'US', 'UK',
    'DEI', 'ESG', 'ETF', 'NYSE', 'NASA', 'FBI', 'CIA', 'NFL', 'NBA', 'WHO',
}

# 行业平均 P/E（简化版）
SECTOR_PE = {
    "Technology": 30, "Financial Services": 15, "Healthcare": 22,
    "Consumer Cyclical": 20, "Communication Services": 18,
    "Consumer Defensive": 24, "Energy": 12, "Industrials": 18,
    "default": 20
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 飞书客户端
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LarkClient:
    def __init__(self):
        self._token = None
        self._expire = 0
    
    def get_token(self):
        now = datetime.datetime.now().timestamp()
        if self._token and now < self._expire - 60:
            return self._token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        res = requests.post(url, json={
            "app_id": cfg["lark_id"],
            "app_secret": cfg["lark_secret"]
        }, timeout=10)
        data = res.json()
        
        if data.get("code") == 0:
            self._token = data["tenant_access_token"]
            self._expire = now + data.get("expire", 7200)
            return self._token
        print(f"❌ Token 失败: {data}")
        return None
    
    def send_card(self, card):
        token = self.get_token()
        if not token:
            return False
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "receive_id": cfg["chat_id"],
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False)
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        result = resp.json()
        return result.get("code") == 0

lark = LarkClient()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 数据获取层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_ticker(text):
    """从新闻识别股票代码"""
    text_lower = text.lower()
    for company, ticker in COMPANY_MAP.items():
        if company in text_lower:
            return ticker
    
    matches = re.findall(r'\b([A-Z]{2,5})\b', text)
    for m in matches:
        if m not in EXCLUDE_TICKERS:
            return m
    return "SPY"


def get_stock_quote(ticker):
    """获取实时报价（Finnhub）"""
    try:
        q = fh_client.quote(ticker.upper())
        if q.get('c') and q.get('pc'):
            price = q['c']
            prev = q['pc']
            change = ((price - prev) / prev) * 100
            return {"price": price, "change": change, "prev": prev}
    except Exception as e:
        print(f"⚠️ Finnhub 报价失败 {ticker}: {e}")
    return None


def get_stock_fundamentals(ticker):
    """获取基本面数据（yfinance）"""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        return {
            "pe": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "sector": info.get('sector', 'Unknown'),
            "market_cap": info.get('marketCap'),
            "target_price": info.get('targetMeanPrice'),
            "target_high": info.get('targetHighPrice'),
            "target_low": info.get('targetLowPrice'),
            "recommendation": info.get('recommendationKey', 'none'),
            "week_52_high": info.get('fiftyTwoWeekHigh'),
            "week_52_low": info.get('fiftyTwoWeekLow'),
            "beta": info.get('beta'),
            "short_name": info.get('shortName', ticker),
        }
    except Exception as e:
        print(f"⚠️ yfinance 失败 {ticker}: {e}")
        return {}


def get_analyst_ratings(ticker):
    """获取分析师评级（Finnhub）"""
    try:
        trends = fh_client.recommendation_trends(ticker)
        if trends:
            latest = trends[0]
            total = latest.get('buy', 0) + latest.get('hold', 0) + latest.get('sell', 0) + \
                    latest.get('strongBuy', 0) + latest.get('strongSell', 0)
            
            buy_total = latest.get('buy', 0) + latest.get('strongBuy', 0)
            sell_total = latest.get('sell', 0) + latest.get('strongSell', 0)
            hold_total = latest.get('hold', 0)
            
            return {
                "buy": buy_total,
                "hold": hold_total,
                "sell": sell_total,
                "total": total,
                "consensus": "买入" if buy_total > hold_total + sell_total else \
                            "卖出" if sell_total > buy_total + hold_total else "持有"
            }
    except Exception as e:
        print(f"⚠️ 分析师评级失败 {ticker}: {e}")
    return None


def get_market_overview():
    """获取市场概览"""
    indices = [
        ("SPY", "S&P500"),
        ("QQQ", "纳指100"),
        ("DIA", "道指"),
    ]
    
    results = []
    for ticker, name in indices:
        quote = get_stock_quote(ticker)
        if quote:
            chg = quote['change']
            emoji = "🟢" if chg > 0 else "🔴" if chg < 0 else "⚪"
            results.append({
                "name": name,
                "ticker": ticker,
                "change": chg,
                "emoji": emoji,
                "price": quote['price']
            })
    
    return results


def get_vix():
    """获取 VIX 恐慌指数"""
    try:
        vix = yf.Ticker("^VIX")
        price = vix.info.get('regularMarketPrice') or vix.info.get('previousClose')
        if price:
            if price < 15:
                level = "低恐慌"
            elif price < 25:
                level = "正常"
            elif price < 35:
                level = "警惕"
            else:
                level = "高恐慌"
            return {"value": price, "level": level}
    except:
        pass
    return None


def get_philly_fed():
    """获取费城联储制造业指数"""
    if not cfg.get("fred_key"):
        return None
    
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
            return float(val)
    except:
        pass
    return None


def get_comprehensive_data(ticker):
    """获取股票的综合数据"""
    data = {
        "ticker": ticker.upper(),
        "quote": get_stock_quote(ticker),
        "fundamentals": get_stock_fundamentals(ticker),
        "analyst": get_analyst_ratings(ticker),
    }
    
    # 计算 52 周位置
    fund = data["fundamentals"]
    quote = data["quote"]
    if fund.get("week_52_high") and fund.get("week_52_low") and quote:
        high = fund["week_52_high"]
        low = fund["week_52_low"]
        price = quote["price"]
        if high > low:
            position = ((price - low) / (high - low)) * 100
            data["week_52_position"] = round(position, 1)
    
    # 计算 P/E 与行业对比
    if fund.get("pe") and fund.get("sector"):
        sector_avg = SECTOR_PE.get(fund["sector"], SECTOR_PE["default"])
        data["pe_vs_sector"] = {
            "stock_pe": fund["pe"],
            "sector_pe": sector_avg,
            "premium": round(((fund["pe"] - sector_avg) / sector_avg) * 100, 1)
        }
    
    # 计算目标价上涨空间
    if fund.get("target_price") and quote:
        upside = ((fund["target_price"] - quote["price"]) / quote["price"]) * 100
        data["upside"] = round(upside, 1)
    
    return data

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. AI 分析引擎
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze_with_ai(title, ticker, data):
    """AI 深度分析"""
    
    # 构建数据上下文
    ctx_parts = [f"股票: {ticker}"]
    
    if data.get("quote"):
        q = data["quote"]
        ctx_parts.append(f"价格: ${q['price']:.2f} ({q['change']:+.2f}%)")
    
    if data.get("fundamentals"):
        f = data["fundamentals"]
        if f.get("pe"):
            ctx_parts.append(f"P/E: {f['pe']:.1f}")
        if f.get("sector"):
            ctx_parts.append(f"行业: {f['sector']}")
    
    if data.get("pe_vs_sector"):
        pv = data["pe_vs_sector"]
        ctx_parts.append(f"估值溢价: {pv['premium']:+.1f}% vs 行业")
    
    if data.get("analyst"):
        a = data["analyst"]
        ctx_parts.append(f"分析师: {a['buy']}买/{a['hold']}持有/{a['sell']}卖出")
    
    if data.get("upside"):
        ctx_parts.append(f"目标价上涨空间: {data['upside']:+.1f}%")
    
    if data.get("week_52_position"):
        ctx_parts.append(f"52周位置: {data['week_52_position']:.0f}%")
    
    data_context = "\n".join(ctx_parts)
    
    prompt = f"""你是 Citadel 首席宏观策略师，同时拥有沃顿商学院金融学博士学位。
你的分析以"穿透本质、冷峻专业、逻辑严密"著称。

【新闻标题】
{title}

【量化数据】
{data_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请严格按以下格式输出（每项必填，中文回答）：

评分: [1-10的整数，1=极度利空，5=中性，10=极度利好]

核心判断: [一句话，说明利好/利空及影响程度，15-25字]

因果链: [用"A → B → C"格式，说明因果逻辑，25-40字]

估值视角: [结合P/E和目标价，判断是否已Price In，15-25字]

风险提示: [最大的不确定性是什么，15-20字]

操作建议: [对持有者和观望者的建议，15-25字]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

要求：
1. 必须有具体逻辑推理，不说空话套话
2. 每句话必须完整，不能截断
3. 结合量化数据进行分析
4. 如果数据不足，基于新闻内容合理推断
"""
    
    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = resp.text
        
        # 解析各字段
        result = {
            "score": 5,
            "core": "影响中性，需持续观察。",
            "logic": "信息有限 → 市场观望 → 短期波动有限",
            "valuation": "当前估值合理，无明显偏离。",
            "risk": "需关注后续发展。",
            "action": "观望为主，等待更多信息。"
        }
        
        # 评分
        m = re.search(r'评分:\s*(\d+)', text)
        if m:
            result["score"] = max(1, min(10, int(m.group(1))))
        
        # 核心判断
        m = re.search(r'核心判断:\s*(.+?)(?=\n|因果链|$)', text, re.DOTALL)
        if m:
            result["core"] = m.group(1).strip()[:40]
        
        # 因果链
        m = re.search(r'因果链:\s*(.+?)(?=\n|估值|$)', text, re.DOTALL)
        if m:
            result["logic"] = m.group(1).strip()[:60]
        
        # 估值视角
        m = re.search(r'估值视角:\s*(.+?)(?=\n|风险|$)', text, re.DOTALL)
        if m:
            result["valuation"] = m.group(1).strip()[:40]
        
        # 风险提示
        m = re.search(r'风险提示:\s*(.+?)(?=\n|操作|$)', text, re.DOTALL)
        if m:
            result["risk"] = m.group(1).strip()[:30]
        
        # 操作建议
        m = re.search(r'操作建议:\s*(.+?)(?=\n|$)', text, re.DOTALL)
        if m:
            result["action"] = m.group(1).strip()[:40]
        
        return result
        
    except Exception as e:
        print(f"⚠️ AI 分析失败: {e}")
        return {
            "score": 5,
            "core": "分析暂不可用。",
            "logic": "系统繁忙，请稍后再试。",
            "valuation": "数据不足。",
            "risk": "无法评估。",
            "action": "暂不操作。"
        }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 卡片构建
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_market_overview_card(market_data, vix, philly_fed):
    """构建市场概览卡片"""
    now = datetime.datetime.now(ZoneInfo("America/New_York"))
    
    # 市场指数行
    market_lines = []
    for m in market_data:
        market_lines.append(f"{m['emoji']} **{m['name']}** {m['change']:+.2f}%")
    market_str = " | ".join(market_lines)
    
    # VIX 行
    vix_str = ""
    if vix:
        vix_emoji = "🟢" if vix["value"] < 20 else "🟡" if vix["value"] < 30 else "🔴"
        vix_str = f"{vix_emoji} **VIX**: {vix['value']:.1f} ({vix['level']})"
    
    # 费城联储行
    philly_str = ""
    if philly_fed is not None:
        philly_emoji = "🟢" if philly_fed > 0 else "🔴"
        philly_str = f"{philly_emoji} **费城联储**: {philly_fed:.1f}"
    
    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📅 **{now.strftime('%Y-%m-%d %H:%M')} EST** | Philadelphia"
            }
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📈 {market_str}"
            }
        },
    ]
    
    if vix_str or philly_str:
        macro_parts = [x for x in [vix_str, philly_str] if x]
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "🌡️ " + " | ".join(macro_parts)
            }
        })
    
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": "Bloomberg V7.0 Pro | Citadel AI Engine"
        }]
    })
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "🏛 市场脉搏 | Market Pulse"},
            "template": "blue"
        },
        "elements": elements
    }


def build_news_card(title, data, analysis):
    """构建新闻分析卡片"""
    score = analysis["score"]
    ticker = data["ticker"]
    
    # 颜色和信号
    if score >= 7:
        theme, signal, emoji = "green", "利好", "🟢"
    elif score <= 4:
        theme, signal, emoji = "red", "利空", "🔴"
    else:
        theme, signal, emoji = "blue", "中性", "⚪"
    
    # 标题
    short_title = title[:26] + "..." if len(title) > 26 else title
    
    # 第一行：股票基本信息
    quote = data.get("quote", {})
    fund = data.get("fundamentals", {})
    
    price_str = f"${quote['price']:.2f}" if quote.get("price") else "--"
    change_str = f"{quote['change']:+.2f}%" if quote.get("change") else "--"
    
    # 第二行：估值信息
    pe_str = f"{fund.get('pe', 0):.1f}" if fund.get('pe') else "--"
    
    # 分析师信息
    analyst = data.get("analyst", {})
    if analyst:
        analyst_str = f"{analyst.get('consensus', '--')} ({analyst.get('buy', 0)}/{analyst.get('hold', 0)}/{analyst.get('sell', 0)})"
    else:
        analyst_str = "--"
    
    # 目标价
    if data.get("upside") is not None:
        target_str = f"{data['upside']:+.1f}%"
    else:
        target_str = "--"
    
    # 52周位置
    if data.get("week_52_position") is not None:
        week_str = f"{data['week_52_position']:.0f}%"
    else:
        week_str = "--"
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"{emoji} {short_title}"},
            "template": theme
        },
        "elements": [
            # 股票数据行
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{ticker}** | {price_str} ({change_str})"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"P/E: {pe_str} | 52周: {week_str}"
                        }
                    }
                ]
            },
            # 分析师行
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"📊 **分析师**: {analyst_str}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"🎯 **目标价空间**: {target_str}"
                        }
                    }
                ]
            },
            {"tag": "hr"},
            # 核心判断
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**🎯 核心判断**\n{analysis['core']}"
                }
            },
            # 因果链
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**🔗 因果链**\n{analysis['logic']}"
                }
            },
            # 估值视角
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**💰 估值视角**\n{analysis['valuation']}"
                }
            },
            {"tag": "hr"},
            # 风险与建议
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**⚠️ 风险**\n{analysis['risk']}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**💡 建议**\n{analysis['action']}"
                        }
                    }
                ]
            },
            # 底部
            {
                "tag": "note",
                "elements": [{
                    "tag": "plain_text",
                    "content": f"评分 {score}/10 | {signal} | WSJ | Citadel AI"
                }]
            }
        ]
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 主程序
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run():
    print("=" * 60)
    print("🚀 Bloomberg V7.0 Pro 启动")
    print("=" * 60)
    
    # ========== 1. 市场概览 ==========
    print("\n📈 获取市场数据...")
    market_data = get_market_overview()
    vix = get_vix()
    philly_fed = get_philly_fed()
    
    for m in market_data:
        print(f"   {m['emoji']} {m['name']}: {m['change']:+.2f}%")
    if vix:
        print(f"   🌡️ VIX: {vix['value']:.1f} ({vix['level']})")
    if philly_fed:
        print(f"   🏭 费城联储: {philly_fed:.1f}")
    
    # 发送市场概览卡片
    overview_card = build_market_overview_card(market_data, vix, philly_fed)
    if lark.send_card(overview_card):
        print("✅ 市场概览卡片已发送")
    else:
        print("❌ 市场概览卡片发送失败")
    
    # ========== 2. 新闻分析 ==========
    print("\n📰 抓取 WSJ 新闻...")
    feed = feedparser.parse("https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml")
    
    if not feed.entries:
        print("⚠️ 无新闻可用")
        return
    
    print(f"   找到 {len(feed.entries)} 条新闻")
    
    success_count = 0
    for i, entry in enumerate(feed.entries[:4]):
        title = entry.get('title', 'No Title')
        summary = entry.get('summary', '')
        
        print(f"\n{'─' * 50}")
        print(f"📄 [{i+1}/4] {title[:50]}...")
        
        # 识别 Ticker
        full_text = title + " " + summary
        ticker = extract_ticker(full_text)
        print(f"   🔍 标的: {ticker}")
        
        # 获取综合数据
        print(f"   📊 获取数据...")
        stock_data = get_comprehensive_data(ticker)
        
        if stock_data.get("quote"):
            q = stock_data["quote"]
            print(f"   💰 价格: ${q['price']:.2f} ({q['change']:+.2f}%)")
        
        if stock_data.get("fundamentals", {}).get("pe"):
            print(f"   📈 P/E: {stock_data['fundamentals']['pe']:.1f}")
        
        if stock_data.get("analyst"):
            a = stock_data["analyst"]
            print(f"   👥 分析师: {a['consensus']} ({a['buy']}/{a['hold']}/{a['sell']})")
        
        if stock_data.get("upside"):
            print(f"   🎯 目标价空间: {stock_data['upside']:+.1f}%")
        
        # AI 分析
        print(f"   🤖 AI 分析中...")
        analysis = analyze_with_ai(title, ticker, stock_data)
        print(f"   ✨ 评分: {analysis['score']}/10")
        print(f"   📝 判断: {analysis['core']}")
        
        # 构建并发送卡片
        card = build_news_card(title, stock_data, analysis)
        if lark.send_card(card):
            success_count += 1
            print(f"   ✅ 卡片已发送")
        else:
            print(f"   ❌ 卡片发送失败")
    
    # ========== 3. 完成 ==========
    print(f"\n{'=' * 60}")
    print(f"🏁 完成！成功发送 {success_count + 1}/5 条卡片")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run()
