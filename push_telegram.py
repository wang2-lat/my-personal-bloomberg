import finnhub
import google.generativeai as genai
import requests
import datetime
import feedparser
import os

# --- 1. 配置 (从 GitHub Secrets 自动读取) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# --- 2. 初始化客户端 ---
finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') # 2026年推荐使用的快速模型

# --- 3. 情报源配置 (借用 finance-news-mcp 核心精华) ---
RSS_SOURCES = {
    "WSJ_商业": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "WSJ_市场": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "NYT_技术": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "NYT_政治": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
}

def get_comprehensive_news():
    news_pool = []
    # 抓取 Finnhub 快讯
    try:
        fh_news = finnhub_client.general_news('general', min_id=0)[:8]
        for n in fh_news:
            news_pool.append({"title": n['headline'], "summary": n['summary'], "source": "Finnhub"})
    except: print("Finnhub 获取失败")
    
    # 抓取 RSS 顶级深度报道
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # 每个源取前 3 条
                news_pool.append({
                    "title": entry.title, 
                    "summary": getattr(entry, 'summary', '查看原文获取详情'), 
                    "source": name
                })
        except: print(f"{name} 获取失败")
    return news_pool

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def run_ai_terminal():
    print("🚀 正在收集全球多维情报...")
    raw_news = get_comprehensive_news()
    
    header = f"🏛 *王同学的全球情报终端 (Bloomberg 2.0)*\n"
    header += f"📅 {datetime.date.today()} | 城市: Philadelphia\n"
    header += "==============================\n\n"
    
    send_telegram(header) # 先发报头

    for item in raw_news[:12]: # 选取最精华的 12 条进行 AI 深度解析
        prompt = f"""
        你是一名身处费城的资深量化与政治分析师。
        请对以下来自顶级媒体（{item['source']}）的新闻进行【彭博终端级】深度解读：
        
        1. 【核心翻译】简明扼要的中文总结。
        2. 【深度洞察】结合 AI 浪潮（如 Nvidia）、地缘政治或历史背景分析本质。
        3. 【情绪评分】利好/利空程度 (-10 到 +10)。
        
        新闻标题：{item['title']}
        新闻内容：{item['summary']}
        """
        try:
            analysis = model.generate_content(prompt).text.strip()
            send_telegram(analysis) # 逐条发送，防止消息过长被屏蔽
        except: continue

if __name__ == "__main__":
    run_ai_terminal()
