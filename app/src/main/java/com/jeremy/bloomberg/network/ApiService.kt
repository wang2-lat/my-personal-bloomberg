package com.jeremy.bloomberg.network

import com.jeremy.bloomberg.model.*
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Query
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import java.util.concurrent.TimeUnit

/**
 * API 服务接口
 */
interface BloombergApiService {
    
    @GET("market-overview")
    suspend fun getMarketOverview(): MarketOverviewResponse
    
    @GET("news")
    suspend fun getNews(
        @Query("limit") limit: Int = 4
    ): NewsResponse
    
    @GET("stock")
    suspend fun getStockData(
        @Query("ticker") ticker: String
    ): StockDataResponse
    
    @GET("analyze")
    suspend fun analyzeNews(
        @Query("title") title: String,
        @Query("ticker") ticker: String
    ): AIAnalysisResponse
}

/**
 * API 响应数据类
 */
data class MarketOverviewResponse(
    val success: Boolean,
    val data: MarketOverview?
)

data class NewsResponse(
    val success: Boolean,
    val data: List<NewsCard>?
)

data class StockDataResponse(
    val success: Boolean,
    val quote: StockQuote?,
    val fundamentals: StockFundamentals?,
    val analyst: AnalystRating?
)

data class AIAnalysisResponse(
    val success: Boolean,
    val analysis: AIAnalysis?
)

/**
 * API 客户端单例
 */
object ApiClient {
    // TODO: 部署后端后替换为你的 API 地址
    private const val BASE_URL = "https://your-api.vercel.app/api/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val service: BloombergApiService = retrofit.create(BloombergApiService::class.java)
}

/**
 * 模拟数据提供者（在后端部署前使用）
 */
object MockDataProvider {
    
    fun getMarketOverview(): MarketOverview {
        return MarketOverview(
            timestamp = "2026-01-11 08:00 EST",
            indices = listOf(
                MarketIndex("SPY", "S&P500", 694.07, 4.56, 0.66),
                MarketIndex("QQQ", "纳指100", 512.34, 5.12, 1.00),
                MarketIndex("DIA", "道指", 425.67, 1.78, 0.42)
            ),
            vix = VixData(14.2, "低恐慌"),
            phillyFed = -8.8
        )
    }
    
