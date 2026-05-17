<template>
  <div class="idic-app">
    <el-container class="main-container">
      <!-- 顶部菜单栏 -->
      <div class="menu-bar">
        <div class="menu-item" @click="showConfig = true">
          <el-icon><Setting /></el-icon>
          <span>模型配置</span>
        </div>
        <div class="menu-item" @click="showSettings = true">
          <el-icon><Tools /></el-icon>
          <span>设置</span>
        </div>
        <div class="menu-item" @click="showWordbook = true">
          <el-icon><Star /></el-icon>
          <span>生词本</span>
        </div>
        <div class="menu-item" @click="showAbout = true">
          <el-icon><InfoFilled /></el-icon>
          <span>关于</span>
        </div>
      </div>
      
      <!-- 头部搜索栏 -->
      <el-header class="header">
        <div class="header-content">
          <div class="logo">
            <el-icon><Reading /></el-icon>
            <span>iDic</span>
          </div>
          
          <div class="search-section">
            <el-radio-group v-model="direction" size="large">
              <el-radio-button value="en2zh">英 → 中</el-radio-button>
              <el-radio-button value="zh2en">中 → 英</el-radio-button>
            </el-radio-group>
            
            <div class="search-input-wrapper">
                <el-input
                  v-model="searchText"
                  size="large"
                  placeholder="请输入要查询的单词或句子"
                  @keyup.enter="handleSearch"
                  @focus="onInputFocus"
                  @blur="hideHistory"
                  @input="onInputChange"
                  class="search-input"
                  clearable>
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                
                <!-- 单词建议下拉 -->
                <div v-if="showSuggestions && suggestions.length > 0" class="suggestions-dropdown">
                    <div v-for="(word, index) in suggestions" :key="index" 
                         class="suggestion-item" @mousedown.prevent="selectSuggestion(word)">
                        {{ word }}
                    </div>
                </div>

                <!-- 历史记录下拉 -->
                <div v-if="showHistory && queryHistory.length > 0 && !showSuggestions" class="history-dropdown">
                    <div v-for="(item, index) in queryHistory" :key="index" 
                         class="history-item" @click="selectFromHistory(item)">
                        <div class="history-word">{{ item.word }}</div>
                        <div class="history-time">{{ item.timestamp }}</div>
                    </div>
                </div>
            </div>
            
            <el-button type="primary" size="large" @click="handleSearch" :loading="loading">
              查询
            </el-button>
          </div>
          
          <div class="options">
            <el-checkbox v-model="useDict">本地词典</el-checkbox>
            <el-checkbox v-model="useAI">AI 解析</el-checkbox>
            <el-select
              v-model="currentModelId"
              placeholder="选择模型"
              size="default"
              class="model-select"
              @change="switchModel"
            >
              <el-option
                v-for="m in modelList"
                :key="m.id"
                :label="m.name"
                :value="m.id"
              />
            </el-select>
          </div>
        </div>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main class="main-content">
        <div v-if="currentWord" class="word-header">
          <h1 class="word-title">{{ currentWord }}</h1>
          <div class="word-actions">
            <el-button @click="handlePronounce">
              <el-icon><Microphone /></el-icon>发音
            </el-button>
            <el-button type="success" @click="addToWordbook">
              <el-icon><Star /></el-icon>收藏
            </el-button>
          </div>
        </div>
        
        <el-row :gutter="20" class="result-row">
          <!-- 本地词典结果 -->
          <el-col :span="useAI ? 12 : 24" v-if="useDict">
            <el-card class="result-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Document /></el-icon>
                  词典释义
                </div>
              </template>
              <div v-html="dictResult" class="dict-content"></div>
            </el-card>
          </el-col>
          
          <!-- AI 解析结果 -->
          <el-col :span="useDict ? 12 : 24" v-if="useAI">
            <el-card class="result-card">
                <template #header>
                    <div class="card-header">
                        <div class="card-header-left">
                            <el-icon><MagicStick /></el-icon>
                            AI 解析
                            <span v-if="aiLoading" class="ai-loading-info">
                              正在加载中 {{ aiElapsed }}s
                            </span>
                            <span v-else-if="aiStats" class="ai-stats-info">
                              {{ aiStats }}
                            </span>
                        </div>
                        <el-button
                          v-if="currentWord && !aiLoading"
                          size="small"
                          type="primary"
                          link
                          @click="reAnalyze"
                        >重新解析</el-button>
                    </div>
                </template>
                <div class="ai-content">
                    <div v-html="aiResultHtml" class="ai-result markdown-body"></div>
                </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
    
    <!-- 模型配置对话框 -->
    <el-dialog v-model="showConfig" title="模型配置" width="700px" @open="loadModels">
      <div class="model-manager">
        <div class="model-list-section">
          <div class="model-list-header">
            <span class="model-list-title">已添加的模型</span>
            <el-button type="primary" size="small" @click="addNewModel">
              <el-icon><Plus /></el-icon>添加模型
            </el-button>
          </div>
          <div v-if="modelList.length === 0" class="model-empty">
            暂无模型，请点击"添加模型"按钮
          </div>
          <div v-else class="model-list">
            <div
              v-for="m in modelList"
              :key="m.id"
              :class="['model-item', { 'model-item-active': m.id === currentModelId }]"
              @click="selectModelForEdit(m)"
            >
              <div class="model-item-info">
                <span class="model-item-name">{{ m.name }}</span>
                <span class="model-item-detail">{{ m.modelName }}</span>
              </div>
              <div class="model-item-actions">
                <el-tag v-if="m.id === currentModelId" size="small" type="success">默认</el-tag>
                <el-button
                  v-else
                  size="small"
                  type="primary"
                  link
                  @click.stop="setDefaultModel(m.id)"
                >设为默认</el-button>
                <el-button
                  size="small"
                  type="danger"
                  link
                  @click.stop="deleteModel(m.id)"
                >删除</el-button>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div v-if="editingModel" class="model-edit-section">
          <h4 class="edit-title">{{ isNewModel ? '添加新模型' : '编辑模型' }}</h4>
          <el-form :model="editingModel" label-width="110px" size="default">
            <el-form-item label="配置名称">
              <el-input v-model="editingModel.name" placeholder="如: 豆包、DeepSeek、NVIDIA" />
            </el-form-item>
            <el-form-item label="模型名称">
              <el-input v-model="editingModel.modelName" placeholder="如: doubao-pro-32k 或 z-ai/glm-5.1" />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input v-model="editingModel.apiKey" placeholder="请输入您的 API Key" type="password" show-password />
            </el-form-item>
            <el-form-item label="API Base URL">
              <el-input v-model="editingModel.apiBase" placeholder="如: https://ark.cn-beijing.volces.com/api/v3" />
            </el-form-item>
            <el-form-item label="超时时间(秒)">
              <el-input-number v-model="editingModel.timeout" :min="10" :max="300" :step="10" />
            </el-form-item>
            <el-form-item label="测试连接">
              <el-button type="warning" @click="testModelConfig" :loading="testLoading">
                发送测试：你是什么大模型
              </el-button>
            </el-form-item>
            <el-form-item v-if="testResult" label="测试结果">
              <el-alert
                :title="testSuccess ? '连接成功' + (testTime ? '  测试时间: ' + testTime : '') : '连接失败' + (testTime ? '  测试时间: ' + testTime : '')"
                :type="testSuccess ? 'success' : 'error'"
                :closable="false"
                show-icon
              />
              <div class="test-result-box">{{ testResult }}</div>
            </el-form-item>
          </el-form>
          <div class="edit-actions">
            <el-button @click="editingModel = null">取消</el-button>
            <el-button type="primary" @click="saveEditingModel">保存</el-button>
          </div>
        </div>
        <div v-else class="model-edit-placeholder">
          点击左侧模型编辑，或点击"添加模型"
        </div>
      </div>
    </el-dialog>
    
    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="设置" width="550px">
      <el-form :model="settingsForm" label-width="120px">
        <el-form-item label="字体大小">
          <el-slider v-model="settingsForm.fontSize" :min="12" :max="24" />
        </el-form-item>
        <el-form-item label="自动发音">
          <el-switch v-model="settingsForm.autoPronounce" />
        </el-form-item>
        <el-form-item label="关闭时隐藏">
          <el-switch v-model="settingsForm.minimizeToTray" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px;">开启后关闭窗口将隐藏到系统托盘</span>
        </el-form-item>
      </el-form>

      <el-divider content-position="left">网络代理</el-divider>
      <el-form :model="proxyForm" label-width="120px">
        <el-form-item label="启用代理">
          <el-switch v-model="proxyForm.proxyEnabled" />
        </el-form-item>
        <el-form-item label="代理地址">
          <el-input 
            v-model="proxyForm.proxyHost" 
            placeholder="如: 127.0.0.1" 
            :disabled="!proxyForm.proxyEnabled" 
          />
        </el-form-item>
        <el-form-item label="代理端口">
          <el-input-number 
            v-model="proxyForm.proxyPort" 
            :min="1" 
            :max="65535" 
            :disabled="!proxyForm.proxyEnabled"
            placeholder="如: 7890"
          />
        </el-form-item>
        <el-form-item v-if="proxyForm.proxyEnabled && proxyForm.proxyHost && proxyForm.proxyPort">
          <el-tag type="info">
            代理地址: http://{{ proxyForm.proxyHost }}:{{ proxyForm.proxyPort }}
          </el-tag>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- 生词本对话框 -->
    <el-dialog v-model="showWordbook" title="生词本" width="700px">
      <el-table :data="wordbook" stripe style="width: 100%">
        <el-table-column prop="word" label="单词" width="200">
          <template #default="{ row }">
            <span style="cursor: pointer; color: #409EFF; text-decoration: underline;" @click="queryFromWordbook(row.word)">
              {{ row.word }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="添加时间" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="removeFromWordbook(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    
    <!-- 关于对话框 -->
    <el-dialog v-model="showAbout" title="关于 iDic" width="400px">
      <div style="text-align: center; padding: 20px;">
        <h2 style="color: #409EFF;">iDic - 智能词典</h2>
        <p>版本: {{ appVersion }}</p>
        <p>一款基于 Vue 3 + Electron 的现代化词典软件</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { 
  Reading, 
  Search, 
  Document, 
  MagicStick, 
  Star, 
  Microphone,
  Setting,
  Tools,
  InfoFilled,
  Plus
} from '@element-plus/icons-vue'

const API_BASE = 'http://localhost:8000'

const md = MarkdownIt({
    html: true,
    linkify: true,
    breaks: true
})

const direction = ref('en2zh')
const searchText = ref('')
const useDict = ref(true)
const useAI = ref(true)
const loading = ref(false)
const aiLoading = ref(false)
const aiElapsed = ref(0)
const aiStats = ref('')
let aiTimer = null
let aiStartTime = 0
let aiTokenCount = 0
const currentWord = ref('')
const dictResult = ref('')
const aiResult = ref('')

const showConfig = ref(false)
const testLoading = ref(false)
const testResult = ref('')
const testSuccess = ref(false)
const testTime = ref('')
const showSettings = ref(false)
const showWordbook = ref(false)
const showAbout = ref(false)
const appVersion = ref('1.2.0')
const showSuggestions = ref(false)
const suggestions = ref([])
let suggestTimer = null

const modelList = ref([])
const currentModelId = ref('')
const editingModel = ref(null)
const isNewModel = ref(false)

const settingsForm = ref({
  fontSize: 16,
  autoPronounce: false,
  minimizeToTray: false
})

const proxyForm = ref({
  proxyEnabled: false,
  proxyHost: '',
  proxyPort: 7890
})

const wordbook = ref([])
const queryHistory = ref([])
const showHistory = ref(false)

const loadModels = async () => {
    try {
        const res = await axios.get(`${API_BASE}/models`)
        modelList.value = res.data.models
        currentModelId.value = res.data.activeModelId
    } catch (e) {
        console.error('加载模型列表失败:', e)
    }
}

const addNewModel = () => {
    isNewModel.value = true
    editingModel.value = {
        name: '',
        modelName: '',
        apiKey: '',
        apiBase: '',
        timeout: 60,
        testResult: '',
        testSuccess: false,
        testTime: ''
    }
    testResult.value = ''
    testSuccess.value = false
    testTime.value = ''
}

const selectModelForEdit = (m) => {
    isNewModel.value = false
    editingModel.value = { ...m }
    testResult.value = m.testResult || ''
    testSuccess.value = m.testSuccess || false
    testTime.value = m.testTime || ''
}

const saveEditingModel = async () => {
    if (!editingModel.value.name && !editingModel.value.modelName) {
        ElMessage.warning('请填写配置名称或模型名称')
        return
    }
    try {
        if (isNewModel.value) {
            const res = await axios.post(`${API_BASE}/models`, editingModel.value)
            if (res.data.success) {
                ElMessage.success('模型已添加')
            } else {
                ElMessage.error(res.data.message)
                return
            }
        } else {
            const res = await axios.put(`${API_BASE}/models/${editingModel.value.id}`, editingModel.value)
            if (res.data.success) {
                ElMessage.success('模型已更新')
            } else {
                ElMessage.error(res.data.message)
                return
            }
        }
        editingModel.value = null
        showConfig.value = false
        await loadModels()
    } catch (err) {
        ElMessage.error('保存失败: ' + (err.response?.data?.message || err.message))
    }
}

const deleteModel = async (id) => {
    try {
        await ElMessageBox.confirm('确定要删除该模型配置吗？', '确认删除', {
            type: 'warning'
        })
    } catch {
        return
    }
    try {
        const res = await axios.delete(`${API_BASE}/models/${id}`)
        if (res.data.success) {
            ElMessage.success('模型已删除')
            if (editingModel.value && editingModel.value.id === id) {
                editingModel.value = null
            }
            await loadModels()
        } else {
            ElMessage.error(res.data.message)
        }
    } catch (err) {
        ElMessage.error('删除失败: ' + (err.response?.data?.message || err.message))
    }
}

const setDefaultModel = async (id) => {
    try {
        const res = await axios.post(`${API_BASE}/models/active/${id}`)
        if (res.data.success) {
            ElMessage.success('已设为默认模型')
            await loadModels()
        } else {
            ElMessage.error(res.data.message)
        }
    } catch (err) {
        ElMessage.error('设置失败: ' + (err.response?.data?.message || err.message))
    }
}

const switchModel = async (id) => {
    try {
        const res = await axios.post(`${API_BASE}/models/active/${id}`)
        if (res.data.success) {
            ElMessage.success('已切换模型')
        } else {
            ElMessage.error(res.data.message)
        }
    } catch (err) {
        ElMessage.error('切换失败: ' + (err.response?.data?.message || err.message))
    }
}

const testModelConfig = async () => {
    if (!editingModel.value) return
    testLoading.value = true
    try {
        const res = await axios.post(`${API_BASE}/test`, editingModel.value, {
            timeout: 60000
        })
        testSuccess.value = res.data.success
        testResult.value = res.data.message
        testTime.value = res.data.testTime || ''
        editingModel.value.testResult = res.data.message
        editingModel.value.testSuccess = res.data.success
        editingModel.value.testTime = res.data.testTime || ''
    } catch (err) {
        testSuccess.value = false
        testResult.value = '请求失败: ' + (err.response?.data?.message || err.message)
        testTime.value = ''
        editingModel.value.testResult = testResult.value
        editingModel.value.testSuccess = false
        editingModel.value.testTime = ''
    } finally {
        testLoading.value = false
    }
}

const loadHistory = async () => {
    try {
        const res = await axios.get(`${API_BASE}/history`)
        queryHistory.value = res.data
    } catch (e) {
        console.error(e)
    }
}

const selectFromHistory = (item) => {
    searchText.value = item.word
    direction.value = item.direction
    showHistory.value = false
    handleSearch()
}

const hideHistory = () => {
    setTimeout(() => { showHistory.value = false; showSuggestions.value = false }, 200)
}

const onInputFocus = () => {
    if (suggestions.value.length > 0) {
        showSuggestions.value = true
    } else {
        showHistory.value = queryHistory.value.length > 0
    }
}

const onInputChange = () => {
    if (suggestTimer) clearTimeout(suggestTimer)
    const text = searchText.value.trim()
    if (!text || text.length < 1) {
        suggestions.value = []
        showSuggestions.value = false
        return
    }
    const hasChinese = /[\u4e00-\u9fff]/.test(text)
    if (hasChinese) {
        suggestions.value = []
        showSuggestions.value = false
        return
    }
    if (text.includes(' ')) {
        suggestions.value = []
        showSuggestions.value = false
        return
    }
    suggestTimer = setTimeout(async () => {
        try {
            const res = await axios.get(`${API_BASE}/suggest`, {
                params: { prefix: text, limit: 10 }
            })
            suggestions.value = res.data.suggestions || []
            showSuggestions.value = suggestions.value.length > 0
            showHistory.value = false
        } catch (err) {
            suggestions.value = []
            showSuggestions.value = false
        }
    }, 300)
}

const selectSuggestion = (word) => {
    searchText.value = word
    showSuggestions.value = false
    suggestions.value = []
    handleSearch()
}

const handleSearch = async () => {
  if (!searchText.value.trim()) return
  
  loading.value = true
  aiLoading.value = true
  currentWord.value = searchText.value
  aiResult.value = ''
  
  try {
    if (useDict.value) {
      const dictRes = await axios.get(`${API_BASE}/dict`, {
        params: { word: searchText.value }
      })
      dictResult.value = dictRes.data
    }
    
    if (useAI.value) {
      await fetchAIStream(searchText.value, direction.value)
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
    aiLoading.value = false
  }
}

const reAnalyze = async () => {
  if (!currentWord.value) return
  aiLoading.value = true
  aiResult.value = ''
  try {
    await axios.delete(`${API_BASE}/cache`, {
      params: { word: currentWord.value, direction: direction.value }
    })
  } catch {}
  try {
    await fetchAIStream(currentWord.value, direction.value)
  } catch (err) {
    console.error(err)
  } finally {
    aiLoading.value = false
  }
}

const fetchAIStream = async (word, dir) => {
  aiStats.value = ''
  aiTokenCount = 0
  aiStartTime = Date.now()
  aiElapsed.value = 0
  aiTimer = setInterval(() => {
    aiElapsed.value = Math.floor((Date.now() - aiStartTime) / 1000)
  }, 1000)

  try {
    const response = await fetch(
      `${API_BASE}/ai/stream?word=${encodeURIComponent(word)}&direction=${dir}`
    )
    
    if (!response.ok) {
      aiResult.value = `<p style='color: #F56C6C;'>请求失败: ${response.status}</p>`
      return
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let usageInfo = null
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)
        if (data === '[DONE]') break
        
        try {
          const parsed = JSON.parse(data)
          if (parsed.error) {
            aiResult.value += `\n<p style='color: #F56C6C;'>错误: ${parsed.error}</p>`
          } else if (parsed.usage) {
            usageInfo = parsed.usage
          } else if (parsed.content) {
            aiResult.value += parsed.content
          }
        } catch {
          aiResult.value += data
        }
      }
    }
  } catch (err) {
    console.error('AI流式请求失败:', err)
    aiResult.value = `<p style='color: #F56C6C;'>AI 解析失败: ${err.message}</p>`
  } finally {
    clearInterval(aiTimer)
    aiTimer = null
    const totalSec = Math.round((Date.now() - aiStartTime) / 1000)
    if (usageInfo && usageInfo.total_tokens) {
      const promptTokens = usageInfo.prompt_tokens || 0
      const completionTokens = usageInfo.completion_tokens || 0
      const totalTokens = usageInfo.total_tokens || 0
      const tokensPerSec = totalSec > 0 ? (completionTokens / totalSec).toFixed(1) : completionTokens
      aiStats.value = `加载完成，耗时: ${totalSec}s，生成Token: ${tokensPerSec}/s，总Token: ${totalTokens}（输入: ${promptTokens}，输出: ${completionTokens}）`
    } else {
      aiStats.value = `加载完成，耗时: ${totalSec}s`
    }
  }
}

