# 给下一位开发者的提示词

复制以下内容发给 Claude 或 GPT：

---

你是一个 Android 开发专家，精通 Kotlin 和 Jetpack Compose，同时也熟悉 Python 后端开发。

我有一个名为 "My Personal Bloomberg" 的金融资讯项目，需要你帮我继续开发。

## 项目当前状态

### 已完成
- Android App 基础 UI（Jetpack Compose + Material 3）
- 市场概览卡片（SPY/QQQ/DIA/VIX）
- 新闻分析卡片（展开/收起动画）
- 术语解释弹窗（P/E、52周、分析师等）
- 深色主题（Bloomberg 风格）
- 飞书机器人（每天自动推送，已部署）

### 未完成
- Android App 使用模拟数据，没有连接真实 API
- 没有后端 API 服务
- UI 比较简陋，缺乏科幻感

## 我需要你帮我完成以下任务

### 任务 1：部署后端 API（优先级：高）
- 使用 Python FastAPI 创建后端
- 集成 Finnhub API（股票实时数据）
- 集成 yfinance（基本面数据）
- 集成 Gemini AI（新闻分析）
- 部署到 Vercel（免费）
- 提供以下接口：
  - GET /api/market-overview（市场概览）
  - GET /api/news（新闻+AI分析）
  - GET /api/stock/{ticker}（单只股票数据）

### 任务 2：Android App 连接后端（优先级：高）
- 修改 ApiService.kt 连接真实 API
- 实现下拉刷新功能
- 添加加载状态和错误处理
- App 启动时自动获取最新数据

### 任务 3：UI 科幻美化（优先级：中）
- 添加渐变背景（深蓝色调，如 #0D1B2A → #1B263B）
- 添加霓虹发光边框效果（青色/蓝色渐变）
- 添加动画效果：
  - 数字滚动动画（股价变化时）
  - 卡片进入动画（从底部滑入）
  - 加载脉冲动画
- 添加背景扫描线效果
- 参考风格：Bloomberg Terminal + Cyberpunk 2077 + Iron Man JARVIS

## 项目技术栈

### Android App
- 语言：Kotlin
- UI：Jetpack Compose + Material 3
- 架构：MVVM
- 网络：Retrofit + OkHttp
- 异步：Kotlin Coroutines + Flow

### 后端
- 语言：Python 3.10
- 框架：FastAPI
- 数据源：Finnhub, yfinance, FRED
- AI：Google Gemini 2.0 Flash
- 部署：Vercel

## API Keys（已有）
- FINNHUB_KEY：股票实时数据
- GEMINI_KEY：AI 分析
- FRED_KEY：宏观经济数据
- ALPHA_VANTAGE_KEY：公司基本面

## 项目文件说明

### Android App 关键文件
- `ApiService.kt`：API 接口定义 + 模拟数据（需要改成真实 API）
- `HomeViewModel.kt`：状态管理
- `HomeScreen.kt`：主页 UI
- `NewsAnalysisCard.kt`：新闻卡片组件
- `Theme.kt`：主题配色（需要美化）

### 后端模板文件
- `api_template.py`：FastAPI 后端模板（需要完善）
- `vercel.json`：Vercel 部署配置
- `requirements.txt`：Python 依赖

## 请你做以下事情

1. 先阅读项目代码，理解现有架构
2. 告诉我你的开发计划和时间估算
3. 按优先级顺序完成任务
4. 每完成一个任务，告诉我如何测试

## 补充信息

- 项目 GitHub：wang2-lat/my-personal-bloomberg
- 飞书机器人已经在运行，代码在 push_telegram.py
- 可以参考飞书机器人的代码来实现后端 API

---

开始吧！请先告诉我你理解了项目需求，然后给出开发计划。
