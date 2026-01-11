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

missing = [k for k, v in cfg.items() if not v and k != "fred_key"]
if missing:
    raise ValueError(f"❌ 缺少环境变量: {missing}")

fh_client = finnhub.Client(api_key=cfg["finnhub_key"])
gemini_client = genai.Client(api_key=cfg["gemini_key"])

# 公司名 → Ticker 映射表（扩展版）
COMPANY_TICKER_MAP = {
    # 科技巨头
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "alphabet": "GOOGL", "amazon": "AMZN", "meta": "META", "facebook": "META",
    "tesla": "TSLA", "netflix": "NFLX", "amd": "AMD", "intel": "INTC",
    "broadcom": "AVGO", "salesforce": "CRM", "oracle": "ORCL", "ibm": "IBM",
    "adobe": "ADBE", "cisco": "CSCO", "qualcomm": "QCOM",
    # 零售
    "walmart": "WMT", "costco": "COST", "target": "TGT", "home depot": "HD",
    "lowe's": "LOW", "dollar general": "DG", "kroger": "KR",
    # 金融
    "jpmorgan": "JPM", "goldman": "GS", "morgan stanley": "MS",
    "bank of america": "BAC", "wells fargo": "WFC", "citigroup": "C",
    "blackrock": "BLK", "visa": "V", "mastercard": "MA",
    # 工业/能源
    "boeing": "BA", "exxon": "XOM", "chevron": "CVX", "caterpillar": "CAT",
    "lockheed": "LMT", "general electric": "GE", "3m": "MMM",
    # 医疗
    "pfizer": "PFE", "johnson": "JNJ", "unitedhealth": "UNH",
    "eli lilly": "LLY", "merck": "MRK", "abbvie": "ABBV",
    # 消费
    "disney": "DIS", "nike": "NKE", "starbucks": "SBUX",
    "coca-cola": "KO", "pepsi": "PEP", "mcdonald": "MCD",
    "procter": "PG", "p&g": "PG",
    # 新经济
    "uber": "UBER", "airbnb": "ABNB", "doordash": "DASH",
    "spotify": "SPOT", "snap": "SNAP", "pinterest": "PINS",
    # AI 关联
    "openai": "MSFT", "anthropic": "GOOGL", "chatgpt": "MSFT",
}

# 需要排除的非股票代码词汇
EXCLUDE_TICKERS = {
    'THE', 'AND', 'FOR', 'CEO', 'IPO', 'SEC', 'FDA', 'GDP', 'AI', 'US', 'UK', 'EU',
    'USD', 'DEI', 'ESG', 'ETF', 'NYSE', 'NASA', 'FBI', 'CIA', 'NFL', 'NBA', 'MLB',
    'COVID', 'WHO', 'IMF', 'FED', 'ECB', 'BOJ', 'RBI', 'OPEC', 'NATO', 'UN',
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
        now = datetime.datetime.now().timestamp()
        if self._token and now < self._token_expire - 60:
            return self._token
