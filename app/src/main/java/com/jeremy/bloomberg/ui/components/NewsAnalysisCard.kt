package com.jeremy.bloomberg.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.jeremy.bloomberg.model.*
import com.jeremy.bloomberg.ui.theme.*

@Composable
fun NewsAnalysisCard(
    newsCard: NewsCard,
    isExpanded: Boolean,
    onToggleExpand: () -> Unit,
    onTermClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val headerColor = Color(newsCard.analysis.color)

    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = BloombergDarkGray),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(headerColor)
                    .clickable { onToggleExpand() }
                    .padding(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = newsCard.analysis.emoji, fontSize = 18.sp)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = newsCard.title,
                        style = MaterialTheme.typography.titleMedium,
                        color = BloombergWhite,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )
                    Icon(
                        imageVector = if (isExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                        contentDescription = "展开",
                        tint = BloombergWhite
                    )
                }
            }

            Column(modifier = Modifier.padding(12.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = newsCard.ticker,
                            style = MaterialTheme.typography.titleLarge,
                            color = BloombergOrange,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        newsCard.quote?.let { quote ->
                            Text(
                                text = "$${String.format("%.2f", quote.price)}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = BloombergWhite
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "(${String.format("%+.2f%%", quote.changePercent)})",
                                style = MaterialTheme.typography.bodyMedium,
                                color = if (quote.change >= 0) BloombergGreen else BloombergRed
                            )
                        }
                    }

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        newsCard.fundamentals?.pe?.let { pe ->
                            ClickableMetric(label = "P/E", value = String.format("%.1f", pe), onClick = { onTermClick("P/E") })
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        newsCard.fundamentals?.week52Position?.let { pos ->
                            ClickableMetric(label = "52周", value = "${pos.toInt()}%", onClick = { onTermClick("52周") })
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    newsCard.analyst?.let { analyst ->
                        ClickableMetric(label = "分析师", value = analyst.displayText, onClick = { onTermClick("分析师") })
                    } ?: Text(text = "分析师: --", style = MaterialTheme.typography.bodySmall, color = BloombergGray)

                    newsCard.fundamentals?.upside?.let { upside ->
                        ClickableMetric(
                            label = "目标价",
                            value = String.format("%+.1f%%", upside),
                            valueColor = if (upside >= 0) BloombergGreen else BloombergRed,
                            onClick = { onTermClick("目标价") }
                        )
                    } ?: Text(text = "目标价: --", style = MaterialTheme.typography.bodySmall, color = BloombergGray)
                }
            }

            AnimatedVisibility(visible = isExpanded, enter = expandVertically(), exit = shrinkVertically()) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp)
                        .padding(bottom = 12.dp)
                ) {
                    Divider(color = BloombergGray.copy(alpha = 0.3f), thickness = 1.dp)
                    Spacer(modifier = Modifier.height(12.dp))

                    AnalysisSection(icon = "🎯", title = "核心判断", content = newsCard.analysis.coreJudgment)
                    Spacer(modifier = Modifier.height(12.dp))
                    AnalysisSection(icon = "🔗", title = "因果链", content = newsCard.analysis.causalChain, onClick = { onTermClick("因果链") })
                    Spacer(modifier = Modifier.height(12.dp))
                    AnalysisSection(icon = "💰", title = "估值视角", content = newsCard.analysis.valuationView)
                    Spacer(modifier = Modifier.height(12.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Column(modifier = Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(text = "⚠️", fontSize = 14.sp)
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "风险", style = MaterialTheme.typography.labelLarge, color = BloombergOrange, fontWeight = FontWeight.Bold)
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(text = newsCard.analysis.risk, style = MaterialTheme.typography.bodySmall, color = BloombergWhite.copy(alpha = 0.9f))
                        }

                        Column(modifier = Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(text = "💡", fontSize = 14.sp)
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "建议", style = MaterialTheme.typography.labelLarge, color = BloombergGold, fontWeight = FontWeight.Bold)
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(text = newsCard.analysis.recommendation, style = MaterialTheme.typography.bodySmall, color = BloombergWhite.copy(alpha = 0.9f))
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))
                    Divider(color = BloombergGray.copy(alpha = 0.3f), thickness = 1.dp)
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                        Text(text = "评分 ${newsCard.analysis.score}/10 | ${newsCard.analysis.signal}", style = MaterialTheme.typography.labelSmall, color = BloombergGray)
                        Text(text = "${newsCard.source} | Citadel AI", style = MaterialTheme.typography.labelSmall, color = BloombergGray)
                    }
                }
            }
        }
    }
}

@Composable
fun ClickableMetric(label: String, value: String, valueColor: Color = BloombergWhite, onClick: () -> Unit) {
    Row(
        modifier = Modifier.clip(RoundedCornerShape(4.dp)).clickable { onClick() }.padding(4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, style = MaterialTheme.typography.bodySmall, color = BloombergGray)
        Spacer(modifier = Modifier.width(4.dp))
        Text(text = value, style = MaterialTheme.typography.bodySmall, color = valueColor, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.width(2.dp))
        Icon(imageVector = Icons.Default.Info, contentDescription = "解释", tint = BloombergGray, modifier = Modifier.size(12.dp))
    }
}

@Composable
fun AnalysisSection(icon: String, title: String, content: String, onClick: (() -> Unit)? = null) {
    Column {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = if (onClick != null) Modifier.clickable { onClick() } else Modifier
        ) {
            Text(text = icon, fontSize = 14.sp)
            Spacer(modifier = Modifier.width(4.dp))
            Text(text = title, style = MaterialTheme.typography.labelLarge, color = BloombergBlue, fontWeight = FontWeight.Bold)
            if (onClick != null) {
                Spacer(modifier = Modifier.width(4.dp))
                Icon(imageVector = Icons.Default.Info, contentDescription = "解释", tint = BloombergGray, modifier = Modifier.size(14.dp))
            }
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(text = content, style = MaterialTheme.typography.bodyMedium, color = BloombergWhite.copy(alpha = 0.9f), lineHeight = 20.sp)
    }
}