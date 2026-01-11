import os
import datetime
import requests
import feedparser
import finnhub
import re
from google import genai
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配置层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_config():
    cfg = {
        "tg_token": os.getenv("TELEGRAM_TOKEN"),
        "chat_id": os.getenv("CHAT_ID"),
        "finnhub_key": os.getenv("FINNHUB_KEY"),
        "gemini_key": os.getenv("GEMINI_KEY"),
        "fred_key": os.getenv("FRED_KEY")  # 可选：用于获取费城联储数据
    }
    # 验证必要配置
    missing = [k for k, v in cfg.items() if not v and k != "fred_key"]
    if missing:
        raise ValueError(f"缺少环境变量: {missing}")
    return cfg

cfg = get_config()
fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

# 公司名 → Ticker 映射表（高频出现的公司）
COMPANY_TICKER_MAP = {
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "alphabet": "GOOGL", "amazon": "AMZN", "meta": "META", "facebook": "META",
    "tesla": "TSLA", "netflix": "NFLX", "amd": "AMD", "intel": "INTC",
    "broadcom": "AVGO", "salesforce": "CRM", "oracle": "ORCL", "ibm": "IBM",
    "walmart": "WMT", "costco": "COST", "target": "TGT", "home depot": "HD",
    "jpmorgan": "JPM", "goldman": "GS", "morgan stanley": "MS", "blackrock": "BLK",
    "berkshire": "BRK.B", "visa": "V", "mastercard": "MA", "paypal": "PYPL",
    "boeing": "BA", "lockheed": "LMT", "raytheon": "RTX", "general electric": "GE",
    "exxon": "XOM", "chevron": "CVX", "conocophillips": "COP",
    "pfizer": "PFE", "johnson": "JNJ", "unitedhealth": "UNH", "eli lilly": "LLY",
    "disney": "DIS", "comcast": "CMCSA", "verizon": "VZ", "at&t": "T",
    "uber": "UBER", "airbnb": "ABNB", "doordash": "DASH", "spotify": "SPOT",
    "openai": "MSFT",  # OpenAI 关联 MSFT
    "anthropic": "GOOGL",  # Anthropic 关联 GOOGL
}

