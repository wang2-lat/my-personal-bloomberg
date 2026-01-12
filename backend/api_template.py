"""
My Personal Bloomberg - 后端 API 模板
=====================================

这是给下一位开发者的后端 API 模板。
部署到 Vercel 后，Android App 可以连接获取真实数据。

使用方法：
1. pip install fastapi uvicorn finnhub-python yfinance google-genai requests
2. 设置环境变量（FINNHUB_KEY, GEMINI_KEY, FRED_KEY）
3. uvicorn main:app --reload
4. 访问 http://localhost:8000/docs 查看 API 文档

部署到 Vercel：
1. 创建 vercel.json 配置文件
2. vercel --prod
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import finnhub
import yfinance as yf
from datetime import datetime
import pytz

# ============== 初始化 ==============

app = FastAPI(
    title="My Personal Bloomberg API",
    description="金融数据和AI分析API",
    version="1.0.0"
)

# 允许跨域（Android App 需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys（从环境变量读取）
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")
FRED_KEY = os.getenv("FRED_KEY", "")

# Finnhub 客户端
fh_client = finnhub.Client(api_key=FINNHUB_KEY) if FINNHUB_KEY else None


# ============== 数据模型 ==============

class MarketIndex(BaseModel):
    ticker: str
    name: str
    price: float
    change: float
    changePercent: float

class VixData(BaseModel):
    value: float
    level: str

class MarketOverview(BaseModel):
    timestamp: str
    indices: List[MarketIndex]
    vix: Optional[VixData]
    phillyFed: Optional[float]

class StockQuote(BaseModel):
    ticker: str
    price: float
    change: float
    changePercent: float
    previousClose: float

class StockFundamentals(BaseModel):
    ticker: str
    companyName: str
    sector: str
    pe: Optional[float]
    forwardPe: Optional[float]
    marketCap: Optional[int]
    week52High: Optional[float]
    week52Low: Optional[float]
    week52Position: Optional[float]
    beta: Optional[float]
    targetPrice: Optional[float]
    upside: Optional[float]

class AnalystRating(BaseModel):
    ticker: str
    buyCount: int
    holdCount: int
    sellCount: int
    consensus: str

class AIAnalysis(BaseModel):
    score: int
    signal: str
    coreJudgment: str
    causalChain: str
    valuationView: str
    risk: str
    recommendation: str

class NewsCard(BaseModel):
    id: str
    title: str
    source: str
    publishedAt: str
    ticker: str
    quote: Optional[StockQuote]
    fundamentals: Optional[StockFundamentals]
    analyst: Optional[AnalystRating]
    analysis: AIAnalysis


# ============== 辅助函数 ==============

def get_est_time():
    """获取美东时间"""
    est = pytz.timezone('US/Eastern')
    return datetime.now(est).strftime("%Y-%m-%d %H:%M EST")

def get_vix_level(value: float) -> str:
    """根据 VIX 值判断恐慌级别"""
    if value < 15:
        return "低恐慌"
    elif value < 20:
        return "正常"
    elif value < 30:
        return "警惕"
    else:
        return "高恐慌"

def get_analyst_consensus(buy: int, hold: int, sell: int) -> str:
    """判断分析师共识"""
    total = buy + hold + sell
    if total == 0:
        return "无数据"
    buy_ratio = buy / total
    if buy_ratio > 0.6:
        return "买入"
    elif buy_ratio < 0.3:
        return "卖出"
    else:
        return "持有"


# ============== API 端点 ==============

@app.get("/")
async def root():
    return {"message": "My Personal Bloomberg API", "status": "running"}


@app.get("/api/market-overview", response_model=MarketOverview)
async def get_market_overview():
    """获取市场概览数据"""
    
    indices = []
    
    # 获取主要指数数据
    tickers = [
        ("SPY", "S&P500"),
        ("QQQ", "纳指100"),
        ("DIA", "道指")
    ]
    
    for ticker, name in tickers:
        try:
            if fh_client:
                quote = fh_client.quote(ticker)
                indices.append(MarketIndex(
                    ticker=ticker,
                    name=name,
                    price=quote.get('c', 0),
                    change=quote.get('d', 0),
                    changePercent=quote.get('dp', 0)
                ))
            else:
                # 使用 yfinance 作为备选
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                if len(hist) >= 2:
                    price = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = price - prev
                    change_pct = (change / prev) * 100
                    indices.append(MarketIndex(
                        ticker=ticker,
                        name=name,
                        price=round(price, 2),
                        change=round(change, 2),
                        changePercent=round(change_pct, 2)
                    ))
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
    
    # 获取 VIX
    vix_data = None
    try:
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="1d")
        if not vix_hist.empty:
            vix_value = round(vix_hist['Close'].iloc[-1], 2)
            vix_data = VixData(
                value=vix_value,
                level=get_vix_level(vix_value)
            )
    except Exception as e:
        print(f"Error fetching VIX: {e}")
    
    # 获取费城联储指数（需要 FRED API）
    philly_fed = None
    # TODO: 实现 FRED API 调用
    
    return MarketOverview(
        timestamp=get_est_time(),
        indices=indices,
        vix=vix_data,
        phillyFed=philly_fed
    )


@app.get("/api/stock/{ticker}")
async def get_stock_data(ticker: str):
    """获取单只股票的详细数据"""
    
    ticker = ticker.upper()
    
    # 获取报价
    quote = None
    if fh_client:
        try:
            q = fh_client.quote(ticker)
            quote = StockQuote(
                ticker=ticker,
                price=q.get('c', 0),
                change=q.get('d', 0),
                changePercent=q.get('dp', 0),
                previousClose=q.get('pc', 0)
            )
        except Exception as e:
            print(f"Finnhub error: {e}")
    
    # 获取基本面（yfinance）
    fundamentals = None
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 计算 52 周位置
        week52_pos = None
        high = info.get('fiftyTwoWeekHigh')
        low = info.get('fiftyTwoWeekLow')
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        if high and low and price and high != low:
            week52_pos = round(((price - low) / (high - low)) * 100, 1)
        
        # 计算目标价上涨空间
        upside = None
        target = info.get('targetMeanPrice')
        if target and price:
            upside = round(((target - price) / price) * 100, 1)
        
        fundamentals = StockFundamentals(
            ticker=ticker,
            companyName=info.get('shortName', ticker),
            sector=info.get('sector', 'Unknown'),
            pe=info.get('trailingPE'),
            forwardPe=info.get('forwardPE'),
            marketCap=info.get('marketCap'),
            week52High=high,
            week52Low=low,
            week52Position=week52_pos,
            beta=info.get('beta'),
            targetPrice=target,
            upside=upside
        )
    except Exception as e:
        print(f"yfinance error: {e}")
    
    # 获取分析师评级
    analyst = None
    if fh_client:
        try:
            rec = fh_client.recommendation_trends(ticker)
            if rec:
                latest = rec[0]
                buy = latest.get('buy', 0) + latest.get('strongBuy', 0)
                hold = latest.get('hold', 0)
                sell = latest.get('sell', 0) + latest.get('strongSell', 0)
                analyst = AnalystRating(
                    ticker=ticker,
                    buyCount=buy,
                    holdCount=hold,
                    sellCount=sell,
                    consensus=get_analyst_consensus(buy, hold, sell)
                )
        except Exception as e:
            print(f"Analyst rating error: {e}")
    
    return {
        "success": True,
        "quote": quote,
        "fundamentals": fundamentals,
        "analyst": analyst
    }


@app.get("/api/news")
async def get_news(limit: int = 4):
    """获取新闻并进行 AI 分析"""
    
    # TODO: 实现以下步骤
    # 1. 从 WSJ RSS 抓取新闻
    # 2. 为每条新闻提取相关股票
    # 3. 获取股票数据
    # 4. 调用 Gemini AI 进行分析
    # 5. 返回 NewsCard 列表
    
    # 临时返回模拟数据
    return {
        "success": True,
        "data": [
            {
                "id": "1",
                "title": "示例新闻标题",
                "source": "WSJ",
                "publishedAt": get_est_time(),
                "ticker": "AAPL",
                "quote": None,
                "fundamentals": None,
                "analyst": None,
                "analysis": {
                    "score": 6,
                    "signal": "中性",
                    "coreJudgment": "这是一条示例新闻，请实现真实的新闻抓取和AI分析。",
                    "causalChain": "新闻事件 → 市场反应 → 股价影响",
                    "valuationView": "请连接真实数据源",
                    "risk": "数据为模拟数据",
                    "recommendation": "请完成后端开发"
                }
            }
        ]
    }


@app.get("/api/analyze")
async def analyze_news(title: str, ticker: str):
    """使用 AI 分析新闻"""
    
    # TODO: 实现 Gemini AI 分析
    # 参考 push_telegram.py 中的 analyze_with_ai 函数
    
    return {
        "success": True,
        "analysis": {
            "score": 5,
            "signal": "中性",
            "coreJudgment": "AI 分析功能待实现",
            "causalChain": "请配置 GEMINI_KEY",
            "valuationView": "请参考 push_telegram.py",
            "risk": "功能待开发",
            "recommendation": "请完成 Gemini 集成"
        }
    }


# ============== Vercel 配置 ==============
"""
创建 vercel.json 文件：

{
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}

创建 requirements.txt 文件：

fastapi
uvicorn
finnhub-python
yfinance
google-genai
requests
pytz
pydantic
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
