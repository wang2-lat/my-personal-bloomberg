import os
import datetime
import requests
import json
import re
import feedparser
import finnhub
from google import genai
from zoneinfo import ZoneInfo

# --- 配置加载 ---
def get_config():
    cfg = {
        "lark_id": os.getenv("LARK_APP_ID"),
        "lark_secret": os.getenv("LARK_APP_SECRET"),
        "lark_chat_id": os.getenv("LARK_CHAT_ID"),
        "finnhub_key": os.getenv("FINNHUB_KEY"),
        "gemini_key": os.getenv("GEMINI_KEY"),
        "fred_key": os.getenv("FRED_KEY")
    }
    return cfg

cfg = get_config()
fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

# --- 飞书客户端 ---
class LarkClient:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
    
    def get_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={"app_id": self.app_id, "app_secret": self.app_secret})
        return resp.json().get("tenant_access_token")

    def send_card(self, chat_id, card_json):
        token = self.get_token()
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card_json, ensure_ascii=False)
        }
        return requests.post(url, headers=headers, json=payload)

lark_client = LarkClient(cfg["lark_id"], cfg["lark_secret"])

# --- 核心逻辑：获取数据 ---
def get_market_summary():
    # 获取标普500概况
    q = fh_client.quote("SPY")
    chg = ((q['c'] - q['pc']) / q['pc']) * 100
    return f"S&P 500: {chg:+.2f}%"

def run_v5():
    print("🚀 开始执行 V5.0 点火测试...")
    market_text = get_market_summary()
    
    # 构建一个简单的测试卡片
    test_card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "🏛 Bloomberg V5.0 已通电"}, "template": "blue"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"📅 **{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}**"}},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"📈 **市场脉搏**: {market_text}"}},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": "📍 来自费城的深夜点火测试"}]}
        ]
    }
    
    res = lark_client.send_card(cfg["lark_chat_id"], test_card)
    if res.status_code == 200:
        print("✅ 飞书卡片发送成功！快看手机。")
    else:
        print(f"❌ 发送失败，状态码: {res.status_code}, 响应: {res.text}")

if __name__ == "__main__":
    run_v5()
