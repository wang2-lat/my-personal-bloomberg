package com.jeremy.bloomberg.data

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.jeremy.bloomberg.model.*
import com.jeremy.bloomberg.network.MockDataProvider
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

/**
 * 主页 UI 状态
 */
data class HomeUiState(
    val isLoading: Boolean = true,
    val marketOverview: MarketOverview? = null,
    val newsCards: List<NewsCard> = emptyList(),
    val error: String? = null,
    val selectedTerm: TermExplanation? = null,  // 当前选中要解释的术语
    val expandedCardId: String? = null  // 当前展开的卡片 ID
)

/**
 * 主页 ViewModel
 */
class HomeViewModel : ViewModel() {
    
    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()
    
    init {
        loadData()
    }
    
    /**
     * 加载数据
     */
    fun loadData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            
            try {
                // 模拟网络延迟
                delay(500)
                
                // 使用模拟数据（后期替换为真实 API 调用）
                val marketOverview = MockDataProvider.getMarketOverview()
                val newsCards = MockDataProvider.getNewsCards()
                
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    marketOverview = marketOverview,
                    newsCards = newsCards
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "加载失败: ${e.message}"
                )
            }
        }
    }
    
    /**
     * 刷新数据
     */
    fun refresh() {
        loadData()
    }
    
    /**
     * 展开/收起卡片
     */
    fun toggleCardExpansion(cardId: String) {
        _uiState.value = _uiState.value.copy(
            expandedCardId = if (_uiState.value.expandedCardId == cardId) null else cardId
        )
    }
    
    /**
     * 显示术语解释
     */
    fun showTermExplanation(term: String) {
        val explanation = TermDictionary.terms[term]
        _uiState.value = _uiState.value.copy(selectedTerm = explanation)
    }
    
    /**
     * 关闭术语解释弹窗
     */
    fun dismissTermExplanation() {
        _uiState.value = _uiState.value.copy(selectedTerm = null)
    }
}
