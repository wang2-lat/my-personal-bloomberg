import os
import datetime
import requests
import feedparser
import finnhub
import re
from google import genai
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 配置层 (Secrets 加载)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_config():
    cfg = {
        "tg_token": os.getenv("TELEGRAM_TOKEN"),
        "chat_id": os.getenv("CHAT_ID"),
        "finnhub_key": os.getenv("FINNHUB_KEY"),
        "gemini_key": os.getenv("GEMINI_KEY"),
        "fred_key": os.getenv("FRED_KEY") 
    }
    return cfg

cfg = get_config()
fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

# 高频 Ticker 映射表
COMPANY_TICKER_MAP = {
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "amazon": "AMZN", "meta": "META", "tesla": "TSLA", "amd": "AMD"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 数据抓取引擎 (Market & Stock)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_market_pulse():
    """获取大盘指数表格"""
    indices = [("SPY", "S&P 500"), ("QQQ", "Nasdaq 100"), ("VXX", "VIX Index")]
    rows = []
    for ticker, name in indices:
        try:
            q = fh_client.quote(ticker)
            chg = ((q['c'] - q['pc']) / q['pc']) * 100
            emoji = "🟢" if chg > 0 else "🔴"
            rows.append(f"| {emoji} {name} | {chg:+.2f}% |")
        except: continue
    header = "| 指标 | 涨跌 |\n|:---|:---:|"
    return header + "\n" + "\n".join(rows)

def get_stock_data(ticker):
    """计算个股量化指标 (MA200 & 52周位置)"""
    try:
        ticker = ticker.upper().strip()
        q = fh_client.quote(ticker)
        current = q['c']
        # 计算 200 日均线
        end = int(datetime.datetime.now().timestamp())
        start = end - 300 * 24 * 60 * 60
        candles = fh_client.stock_candles(ticker, 'D', start, end)
        if candles.get('s') == 'ok':
            closes = candles['c'][-200:]
            ma200 = sum(closes) / len(closes)
            pos_ma200 = ((current - ma200) / ma200) * 100
            
            high_52 = max(candles['h'][-252:])
            low_52 = min(candles['l'][-252:])
            pos_52w = ((current - low_52) / (high_52 - low_52)) * 100
            
            return {
                "ticker": ticker, "price": current, "chg": ((current-q['pc'])/q['pc']*100),
                "ma200": pos_ma200, "w52": pos_52w
            }
    except: return None

def get_philly_fed_index():
    """获取费城联储宏观数据"""
    if cfg["fred_key"]:
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=PHILFEI&api_key={cfg['fred_key']}&file_type=json&limit=1&sort_order=desc"
            data = requests.get(url).json()
            val = data['observations'][0]['value']
            return f"费城联储制造业指数: {val}"
        except: return "费城联储数据: 暂未更新"
    return "费城联储数据: 未配置 FRED_KEY"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. AI 分析逻辑 (Prompt 修复版)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def batch_identify_tickers(news_items):
    """批量识别 Ticker 以节省 API 额度"""
    summary_text = "\n".join([f"[{i}] {n['title']}" for i, n in enumerate(news_items)])
    prompt = f"仅输出股票代码。对以下新闻，识别涉及的美股代码，否则写 NONE。\n{summary_text}\n格式: [序号] TICKER"
    try:
        resp = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        mapping = {}
        for line in resp.text.strip().split('\n'):
            match = re.search(r'\[(\d+)\]\s*([A-Z,\s]+)', line)
            if match:
                idx = int(match.group(1))
                tkrs = [t.strip() for t in match.group(2).split(',') if t.strip() != 'NONE']
                if tkrs: mapping[idx] = tkrs
        return mapping
    except: return {}

def build_v4_prompt(news_items, ticker_map, stock_data, philly_fed_info):
    """构建带量化数据的深度分析 Prompt"""
    news_blocks = []
    for i, news in enumerate(news_items):
        block = f"【{i+1}】[{news['source']}] {news['title']}\n摘要：{news['summary']}"
        if i in ticker_map:
            for t in ticker_map[i]:
                if t in stock_data:
                    d = stock_data[t]
                    block += f"\n📊 数据: {t} ${d['price']:.2f} ({d['chg']:+.2f}%) | MA200位: {d['ma200']:+.1f}% | 52周位: {d['w52']:.0f}%"
        news_blocks.append(block)

    # 重要：此处使用 {{ }} 转义花括号，防止 Python 报错
    return f"""
你是融合了 Wharton 教授与 Citadel PM 思维的首席分析师。
费城时间：{datetime.datetime.now(ZoneInfo('America/New_York'))}

{chr(10).join(news_blocks)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【输出格式要求】

## 📰 [{{序号}}] [标题关键词]

**🎯 穿透观点**: 1句话直击本质。

**📊 量化定位**:
| 指标 | 数值 | 信号 |
|:---|:---:|:---|
| 情绪分 | [X]/10 | [利好/利空] |
| 200日均线位 | [X]% | [趋势判断] |

**⚖️ 三维透视**:
- *估值逻辑*: 基于实时均线数据分析。
- *政治风险*: 监管与政策隐患。

**🏛 费城联储视角**: {philly_fed_info} 对该新闻的宏观映射。
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 主程序执行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_v4_terminal():
    print("🚀 Bloomberg V4.0 Alpha 启动中...")
    start_time = datetime.datetime.now()
    philly_time = datetime.datetime.now(ZoneInfo("America/New_York"))
    
    # 抓取新闻 (WSJ & NYT)
    feeds = ["https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"]
    news = []
    for url in feeds:
        f = feedparser.parse(url)
        for e in f.entries[:3]:
            news.append({"title": e.title, "summary": e.get('summary', '')[:300], "source": "WSJ/NYT"})
    
    # 获取宏观与量化数据
    fed_info = get_philly_fed_index()
    ticker_map = batch_identify_tickers(news)
    
    unique_tickers = set()
    for tlist in ticker_map.values(): unique_tickers.update(tlist)
    
    stock_stats = {}
    for t in list(unique_tickers)[:5]: # 限制 5 只以防限流
        data = get_stock_data(t)
        if data: stock_stats[t] = data

    # AI 分析
    prompt = build_v4_prompt(news, ticker_map, stock_stats, fed_info)
    response = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    
    # 最终报告组装
    header = f"🏛 *王同学的全球决策终端 V4.0*\n📅 {philly_time.strftime('%Y-%m-%d %H:%M')}\n"
    header += f"📈 *市场脉搏*\n{get_market_pulse()}\n\n"
    header += f"🏭 {fed_info}\n━━━━━━━━━━━━━━\n\n"
    
    full_report = header + response.text
    
    # 发送
    requests.post(f"https://api.telegram.org/bot{cfg['tg_token']}/sendMessage", 
                  data={"chat_id": cfg['chat_id'], "text": full_report[:4000], "parse_mode": "Markdown"})
    print(f"✅ 报告已发送 (耗时 {(datetime.datetime.now() - start_time).seconds}s)")

if __name__ == "__main__":
    run_v4_terminal()