# 制造业关键词（触发费城联储关联）
MANUFACTURING_KEYWORDS = [
    "manufacturing", "factory", "industrial", "production", "supply chain",
    "制造", "工厂", "产能", "供应链", "工业", "生产"
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据抓取层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_market_pulse():
    """获取核心市场指标，返回 Markdown 表格"""
    indices = [
        ("SPY", "S&P 500", "大盘风向"),
        ("QQQ", "Nasdaq 100", "科技情绪"),
        ("IWM", "Russell 2000", "小盘活力"),
        ("TLT", "20Y Treasury", "利率预期"),
        ("GLD", "黄金 ETF", "避险情绪"),
        ("VXX", "VIX 恐慌指数", "波动率"),
    ]
    
    rows = []
    for ticker, name, meaning in indices:
        try:
            q = fh_client.quote(ticker)
            if q.get('c') and q.get('pc'):
                chg = ((q['c'] - q['pc']) / q['pc']) * 100
                emoji = "🟢" if chg > 0.3 else "🔴" if chg < -0.3 else "⚪"
                rows.append(f"| {emoji} {name} | {chg:+.2f}% | {meaning} |")
        except:
            continue
    
    if not rows:
        return "| 指标 | 涨跌 | 含义 |\n|---|---|---|\n| ⚠️ 数据暂不可用 | - | - |"
    
    header = "| 指标 | 涨跌 | 信号含义 |\n|:---|:---:|:---|"
    return header + "\n" + "\n".join(rows)


def get_stock_data(ticker):
    """获取个股完整数据：实时价格 + 技术指标"""
    try:
        ticker = ticker.upper().strip()
        if not re.match(r'^[A-Z]{1,5}$', ticker):
            return None
        
        # 实时报价
        q = fh_client.quote(ticker)
        if not (q.get('c') and q.get('pc')):
            return None
        
        current_price = q['c']
        prev_close = q['pc']
        day_change = ((current_price - prev_close) / prev_close) * 100
        day_high = q.get('h', current_price)
        day_low = q.get('l', current_price)
        
        # 获取历史数据计算均线
        ma_200_position = calculate_ma_position(ticker, current_price, 200)
        ma_50_position = calculate_ma_position(ticker, current_price, 50)
        
        # 52周高低点
        week_52 = get_52_week_range(ticker, current_price)
        
        return {
            "ticker": ticker,
            "price": current_price,
            "change_pct": day_change,
            "day_high": day_high,
            "day_low": day_low,
            "ma_50_position": ma_50_position,
            "ma_200_position": ma_200_position,
            "week_52_position": week_52,
            "summary": format_stock_summary(ticker, current_price, day_change, ma_200_position, week_52)
        }
    except Exception as e:
        print(f"获取 {ticker} 数据失败: {e}")
        return None


def calculate_ma_position(ticker, current_price, days):
    """计算当前价格相对于 N 日均线的位置"""
    try:
        # 获取历史 K 线
        end = int(datetime.datetime.now().timestamp())
        start = end - (days + 30) * 24 * 60 * 60  # 多取30天buffer
        
        candles = fh_client.stock_candles(ticker, 'D', start, end)
        if candles.get('s') != 'ok' or len(candles.get('c', [])) < days:
            return None
        
        closes = candles['c'][-days:]
        ma = sum(closes) / len(closes)
        position = ((current_price - ma) / ma) * 100
        
        return round(position, 2)
    except:
        return None


def get_52_week_range(ticker, current_price):
    """计算当前价格在52周范围内的位置"""
    try:
        end = int(datetime.datetime.now().timestamp())
        start = end - 365 * 24 * 60 * 60
        
        candles = fh_client.stock_candles(ticker, 'D', start, end)
        if candles.get('s') != 'ok':
            return None
        
        high_52 = max(candles.get('h', [current_price]))
        low_52 = min(candles.get('l', [current_price]))
        
        if high_52 == low_52:
            return 50.0
        
        position = ((current_price - low_52) / (high_52 - low_52)) * 100
        return round(position, 1)
    except:
        return None


def format_stock_summary(ticker, price, change, ma_200, week_52):
    """格式化股票摘要"""
    parts = [f"{ticker}: ${price:.2f} ({change:+.2f}%)"]
    
    if ma_200 is not None:
        trend = "上方" if ma_200 > 0 else "下方"
        parts.append(f"200MA{trend} {abs(ma_200):.1f}%")
    
    if week_52 is not None:
        if week_52 > 90:
            parts.append("📈 接近52周新高")
        elif week_52 < 10:
            parts.append("📉 接近52周新低")
        else:
            parts.append(f"52周位置: {week_52:.0f}%")
    
    return " | ".join(parts)


def get_philly_fed_index():
    """获取费城联储制造业指数"""
    # 方法1: 尝试 FRED API
    if cfg.get("fred_key"):
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": "MANEMP",  # 制造业就业
                "api_key": cfg["fred_key"],
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.ok:
                data = resp.json()
                obs = data.get("observations", [{}])[0]
                return f"最新制造业就业: {obs.get('value', 'N/A')}K"
        except:
            pass
    
    # 方法2: 返回固定说明（实际部署时可接入真实API）
    return "费城联储制造业指数: 关注供应链与产能利用率动态"


def fetch_top_news():
    """抓取顶级财经新闻"""
    sources = {
        "WSJ": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        "NYT_Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "NYT_Biz": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    }
    
    pool = []
    for name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = entry.get('title', '')
                summary = entry.get('summary', '')[:500]
                
                # 检测是否涉及制造业
                combined_text = (title + " " + summary).lower()
                is_manufacturing = any(kw in combined_text for kw in MANUFACTURING_KEYWORDS)
                
                pool.append({
                    "title": title,
                    "summary": summary,
                    "source": name.replace("_", " "),
                    "is_manufacturing": is_manufacturing
                })
        except Exception as e:
            print(f"抓取 {name} 失败: {e}")
            continue
    
    return pool[:8]  # 限制总数

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Ticker 前置识别层（V4 核心改进）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_tickers_from_text(text):
    """从文本中模糊识别潜在 Ticker"""
    text_lower = text.lower()
    found_tickers = set()
    
    # 方法1: 查表匹配公司名
    for company, ticker in COMPANY_TICKER_MAP.items():
        if company in text_lower:
            found_tickers.add(ticker)
    
    # 方法2: 正则匹配可能的 Ticker（全大写1-5字母）
    # 排除常见非 Ticker 词汇
    exclude_words = {'THE', 'AND', 'FOR', 'NEW', 'CEO', 'CFO', 'IPO', 'SEC', 'FDA', 'USA', 'GDP', 'AI', 'CEO'}
    potential = re.findall(r'\b([A-Z]{2,5})\b', text)
    for p in potential:
        if p not in exclude_words and len(p) >= 2:
            found_tickers.add(p)
    
    return list(found_tickers)


def batch_identify_tickers(news_items):
    """使用轻量 AI 调用批量识别新闻中的 Ticker"""
    # 先用规则提取
    rule_based = {}
    for i, news in enumerate(news_items):
        text = news['title'] + " " + news['summary']
        tickers = extract_tickers_from_text(text)
        if tickers:
            rule_based[i] = tickers[:3]  # 每条新闻最多3个
    
    # 对于规则未能识别的，用 AI 补充
    unidentified = [i for i in range(len(news_items)) if i not in rule_based]
    
    if unidentified:
        # 构建轻量 prompt
        news_text = "\n".join([
            f"[{i}] {news_items[i]['title']}" 
            for i in unidentified
        ])
        
        prompt = f"""
仅输出股票代码。对以下每条新闻，如果涉及上市公司，输出其美股代码；否则输出 NONE。
格式：[序号] TICKER

{news_text}

示例输出：
[0] AAPL
[1] NONE
[2] TSLA, RIVN
"""
        try:
            resp = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            # 解析 AI 输出
            for line in resp.text.strip().split('\n'):
                match = re.match(r'\[(\d+)\]\s*(.+)', line.strip())
                if match:
                    idx = int(match.group(1))
                    tickers_str = match.group(2).strip()
                    if tickers_str.upper() != 'NONE':
                        tickers = [t.strip() for t in tickers_str.split(',')]
                        tickers = [t for t in tickers if re.match(r'^[A-Z]{1,5}$', t)]
                        if tickers:
                            rule_based[idx] = tickers[:3]
        except Exception as e:
            print(f"AI Ticker 识别失败: {e}")
    
    return rule_based


def prefetch_stock_data(ticker_map):
    """预抓取所有识别到的股票数据"""
    all_tickers = set()
    for tickers in ticker_map.values():
        all_tickers.update(tickers)
    
    stock_data = {}
    for ticker in all_tickers:
        data = get_stock_data(ticker)
        if data:
            stock_data[ticker] = data
    
    return stock_data

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI 分析层（带量化数据的 Prompt）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_v4_prompt(news_items, ticker_map, stock_data, philly_fed_info):
    """构建 V4 版本的分析 Prompt，带入预抓取的量化数据"""
    
    news_blocks = []
    for i, news in enumerate(news_items):
        block = f"【{i+1}】[{news['source']}] {news['title']}\n摘要：{news['summary']}"
        
        # 附加已抓取的股票数据
        if i in ticker_map:
            tickers = ticker_map[i]
            data_lines = []
            for t in tickers:
                if t in stock_data:
                    d = stock_data[t]
                    data_lines.append(
                        f"  • {t}: ${d['price']:.2f} ({d['change_pct']:+.2f}%) | "
                        f"MA200位置: {d['ma_200_position']}% | 52周位置: {d['week_52_position']}%"
                    )
            if data_lines:
                block += "\n📊 实时数据:\n" + "\n".join(data_lines)
        
        # 标记制造业相关
        if news['is_manufacturing']:
            block += f"\n🏭 [制造业关联] {philly_fed_info}"
        
        news_blocks.append(block)
    
    return f"""
你是融合了 Wharton 量化金融教授与 Citadel 宏观策略 PM 思维的首席分析师。
当前时间：{datetime.datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M')} (费城时间)

以下是今日重要财经新闻，每条新闻已附带实时股票数据（如有）。

{chr(10).join(news_blocks)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【V4 输出格式要求】（严格遵守）

对每条新闻，输出以下结构：

## 📰 [{序号}] [标题关键词，不超过8字]

**🎯 穿透观点** (1句话直击本质，不要废话)

**📊 量化定位**
| 指标 | 数值 | 信号 |
|:---|:---:|:---|
| 情绪分 | [X]/10 | [利好/利空/中性] |
| 相关标的 | [TICKER] | [使用我提供的实时数据分析] |
| 200日均线位置 | [X]% | [趋势判断：上涨/下跌/横盘] |
| 52周位置 | [X]% | [高位风险/低位机会/中性] |

**⚖️ 三维透视**
- *估值逻辑*: 基于当前股价和均线位置，判断估值合理性
- *政治风险*: 监管、地缘、政策层面隐患
- *历史镜鉴*: 类似历史事件及后续走势

**🏛 费城联储视角**: 
[如果新闻涉及制造业，必须引用费城联储制造业指数，分析对区域经济和货币政策的影响]
[如果不涉及制造业，从费城联储的利率预期或就业数据角度点评]

---

【语气要求】
- 冷峻、专业、不废话
- 像在给 Citadel LP 写每周市场简报
- 直接使用我提供的量化数据，不要虚构数字
- 如果某只股票没有数据，注明"数据暂缺"
"""


def extract_ai_analysis(response_text):
    """清理 AI 输出"""
    # 移除可能的 markdown 代码块标记
    text = response_text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return text

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Telegram 发送层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_telegram(text, chat_id, token):
    """分段发送 Telegram 消息"""
    MAX_LEN = 4000
    
    # 按自然分隔符切分
    if len(text) <= MAX_LEN:
        chunks = [text]
    else:
        chunks = []
        current = ""
        for line in text.split('\n'):
            if len(current) + len(line) + 1 > MAX_LEN:
                if current:
                    chunks.append(current)
                current = line
            else:
                current = current + '\n' + line if current else line
        if current:
            chunks.append(current)
    
    for i, chunk in enumerate(chunks):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={
                    "chat_id": chat_id, 
                    "text": chunk, 
                    "parse_mode": "Markdown"
                },
                timeout=15
            )
            if not resp.ok:
                # Markdown 解析失败时降级到纯文本
                resp = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": chunk},
                    timeout=15
                )
                if not resp.ok:
                    print(f"Telegram 发送失败 (chunk {i+1}): {resp.text}")
        except Exception as e:
            print(f"Telegram 异常: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主程序
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_v4_terminal():
    print("🚀 Bloomberg V4.0 Alpha 启动中...")
    start_time = datetime.datetime.now()
    
    # 获取时间
    philly_time = datetime.datetime.now(ZoneInfo("America/New_York"))
    
    # Step 1: 获取市场脉搏
    print("📈 抓取市场指数...")
    market_pulse = get_market_pulse()
    
    # Step 2: 获取费城联储数据
    print("🏛 获取费城联储数据...")
    philly_fed_info = get_philly_fed_index()
    
    # Step 3: 抓取新闻
    print("📰 抓取财经新闻...")
    news = fetch_top_news()
    if not news:
        error_msg = "⚠️ 今日暂无新闻源可用，请检查网络连接"
        send_telegram(error_msg, cfg['chat_id'], cfg['tg_token'])
        return
    
    # Step 4: 前置识别 Ticker（V4 核心）
    print("🔍 前置识别股票代码...")
    ticker_map = batch_identify_tickers(news)
    print(f"   识别到 {sum(len(v) for v in ticker_map.values())} 个潜在标的")
    
    # Step 5: 预抓取股票数据
    print("📊 预抓取股票量化数据...")
    stock_data = prefetch_stock_data(ticker_map)
    print(f"   成功获取 {len(stock_data)} 只股票数据")
    
    # Step 6: 构建 Prompt 并调用 AI
    print("🤖 生成深度分析...")
    prompt = build_v4_prompt(news, ticker_map, stock_data, philly_fed_info)
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        ai_analysis = extract_ai_analysis(response.text)
    except Exception as e:
        ai_analysis = f"⚠️ AI 分析暂不可用: {e}"
    
    # Step 7: 构建完整报告
    header = f"""
🏛 *王同学的全球决策终端 V4.0 Alpha*
📅 {philly_time.strftime('%Y-%m-%d %H:%M')} | Philadelphia
⏱ 数据延迟: <{(datetime.datetime.now() - start_time).seconds}s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 *市场脉搏*

{market_pulse}

🏭 *费城联储*: {philly_fed_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 *已追踪标的*: {', '.join(stock_data.keys()) if stock_data else '无'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    # 添加实时行情摘要
    if stock_data:
        quote_lines = []
        for ticker, data in stock_data.items():
            emoji = "🟢" if data['change_pct'] > 0 else "🔴" if data['change_pct'] < 0 else "⚪"
            quote_lines.append(f"{emoji} `{data['summary']}`")
        header += "*实时行情快照*\n" + "\n".join(quote_lines) + "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    full_report = header + ai_analysis
    
    # Step 8: 发送
    print("📤 发送报告至 Telegram...")
    send_telegram(full_report, cfg['chat_id'], cfg['tg_token'])
    
    print(f"✅ V4.0 Alpha 报告已发送 (耗时 {(datetime.datetime.now() - start_time).seconds}s)")


if __name__ == "__main__":
    run_v4_terminal()
