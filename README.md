# iDic - 智能词典 (Electron + Vue 3 + Element Plus)

## 🚀 安装与启动

### 方式一：直接安装（推荐）

前往 [Releases](https://github.com/chenzq1604/idic/releases) 页面下载最新的 `iDic Setup x.x.x.exe` 安装包，双击安装即可使用。

- ✅ 无需安装 Node.js、Python 等开发环境
- ✅ 无需手动编译和分别启动前后端服务
- ✅ 安装后桌面自动生成快捷方式，双击即可运行
- ✅ 前端和 Python 后端会自动一起启动

### 方式二：开发模式分别启动

1. **启动后端 (Python)**：
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. **启动前端 (Node.js)**：
   - 先安装依赖
   ```bash
   npm install
   ```
   - 开发模式
   ```bash
   npm run dev
   ```
   - 或者启动 Electron
   ```bash
   npm run electron:dev
   ```

### 方式三：一键启动

创建一个 `start.bat` 来同时启动前端和后端（Windows）：
```batch
@echo off
start "Backend" cmd /k "cd backend && python main.py"
timeout /t 2
start "Frontend" cmd /k "npm run dev"
```

## 🤖 模型配置

iDic 依赖大语言模型进行智能翻译解析，首次使用前需要配置模型。

### 配置文件位置

| 运行方式 | 配置文件路径 |
|---------|------------|
| 开发模式 | `resources/llm_configs.json` |
| 安装后 | `%APPDATA%/iDic/llm_configs.json` |

### 配置方法

1. 复制模板文件并重命名：
   ```bash
   copy resources\llm_configs.json.example resources\llm_configs.json
   ```

2. 编辑 `llm_configs.json`，填入你的模型信息：
   ```json
   [
     {
       "name": "我的模型",
       "api_key": "你的API Key",
       "api_base": "https://api.example.com/v3",
       "model_name": "model-name",
       "is_active": true
     }
   ]
   ```

### 配置字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 配置名称，用于界面显示，可自定义 |
| `api_key` | 是 | 大模型服务的 API Key |
| `api_base` | 是 | API 地址，需兼容 OpenAI 格式 |
| `model_name` | 是 | 模型标识，如 `gpt-4o`、`deepseek-chat` |
| `is_active` | 否 | 是否为当前激活的模型，仅一个可设为 `true` |

### 支持的模型服务

iDic 兼容所有 OpenAI API 格式的模型服务，包括但不限于：

- **火山引擎（豆包）** — `api_base`: `https://ark.cn-beijing.volces.com/api/v3`
- **DeepSeek** — `api_base`: `https://api.deepseek.com/v3`
- **OpenAI** — `api_base`: `https://api.openai.com/v3`
- **硅基流动（SiliconFlow）** — `api_base`: `https://api.siliconflow.cn/v3`
- **其他兼容服务** — 只需填入对应的 API 地址即可

### 多模型配置

可以同时配置多个模型，通过 `is_active` 切换当前使用的模型：

```json
[
  {
     "name": "DeepSeek",
     "api_key": "sk-xxx",
     "api_base": "https://api.deepseek.com/v3",
     "model_name": "deepseek-chat",
     "is_active": true
  },
  {
     "name": "GPT-4o",
     "api_key": "sk-yyy",
     "api_base": "https://api.openai.com/v3",
     "model_name": "gpt-4o",
     "is_active": false
  }
]
```

> ⚠️ **安全提醒**：`llm_configs.json` 包含 API Key 等敏感信息，已被 `.gitignore` 排除，不会被上传到 Git 仓库。请勿将该文件提交到公开仓库。

## 🛠️ 技术栈

- **前端**：Vue 3 + Element Plus + Vite
- **桌面框架**：Electron
- **后端**：Python + FastAPI

## 🎨 界面预览

现代化的界面，完全可自定义！
