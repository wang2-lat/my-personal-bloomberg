import finnhub
import google.generativeai as genai
import requests
import datetime

# --- 1. 配置信息 ---
TELEGRAM_TOKEN = "7762507386:AAG_FsGY2ur7yB6CID-9zKk3BaniBnHUmGI"
CHAT_ID = "8048594162"  # 填入第一步拿到的数字
FINNHUB_KEY = "d5hf2tpr01qqequ238dgd5hf2tpr01qqequ238e0"
GEMINI_KEY = "AIzaSyDOOazqDeyv8XBbaG5F5zKIiEpDroqHdpA"

# --- 2. 初始化 ---
finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') # 使用最快模型

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def run_ai_morning_report():
    print("🚀 正在抓取并分析新闻...")
    news = finnhub_client.general_news('general', min_id=0)
    
    # 结合你的兴趣：AI、Nvidia、费城、沃顿研究
    interests = ["AI", "Nvidia", "Software", "Wharton", "Philadelphia", "Fed"]
    
    report = f"🤖 *个人金融情报终端* \n"
    report += f"📅 {datetime.date.today()} | 城市: Philadelphia\n"
    report += "----------------------------\n"
    
    count = 0
    for item in news:
        # 只处理你关心的关键词
        if any(word.lower() in item['headline'].lower() for word in interests):
            # 调用 AI 进行中文深度摘要
            prompt = f"""
            你是一个资深分析师。请用中文总结这则新闻对市场或相关公司的影响（20字以内）。
            新闻标题：{item['headline']}
            摘要：{item['summary']}
            """
            try:
                ai_summary = model.generate_content(prompt).text.strip()
                report += f"🔥 *{ai_summary}*\n"
                report += f"🔗 [阅读原文]({item['url']})\n\n"
                count += 1
            except:
                continue
        
        if count >= 5: break # 每天早上只看最精华的 5 条

    if count > 0:
        send_telegram_msg(report)
        print("✅ 成功！请查看你的 Telegram。")
    else:
        print("📭 当前无匹配新闻。")

if __name__ == "__main__":
    run_ai_morning_report()