let currentAudio = null

const speakWord = (word) => {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  
  const hasSpace = /\s/.test(word.trim())
  
  if (hasSpace) {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(word)
      u.lang = 'en-US'
      u.onend = () => { console.log('发音结束:', word) }
      u.onerror = (e) => {
        if (e.error === 'canceled' || e.error === 'interrupted') return
        console.error('speechSynthesis错误:', e.error)
      }
      speechSynthesis.speak(u)
    }
    return
  }
  
  const audio = new Audio(`https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=2`)
  audio.onplay = () => { console.log('发音开始:', word) }
  audio.onended = () => { console.log('发音结束:', word) }
  audio.onerror = () => {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(word)
      u.lang = 'en-US'
      speechSynthesis.speak(u)
    }
  }
  currentAudio = audio
  audio.play().catch(() => {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(word)
      u.lang = 'en-US'
      speechSynthesis.speak(u)
    }
  })
}

const handlePronounce = () => {
  if (!currentWord.value) return
  speakWord(currentWord.value);
}

const saveSettings = async () => {
  localStorage.setItem('idic_settings', JSON.stringify(settingsForm.value))
  try {
    await axios.post(`${API_BASE}/proxy`, proxyForm.value)
  } catch (err) {
    console.error('保存代理配置失败:', err)
  }
  if (window.electronAPI) {
    try {
      await window.electronAPI.setMinimizeToTray(settingsForm.value.minimizeToTray)
    } catch (err) {
      console.error('保存托盘设置失败:', err)
    }
  }
  showSettings.value = false
  ElMessage.success('设置已保存')
}

