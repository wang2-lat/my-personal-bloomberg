package com.jeremy.bloomberg.model

/**
 * 市场指数数据
 */
data class MarketIndex(
    val ticker: String,
    val name: String,
    val price: Double,
    val change: Double,
    val changePercent: Double
) {
    val isPositive: Boolean get() = change >= 0
    val emoji: String get() = if (isPositive) "🟢" else "🔴"
}

/**
 * 股票报价
 */
data class StockQuote(
    val ticker: String,
    val price: Double,
    val change: Double,
    val changePercent: Double,
    val previousClose: Double
)

/**
 * 股票基本面数据
 */
data class StockFundamentals(
    val ticker: String,
    val companyName: String,
    val sector: String,
    val pe: Double?,
    val forwardPe: Double?,
    val marketCap: Long?,
    val week52High: Double?,
    val week52Low: Double?,
    val week52Position: Double?,
    val beta: Double?,
    val targetPrice: Double?,
    val targetHigh: Double?,
    val targetLow: Double?,
    val upside: Double?
)

/**
 * 分析师评级
 */
data class AnalystRating(
    val ticker: String,
    val buyCount: Int,
    val holdCount: Int,
    val sellCount: Int,
    val consensus: String
) {
    val total: Int get() = buyCount + holdCount + sellCount
    val displayText: String get() = "$consensus ($buyCount/$holdCount/$sellCount)"
}

/**
 * AI 分析结果
 */
data class AIAnalysis(
    val score: Int,
    val signal: String,
    val coreJudgment: String,
    val causalChain: String,
    val valuationView: String,
    val risk: String,
    val recommendation: String
) {
    val emoji: String get() = when {
        score >= 7 -> "🟢"
        score <= 4 -> "🔴"
        else -> "⚪"
    }

    val color: Long get() = when {
        score >= 7 -> 0xFF4CAF50
        score <= 4 -> 0xFFF44336
        else -> 0xFF2196F3
    }
}

/**
 * 新闻卡片完整数据
 */
data class NewsCard(
    val id: String,
    val title: String,
    val source: String,
    val publishedAt: String,
    val ticker: String,
    val quote: StockQuote?,
    val fundamentals: StockFundamentals?,
    val analyst: AnalystRating?,
    val analysis: AIAnalysis
)

/**
 * 市场概览数据
 */
data class MarketOverview(
    val timestamp: String,
    val indices: List<MarketIndex>,
    val vix: VixData?,
    val phillyFed: Double?
)

/**
 * VIX 恐慌指数
 */
data class VixData(
    val value: Double,
    val level: String
) {
    val emoji: String get() = when {
        value < 20 -> "🟢"
        value < 30 -> "🟡"
        else -> "🔴"
    }
}

/**
 * 术语解释
 */
data class TermExplanation(
    val term: String,
    val shortDescription: String,
    val fullExplanation: String,
    val example: String?,
    val howToUse: String?
)

/**
 * 术语库
 */
object TermDictionary {
    val terms = mapOf(
        "P/E" to TermExplanation(
            term = "P/E (市盈率)",
            shortDescription = "股价 / 每股收益",
            fullExplanation = "市盈率表示你愿意为公司每赚1美元付多少钱。P/E越高,说明市场对公司未来增长预期越高,但也可能意味着股价被高估。",
            example = "AMZN P/E = 34.9 意味着你为亚马逊每赚1美元付34.9美元",
            howToUse = "< 15: 便宜\n15-25: 合理\n25-40: 较贵\n> 40: 很贵"
        ),
        "52周" to TermExplanation(
            term = "52周位置",
            shortDescription = "当前价在过去一年高低点之间的位置",
            fullExplanation = "52周位置显示股价在过去一年最高价和最低价之间的相对位置。88%意味着接近一年高点,股价强势;36%意味着接近一年低点,股价弱势。",
            example = "AMZN 52周: 88% 表示接近一年最高点",
            howToUse = "0-20%: 接近底部\n20-40%: 偏低\n60-80%: 偏高\n80-100%: 接近顶部"
        ),
        "分析师" to TermExplanation(
            term = "分析师评级",
            shortDescription = "华尔街分析师的买入/持有/卖出建议",
            fullExplanation = "显示有多少华尔街分析师给出买入、持有、卖出评级。(73/4/0)表示73人说买入,4人说持有,0人说卖出。",
            example = "AMZN: 买入 (73/4/0) 表示绝大多数分析师看好",
            howToUse = "注意: 分析师很少说卖出(怕得罪公司),所以持有往往意味着不看好。"
        ),
        "目标价" to TermExplanation(
            term = "目标价空间",
            shortDescription = "分析师预测的股价 vs 当前价的差距",
            fullExplanation = "目标价是分析师对未来12个月股价的预测。目标价空间表示当前价距离目标价还有多少上涨/下跌空间。",
            example = "+19.2% 表示分析师认为还能涨19.2%",
            howToUse = "> +20%: 强烈看好\n+10% - +20%: 看好\n0% - +10%: 中性\n< 0%: 看空(当前价已超过目标价)"
        ),
        "VIX" to TermExplanation(
            term = "VIX 恐慌指数",
            shortDescription = "市场对未来30天波动的预期",
            fullExplanation = "VIX也叫恐慌指数,反映投资者对市场未来波动的预期。VIX越高,市场越恐慌。",
            example = "VIX = 14.2 表示市场情绪乐观,波动预期低",
            howToUse = "< 15: 极度乐观\n15-20: 正常\n20-30: 有些担忧\n30-40: 恐慌\n> 40: 极度恐慌"
        ),
        "因果链" to TermExplanation(
            term = "因果链分析",
            shortDescription = "事件影响股价的逻辑推理链",
            fullExplanation = "因果链用 A -> B -> C 的格式展示新闻事件如何一步步影响股价,帮助你理解背后的投资逻辑。",
            example = "DEI取消 -> 成本降低 -> 利润率提高 -> 股价上涨",
            howToUse = "关注每一步的逻辑是否合理,有没有被忽略的因素。"
        )
    )
}