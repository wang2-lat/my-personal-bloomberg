package com.jeremy.bloomberg.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.jeremy.bloomberg.data.HomeViewModel
import com.jeremy.bloomberg.ui.components.*
import com.jeremy.bloomberg.ui.theme.*

/**
 * 主页屏幕
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: HomeViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "🏛",
                            style = MaterialTheme.typography.headlineMedium
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Column {
                            Text(
                                text = "My Personal Bloomberg",
                                style = MaterialTheme.typography.titleLarge,
                                color = BloombergWhite,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "Citadel AI Engine",
                                style = MaterialTheme.typography.labelSmall,
                                color = BloombergGray
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "刷新",
                            tint = BloombergOrange
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = BloombergBlack
                )
            )
        },
        containerColor = BloombergBlack
    ) { paddingValues ->
        
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            when {
                uiState.isLoading -> {
                    // 加载中
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        CircularProgressIndicator(color = BloombergOrange)
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "正在获取市场数据...",
                            color = BloombergGray
                        )
                    }
                }
                
                uiState.error != null -> {
                    // 错误状态
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "😕",
                            style = MaterialTheme.typography.headlineLarge
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = uiState.error!!,
                            color = BloombergRed
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(
                            onClick = { viewModel.refresh() },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = BloombergOrange
                            )
                        ) {
                            Text("重试")
                        }
                    }
                }
                
                else -> {
                    // 正常显示内容
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        // 市场概览卡片
                        uiState.marketOverview?.let { overview ->
                            item {
                                MarketOverviewCard(
                                    marketOverview = overview,
                                    onVixClick = { viewModel.showTermExplanation("VIX") }
                                )
                            }
                        }
                        
                        // 新闻标题
                        item {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "📰",
                                    style = MaterialTheme.typography.titleLarge
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = "今日新闻分析",
                                    style = MaterialTheme.typography.titleLarge,
                                    color = BloombergWhite,
                                    fontWeight = FontWeight.Bold
                                )
                                Spacer(modifier = Modifier.weight(1f))
                                Text(
                                    text = "${uiState.newsCards.size} 条",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = BloombergGray
                                )
                            }
                        }
                        
                        // 新闻卡片列表
                        items(uiState.newsCards) { newsCard ->
                            NewsAnalysisCard(
                                newsCard = newsCard,
                                isExpanded = uiState.expandedCardId == newsCard.id,
                                onToggleExpand = { viewModel.toggleCardExpansion(newsCard.id) },
                                onTermClick = { term -> viewModel.showTermExplanation(term) }
                            )
                        }
                        
                        // 底部说明
                        item {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "💡 点击指标可查看解释 | 点击卡片展开详情",
                                style = MaterialTheme.typography.labelSmall,
                                color = BloombergGray,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }
            }
            
            // 术语解释弹窗
            uiState.selectedTerm?.let { term ->
                TermExplanationDialog(
                    explanation = term,
                    onDismiss = { viewModel.dismissTermExplanation() }
                )
            }
        }
    }
}