    fun getNewsCards(): List<NewsCard> {
        return listOf(
            NewsCard(
                id = "1",
                title = "Amazon Willing to Discuss Quebec Shutdown",
                source = "WSJ",
                publishedAt = "2026-01-11",
                ticker = "AMZN",
                quote = StockQuote("AMZN", 247.38, 1.08, 0.44, 246.30),
                fundamentals = StockFundamentals(
                    ticker = "AMZN",
                    companyName = "Amazon.com Inc",
                    sector = "Technology",
                    pe = 34.9,
                    forwardPe = 28.5,
                    marketCap = 1580000000000,
                    week52High = 260.0,
                    week52Low = 180.0,
                    week52Position = 88.0,
                    beta = 1.15,
                    targetPrice = 295.0,
                    targetHigh = 320.0,
                    targetLow = 250.0,
                    upside = 19.2
                ),
                analyst = AnalystRating("AMZN", 73, 4, 0, "买入"),
                analysis = AIAnalysis(
                    score = 5,
                    signal = "中性",
                    coreJudgment = "Amazon积极沟通或缓解潜在监管风险，但影响程度有限，短期股价波动可能较小。",
                    causalChain = "魁北克关停风险 → Amazon主动沟通加拿大官员 → 降低监管不确定性，稳定运营预期 → 长期利好。",
                    valuationView = "P/E显著高于行业，目标价有上涨空间，部分乐观预期已Price In，但沟通进展仍需观察。",
                    risk = "沟通结果的不确定性，以及魁北克政府强硬态度，可能导致未来运营受阻。",
                    recommendation = "持有者可继续持有，观望者需关注沟通进展，确认风险可控后再考虑介入。"
                )
            ),
            NewsCard(
                id = "2",
                title = "Target Drops DEI Goals and Ends Program",
                source = "WSJ",
                publishedAt = "2026-01-11",
                ticker = "TGT",
                quote = StockQuote("TGT", 105.52, -0.81, -0.76, 106.33),
                fundamentals = StockFundamentals(
                    ticker = "TGT",
                    companyName = "Target Corporation",
                    sector = "Consumer Defensive",
                    pe = 12.8,
                    forwardPe = 11.5,
                    marketCap = 48000000000,
                    week52High = 165.0,
                    week52Low = 100.0,
                    week52Position = 36.0,
                    beta = 0.95,
                    targetPrice = 98.0,
                    targetHigh = 145.0,
                    targetLow = 85.0,
                    upside = -7.2
                ),
                analyst = AnalystRating("TGT", 14, 23, 6, "持有"),
                analysis = AIAnalysis(
                    score = 6,
                    signal = "中性",
                    coreJudgment = "中性偏利好。短期可能面临争议，长期看有利于降低运营成本，提升股东价值。",
                    causalChain = "DEI目标取消 → 减少供应商多样性相关成本 → 提高利润率 → 提升投资者信心。",
                    valuationView = "P/E较低且估值溢价较大，目标价下行空间有限，表明市场可能未充分price in。",
                    risk = "取消DEI可能引发消费者抵制和品牌声誉受损，影响短期销售额。",
                    recommendation = "持有者可继续持有，观察消费者反应。观望者可小仓位建仓，等待进一步消息。"
                )
            ),
            NewsCard(
                id = "3",
                title = "Wall Street Banks Prepare to Sell Billions in X Loans",
                source = "WSJ",
                publishedAt = "2026-01-11",
                ticker = "SPY",
                quote = StockQuote("SPY", 694.07, 4.56, 0.66, 689.51),
                fundamentals = StockFundamentals(
                    ticker = "SPY",
                    companyName = "SPDR S&P 500 ETF",
                    sector = "ETF",
                    pe = 28.1,
                    forwardPe = 24.5,
                    marketCap = null,
                    week52High = 700.0,
                    week52Low = 520.0,
                    week52Position = 99.0,
                    beta = 1.0,
                    targetPrice = null,
                    targetHigh = null,
                    targetLow = null,
                    upside = null
                ),
                analyst = null,
                analysis = AIAnalysis(
                    score = 4,
                    signal = "利空",
                    coreJudgment = "华尔街银行出售X贷款的消息可能导致市场担忧信贷风险上升。",
                    causalChain = "银行抛售贷款 → 流动性压力或信贷风险信号 → 市场担忧情绪上升 → 短期承压。",
                    valuationView = "SPY估值溢价较高，此类消息或加剧市场对经济增长的担忧，但短期内已部分Price In。",
                    risk = "贷款抛售规模未知，可能引发更广泛的信贷担忧。",
                    recommendation = "持有者关注宏观经济数据，谨慎持有；观望者可等待市场调整，再择机入场。"
                )
            ),
            NewsCard(
                id = "4",
                title = "Canada to Provide $720 Million to Canada Post",
                source = "WSJ",
                publishedAt = "2026-01-11",
                ticker = "SPY",
                quote = StockQuote("SPY", 694.07, 4.56, 0.66, 689.51),
                fundamentals = StockFundamentals(
                    ticker = "SPY",
                    companyName = "SPDR S&P 500 ETF",
                    sector = "ETF",
                    pe = 28.1,
                    forwardPe = 24.5,
                    marketCap = null,
                    week52High = 700.0,
                    week52Low = 520.0,
                    week52Position = 99.0,
                    beta = 1.0,
                    targetPrice = null,
                    targetHigh = null,
                    targetLow = null,
                    upside = null
                ),
                analyst = null,
                analysis = AIAnalysis(
                    score = 4,
                    signal = "利空",
                    coreJudgment = "加拿大政府救助加拿大邮政，短期避免破产，长期对SPY影响中性偏负面，但幅度有限。",
                    causalChain = "加拿大邮政经营不善 → 政府注资避免破产 → 增加政府财政负担 → 可能影响整体经济增长和市场情绪。",
                    valuationView = "SPY估值溢价较高，此类消息或加剧市场对经济增长的担忧，但短期内已部分Price In。",
                    risk = "加拿大邮政问题可能只是冰山一角，更广泛的经济问题或浮出水面。",
                    recommendation = "持有者关注宏观经济数据，谨慎持有；观望者可等待市场调整，再择机入场。"
                )
            )
        )
    }
}
