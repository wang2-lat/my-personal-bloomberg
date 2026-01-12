# My Personal Bloomberg - Android App

一个专业级的个人金融终端 Android 应用，提供实时市场数据、新闻分析和 AI 驱动的投资洞察。

## 📱 功能特性

### 已实现
- ✅ 市场概览（S&P500, 纳指, 道指）
- ✅ VIX 恐慌指数显示
- ✅ 费城联储制造业指数
- ✅ 新闻卡片展示
- ✅ AI 深度分析（核心判断、因果链、估值视角）
- ✅ 分析师评级和目标价
- ✅ P/E、52周位置等关键指标
- ✅ **点击术语弹出解释**（P/E、52周、分析师、VIX 等）
- ✅ **卡片展开/收起动画**
- ✅ 深色主题（Bloomberg 风格）

### 待实现
- 📋 自选股关注列表
- 📋 推送通知
- 📋 股票搜索
- 📋 历史走势图表
- 📋 后端 API 集成

## 🛠️ 技术栈

- **语言**: Kotlin
- **UI**: Jetpack Compose + Material 3
- **架构**: MVVM
- **网络**: Retrofit + OkHttp
- **异步**: Kotlin Coroutines + Flow

## 📦 安装步骤

### 1. 安装 Android Studio

1. 访问 https://developer.android.com/studio
2. 下载 Android Studio（Mac 版本约 1GB）
3. 安装并打开
4. 首次启动会下载 Android SDK（约 3-5GB）

### 2. 打开项目

1. 打开 Android Studio
2. 选择 "Open" 或 "File > Open"
3. 选择 `my-personal-bloomberg-android` 文件夹
4. 等待 Gradle 同步完成（首次可能需要几分钟）

### 3. 运行应用

**方式一：使用模拟器**
1. 点击 "Device Manager"（右侧工具栏）
2. 创建一个虚拟设备（推荐 Pixel 6, API 34）
3. 点击绿色 Run 按钮 ▶️

**方式二：使用真机**
1. 手机打开 "开发者选项"
2. 开启 "USB 调试"
3. 用数据线连接电脑
4. 手机上点击 "允许 USB 调试"
5. 在 Android Studio 中选择你的设备
6. 点击 Run ▶️

## 📁 项目结构

```
app/src/main/java/com/jeremy/bloomberg/
├── MainActivity.kt           # 应用入口
├── model/
│   └── Models.kt             # 数据模型（股票、新闻、分析等）
├── data/
│   └── HomeViewModel.kt      # 状态管理
├── network/
│   └── ApiService.kt         # 网络请求 + 模拟数据
└── ui/
    ├── theme/
    │   └── Theme.kt          # Bloomberg 风格主题
    ├── components/
    │   ├── MarketOverviewCard.kt    # 市场概览卡片
    │   ├── NewsAnalysisCard.kt      # 新闻分析卡片
    │   └── TermExplanationDialog.kt # 术语解释弹窗
    └── screens/
        └── HomeScreen.kt     # 主页屏幕
```

## 🎨 界面预览

### 主要界面
- **市场概览**: 显示 S&P500、纳指、道指的实时涨跌
- **VIX 指标**: 点击可查看恐慌指数解释
- **新闻卡片**: 展示 AI 分析的新闻
  - 点击卡片展开详细分析
  - 点击 P/E、52周等指标查看解释

### 术语解释弹窗
点击任何金融术语（P/E、52周、分析师评级等），会弹出详细解释，包括：
- 定义和公式
- 举例说明
- 判断标准

## 🔧 自定义配置

### 修改 API 地址
编辑 `network/ApiService.kt`:
```kotlin
private const val BASE_URL = "https://your-api.vercel.app/api/"
```

### 添加新的术语解释
编辑 `model/Models.kt` 中的 `TermDictionary`:
```kotlin
"新术语" to TermExplanation(
    term = "术语名称",
    shortDescription = "简短描述",
    fullExplanation = "详细解释...",
    example = "举例...",
    howToUse = "判断标准..."
)
```

## 📱 Mac 开发者快捷键

| 功能 | 快捷键 |
|:-----|:------|
| 运行项目 | Ctrl + R |
| 停止运行 | Cmd + F2 |
| 格式化代码 | Cmd + Option + L |
| 查找文件 | Cmd + Shift + O |
| 全局搜索 | Cmd + Shift + F |

## 🚀 下一步计划

1. **部署后端 API** - 把 Python 代码改成 FastAPI 部署到 Vercel
2. **替换模拟数据** - 连接真实 API
3. **添加自选股** - 用户可以关注特定股票
4. **推送通知** - 重大新闻推送到手机

## 📄 License

MIT License - 仅供学习使用

---

Made with ❤️ by Jeremy | Powered by Citadel AI Engine