const addToWordbook = () => {
  if (!currentWord.value) return
  const item = {
    word: currentWord.value,
    date: new Date().toLocaleString()
  }
  wordbook.value.push(item)
  localStorage.setItem('idic_wordbook', JSON.stringify(wordbook.value))
  ElMessage.success('已添加到生词本')
}

const queryFromWordbook = (word) => {
  showWordbook.value = false
  searchText.value = word
  handleSearch()
}

const removeFromWordbook = (row) => {
  const index = wordbook.value.findIndex(w => w.word === row.word)
  if (index > -1) {
    wordbook.value.splice(index, 1)
    localStorage.setItem('idic_wordbook', JSON.stringify(wordbook.value))
    ElMessage.success('已从生词本中删除')
  }
}

const aiResultHtml = computed(() => {
    if (!aiResult.value) return ''
    
    let content = aiResult.value
    let html = md.render(content)
    
    const tags = []
    let i = 0
    html = html.replace(/<[^>]+>/g, (tag) => {
        tags[i] = tag
        return `\x00T${i++}\x00`
    })

    const entities = []
    let j = 0
    html = html.replace(/&[a-zA-Z]+;|&#\d+;/g, (entity) => {
        entities[j] = entity
        return `\x00E${j++}\x00`
    })
    
    const phonetics = []
    let k = 0
    html = html.replace(/\/[^\/]+\//g, (ph) => {
        phonetics[k] = ph
        return `\x00P${k++}\x00`
    })
    
    html = html.replace(/\b([a-zA-Z]{2,}(?:[\s\-][a-zA-Z]+)*)\b/g, 
        (word) => {
            const escapedWord = word.replace(/'/g, "\\'")
            return `<span class="pronounce-word" onclick="window.pronounceWord('${escapedWord}')">${word}<span class="pronounce-icon">🔊</span></span>`
        }
    )
    
    for (let pi = 0; pi < phonetics.length; pi++) {
        html = html.split(`\x00P${pi}\x00`).join(phonetics[pi])
    }
    for (let ei = 0; ei < entities.length; ei++) {
        html = html.split(`\x00E${ei}\x00`).join(entities[ei])
    }
    for (let ti = 0; ti < tags.length; ti++) {
        html = html.split(`\x00T${ti}\x00`).join(tags[ti])
    }
    
    return html
})

