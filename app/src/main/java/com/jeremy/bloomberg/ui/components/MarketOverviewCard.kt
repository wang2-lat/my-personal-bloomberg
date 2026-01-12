package com.jeremy.bloomberg.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.jeremy.bloomberg.model.*
import com.jeremy.bloomberg.ui.theme.*

/**
 * 市场概览卡片
 */
@Composable
fun MarketOverviewCard(
    marketOverview: MarketOverview,
    onVixClick: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = BloombergBlue.copy(alpha = 0.15f)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // 标题行
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "🏛",
                    fontSize = 20.sp
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "市场脉搏",
                    style = MaterialTheme.typography.headlineSmall,
                    color = BloombergWhite
                )
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    text = marketOverview.timestamp,
                    style = MaterialTheme.typography.bodySmall,
                    color = BloombergGray
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 指数行
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                marketOverview.indices.forEach { index ->
                    IndexChip(index = index)
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // VIX 和费城联储行
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // VIX
                marketOverview.vix?.let { vix ->
                    Row(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .clickable { onVixClick() }
                            .background(BloombergDarkGray)
                            .padding(horizontal = 12.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = vix.emoji, fontSize = 14.sp)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "VIX",
                            style = MaterialTheme.typography.labelMedium,
                            color = BloombergGray
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = String.format("%.1f", vix.value),
                            style = MaterialTheme.typography.labelMedium,
                            color = BloombergWhite,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "(${vix.level})",
                            style = MaterialTheme.typography.labelSmall,
                            color = BloombergGray
                        )
                    }
                }
                
                // 费城联储
                marketOverview.phillyFed?.let { fed ->
                    Row(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(BloombergDarkGray)
                            .padding(horizontal = 12.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = if (fed > 0) "🟢" else "🔴",
                            fontSize = 14.sp
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "费城联储",
                            style = MaterialTheme.typography.labelMedium,
                            color = BloombergGray
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = String.format("%.1f", fed),
                            style = MaterialTheme.typography.labelMedium,
                            color = if (fed > 0) BloombergGreen else BloombergRed,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

/**
 * 单个指数芯片
 */
@Composable
fun IndexChip(
    index: MarketIndex,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(BloombergDarkGray)
            .padding(horizontal = 12.dp, vertical = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = index.emoji,
            fontSize = 16.sp
        )
        Text(
            text = index.name,
            style = MaterialTheme.typography.labelSmall,
            color = BloombergGray
        )
        Text(
            text = String.format("%+.2f%%", index.changePercent),
            style = MaterialTheme.typography.labelMedium,
            color = if (index.isPositive) BloombergGreen else BloombergRed,
            fontWeight = FontWeight.Bold
        )
    }
}
