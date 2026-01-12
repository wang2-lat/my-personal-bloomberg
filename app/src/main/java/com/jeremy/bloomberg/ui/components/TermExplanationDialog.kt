package com.jeremy.bloomberg.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.School
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.jeremy.bloomberg.model.TermExplanation
import com.jeremy.bloomberg.ui.theme.*

/**
 * 术语解释弹窗
 */
@Composable
fun TermExplanationDialog(
    explanation: TermExplanation,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .wrapContentHeight(),
            colors = CardDefaults.cardColors(
                containerColor = BloombergDarkGray
            ),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState())
            ) {
                // 标题行
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.School,
                            contentDescription = null,
                            tint = BloombergOrange,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = explanation.term,
                            style = MaterialTheme.typography.headlineSmall,
                            color = BloombergWhite,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    IconButton(onClick = onDismiss) {
                        Icon(
                            imageVector = Icons.Default.Close,
                            contentDescription = "关闭",
                            tint = BloombergGray
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // 简短描述
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(BloombergBlue.copy(alpha = 0.2f))
                        .padding(12.dp)
                ) {
                    Text(
                        text = explanation.shortDescription,
                        style = MaterialTheme.typography.titleMedium,
                        color = BloombergBlue,
                        fontWeight = FontWeight.SemiBold
                    )
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // 详细解释
                Text(
                    text = "📖 详细解释",
                    style = MaterialTheme.typography.labelLarge,
                    color = BloombergOrange,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = explanation.fullExplanation,
                    style = MaterialTheme.typography.bodyMedium,
                    color = BloombergWhite.copy(alpha = 0.9f),
                    lineHeight = 22.sp
                )
                
                // 示例
                explanation.example?.let { example ->
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "💡 举个例子",
                        style = MaterialTheme.typography.labelLarge,
                        color = BloombergGold,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(BloombergBlack)
                            .padding(12.dp)
                    ) {
                        Text(
                            text = example,
                            style = MaterialTheme.typography.bodyMedium,
                            color = BloombergGreen
                        )
                    }
                }
                
                // 使用方法
                explanation.howToUse?.let { howToUse ->
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "📊 判断标准",
                        style = MaterialTheme.typography.labelLarge,
                        color = BloombergBlue,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = howToUse,
                        style = MaterialTheme.typography.bodySmall,
                        color = BloombergWhite.copy(alpha = 0.8f),
                        lineHeight = 20.sp
                    )
                }
                
                Spacer(modifier = Modifier.height(20.dp))
                
                // 关闭按钮
                Button(
                    onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = BloombergOrange
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = "明白了 👍",
                        color = BloombergWhite,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