onMounted(async () => {
    await loadModels()
    
    const savedSettings = localStorage.getItem('idic_settings')
    if (savedSettings) {
        settingsForm.value = JSON.parse(savedSettings)
    }

    if (window.electronAPI) {
        try {
            const version = await window.electronAPI.getAppVersion()
            if (version) appVersion.value = version
            const traySetting = await window.electronAPI.getMinimizeToTray()
            settingsForm.value.minimizeToTray = traySetting
        } catch (err) {
            console.error('读取Electron设置失败:', err)
        }
    }
    
    try {
        const proxyRes = await axios.get(`${API_BASE}/proxy`)
        proxyForm.value = proxyRes.data
    } catch (err) {
        console.error('加载代理配置失败:', err)
    }
    
    const savedWordbook = localStorage.getItem('idic_wordbook')
    if (savedWordbook) {
        wordbook.value = JSON.parse(savedWordbook)
    }
    
    await loadHistory()
    
    window.pronounceWord = (word) => {
        speakWord(word);
    }
})
</script>

<style scoped>
.idic-app {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
}

.main-container {
  height: 100%;
}

.menu-bar {
  background: #fff;
  padding: 8px 30px;
  display: flex;
  gap: 8px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  transition: all 0.3s;
}

.menu-item:hover {
  background: #f5f7fa;
  color: #409EFF;
}

