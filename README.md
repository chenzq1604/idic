# iDic - 智能词典 (Electron + Vue 3 + Element Plus)

## 🚀 启动方式

### 方式一：分别启动

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

### 方式二：一键启动

创建一个 `start.bat` 来同时启动前端和后端（Windows）：
```batch
@echo off
start "Backend" cmd /k "cd backend && python main.py"
timeout /t 2
start "Frontend" cmd /k "npm run dev"
```

## 🛠️ 技术栈

- **前端**：Vue 3 + Element Plus + Vite
- **桌面框架**：Electron
- **后端**：Python + FastAPI

## 🎨 界面预览

现代化的界面，完全可自定义！
