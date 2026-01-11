import finnhub, google.generativeai as genai, requests, datetime, feedparser, os

# --- 1. 变量检查 ---
def check_secrets():
    keys = ["TELEGRAM_TOKEN", "CHAT_ID", "FINNHUB_KEY", "GEMINI_KEY"]
    for k in keys:
        val = os.getenv(k)
        if not val:
            print(f"❌ 错误：机密变量 {k} 为空！请检查 GitHub Secrets 设置。")
        else:
            print(f"✅ 已识别：{k} (长度: {len(val)})")

# --- 2. 抓取逻辑 ---
def get_debug_news():
    news_pool = []
    # 尝试抓取 Finnhub
    try:
        fh_news = finnhub.Client(api_key=os.getenv("FINNHUB_KEY")).general_news('general', min_id=0)[:5]
        print(f"📡 Finnhub 抓取到 {len(fh_news)} 条原始新闻")
        for n in fh_news:
            news_pool.append({"title": n['headline'], "summary": n['summary'], "source": "Finnhub"})
    except Exception as e:
        print(f"❌ Finnhub 抓取失败: {e}")

    # 尝试抓取 RSS
    rss_url = "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"
    try:
        feed = feedparser.parse(rss_url)
        print(f"📡 WSJ RSS 抓取到 {len(feed.entries)} 条原始新闻")
        for entry in feed.entries[:3]:
            news_pool.append({"title": entry.title, "summary": getattr(entry, 'summary', ''), "source": "WSJ"})
    except Exception as e:
        print(f"❌ RSS 抓取失败: {e}")
    
    return news_pool

# --- 3. 主程序 ---
def run_debug_terminal():
    print("🚀 --- 开始深度调试任务 ---")
    check_secrets()
    
    raw_news = get_debug_news()
    print(f"📊 待处理新闻总计: {len(raw_news)} 条")

    if len(raw_news) == 0:
        print("📭 警告：没有任何新闻源返回数据，调试结束。")
        return

    # 初始化 AI
    genai.configure(api_key=os.getenv("GEMINI_KEY"))
    model = genai.GenerativeModel('gemini-2.0-flash')

    for i, item in enumerate(raw_news):
        print(f"🤖 正在处理第 {i+1} 条 AI 分析...")
        prompt = f"请简短总结这则新闻：{item['title']}"
        try:
            analysis = model.generate_content(prompt).text.strip()
            # 强制发送，观察返回
            url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
            res = requests.post(url, data={"chat_id": os.getenv("CHAT_ID"), "text": f"测试 {i+1}:\n{analysis}"})
            print(f"📤 Telegram 返回状态: {res.status_code}")
        except Exception as e:
            print(f"❌ 分析或发送失败: {e}")

if __name__ == "__main__":
    run_debug_terminal()
