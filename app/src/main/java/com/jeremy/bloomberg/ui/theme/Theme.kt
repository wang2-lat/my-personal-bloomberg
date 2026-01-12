package com.jeremy.bloomberg.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle

// Bloomberg 风格颜色
val BloombergBlack = Color(0xFF1A1A1A)
val BloombergDarkGray = Color(0xFF2D2D2D)
val BloombergOrange = Color(0xFFFF6B35)
val BloombergGreen = Color(0xFF4CAF50)
val BloombergRed = Color(0xFFF44336)
val BloombergBlue = Color(0xFF2196F3)
val BloombergGold = Color(0xFFFFD700)
val BloombergWhite = Color(0xFFFFFFFF)
val BloombergGray = Color(0xFF9E9E9E)

private val DarkColorScheme = darkColorScheme(
    primary = BloombergOrange,
    secondary = BloombergBlue,
    tertiary = BloombergGold,
    background = BloombergBlack,
    surface = BloombergDarkGray,
    onPrimary = BloombergWhite,
    onSecondary = BloombergWhite,
    onTertiary = BloombergBlack,
    onBackground = BloombergWhite,
    onSurface = BloombergWhite,
)

private val LightColorScheme = lightColorScheme(
    primary = BloombergOrange,
    secondary = BloombergBlue,
    tertiary = BloombergGold,
    background = Color(0xFFF5F5F5),
    surface = BloombergWhite,
    onPrimary = BloombergWhite,
    onSecondary = BloombergWhite,
    onTertiary = BloombergBlack,
    onBackground = BloombergBlack,
    onSurface = BloombergBlack,
)

val BloombergTypography = Typography(
    headlineLarge = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 28.sp,
        lineHeight = 36.sp
    ),
    headlineMedium = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 22.sp,
        lineHeight = 28.sp
    ),
    headlineSmall = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 18.sp,
        lineHeight = 24.sp
    ),
    titleLarge = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 16.sp,
        lineHeight = 22.sp
    ),
    titleMedium = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp
    ),
    bodyLarge = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp
    ),
    bodyMedium = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp
    ),
    bodySmall = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 16.sp
    ),
    labelLarge = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp
    ),
    labelMedium = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp
    ),
    labelSmall = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 10.sp,
        lineHeight = 14.sp
    )
)

@Composable
fun MyPersonalBloombergTheme(
    darkTheme: Boolean = true,  // 默认深色主题（Bloomberg 风格）
    dynamicColor: Boolean = false,  // 不使用动态颜色，保持 Bloomberg 风格
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = BloombergTypography,
        content = content
    )
}