.header {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  padding: 20px 40px;
  height: auto !important;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.search-section {
  display: flex;
  flex: 1;
  gap: 16px;
  align-items: center;
  max-width: 900px;
}

.search-input-wrapper {
  position: relative;
  flex: 1;
  z-index: 100;
}

.search-input {
  flex: 1;
}

.model-select {
  width: 160px;
}

.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #E4E7ED;
  border-radius: 8px;
  margin-top: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1001;
}

.suggestion-item {
  padding: 8px 16px;
  cursor: pointer;
  border-bottom: 1px solid #F5F7FA;
  transition: all 0.2s;
  font-size: 14px;
  color: #303133;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: #ECF5FF;
  color: #409EFF;
}

.history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #E4E7ED;
  border-radius: 8px;
  margin-top: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.history-item {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #F5F7FA;
  transition: all 0.2s;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item:hover {
  background: #F5F7FA;
}

.history-word {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.history-time {
  font-size: 12px;
  color: #909399;
}

.pronounce-word {
  display: inline-block;
  cursor: pointer;
  padding: 2px 6px;
  margin: 1px;
  border-radius: 4px;
  transition: all 0.2s;
}

.pronounce-word:hover {
  background: #ecf5ff;
}

.pronounce-icon {
  margin-left: 4px;
  font-size: 14px;
  opacity: 0.7;
}

.pronounce-word:hover .pronounce-icon {
  opacity: 1;
}

.options {
  display: flex;
  gap: 16px;
  font-size: 15px;
  align-items: center;
}

.main-content {
  padding: 30px 40px;
  overflow-y: auto;
}

.word-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 30px;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  margin-bottom: 24px;
}

.word-title {
  font-size: 48px;
  font-weight: 900;
  margin: 0;
  color: #409EFF;
}

.result-row {
  margin-top: 16px;
}

.result-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-loading-info {
  font-size: 12px;
  font-weight: 400;
  color: #E6A23C;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.ai-stats-info {
  font-size: 12px;
  font-weight: 400;
  color: #67C23A;
}

.dict-content, .ai-result {
    line-height: 1.8;
    font-size: 16px;
}

.markdown-body {
    line-height: 1.8;
    font-size: 16px;
    color: #333;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
    line-height: 1.4;
    color: #409EFF;
}

.markdown-body h1 {
    font-size: 2em;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.3em;
}

.markdown-body h2 {
    font-size: 1.5em;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.3em;
}

.markdown-body h3 {
    font-size: 1.25em;
}

.markdown-body p {
    margin-top: 1em;
    margin-bottom: 1em;
}

.markdown-body ul,
.markdown-body ol {
    padding-left: 2em;
    margin-top: 1em;
    margin-bottom: 1em;
}

.markdown-body li {
    margin: 0.5em 0;
}

.markdown-body li > p {
    margin-top: 0.5em;
    margin-bottom: 0.5em;
}

.markdown-body code {
    background: #f5f7fa;
    border-radius: 3px;
    padding: 0.2em 0.4em;
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
    font-size: 0.9em;
}

.markdown-body pre {
    background: #f5f7fa;
    border-radius: 6px;
    padding: 1em;
    overflow-x: auto;
}

.markdown-body pre code {
    background: transparent;
    padding: 0;
}

.markdown-body blockquote {
    border-left: 3px solid #409EFF;
    background: #f0f9ff;
    padding: 0.5em 1em;
    margin: 1em 0;
    color: #666;
}

.markdown-body strong,
.markdown-body b {
    font-weight: 600;
    color: #333;
}

.markdown-body a {
    color: #409EFF;
    text-decoration: none;
}

.markdown-body a:hover {
    text-decoration: underline;
}

.test-result-box {
  margin-top: 8px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
}

.model-manager {
  min-height: 300px;
}

.model-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.model-list-title {
  font-weight: 600;
  font-size: 15px;
  color: #333;
}

.model-empty {
  text-align: center;
  padding: 30px;
  color: #909399;
  font-size: 14px;
}

.model-list {
  max-height: 240px;
  overflow-y: auto;
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid #EBEEF5;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.model-item:hover {
  border-color: #409EFF;
  background: #f0f9ff;
}

.model-item-active {
  border-color: #409EFF;
  background: #ecf5ff;
}

.model-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-item-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.model-item-detail {
  font-size: 12px;
  color: #909399;
}

.model-item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.edit-title {
  margin: 0 0 16px;
  font-size: 15px;
  color: #409EFF;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.model-edit-placeholder {
  text-align: center;
  padding: 40px;
  color: #C0C4CC;
  font-size: 14px;
}
</style>

<!-- Markdown 全局样式 -->
<style>
.ai-result.markdown-body h1,
.ai-result.markdown-body h2,
.ai-result.markdown-body h3,
.ai-result.markdown-body h4,
.ai-result.markdown-body h5,
.ai-result.markdown-body h6 {
    color: #409EFF !important;
}
</style>
