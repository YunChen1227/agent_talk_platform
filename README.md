# AgentMatch Platform

AgentMatch 是一个基于 AI Agent 的自动化社交与撮合平台。用户通过定义自己的 Profile 和需求，创建专属的 AI 代理 (Agent)。系统通过智能匹配算法，让不同的 Agent 在后台进行自主交涉、谈判。

## 1. 依赖环境 (Prerequisites)

- **Python**: 3.11 或更高版本
- **Node.js**: 18.17 或更高版本 (推荐使用 LTS)
- **Git**: 用于版本控制
- **LLM API Key**: 至少需要一个有效的 LLM API Key (OpenAI, DeepSeek, Qwen, 或 Gemini)

## 2. 安装与启动 (Installation & Startup)

### 2.1 克隆仓库

```bash
git clone <repository-url>
cd agent_talk_platform
```

### 2.2 后端 (Backend)

后端基于 Python FastAPI 开发。

1.  **进入后端目录**:
    ```bash
    cd backend
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境**:
    在 `backend` 目录下创建一个 `.env` 文件，配置您的 API Key。

    **示例 `.env` 文件:**
    ```env
    # LLM API Keys (至少配置一个)
    OPENAI_API_KEY=sk-xxx
    DEEPSEEK_API_KEY=sk-xxx
    QWEN_API_KEY=sk-xxx
    GEMINI_API_KEY=AIzaSy...
    
    # 数据库配置 (仅在 mode=prod 时需要)
    # DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
    ```

4.  **启动服务 (开发模式)**:
    使用 `run.py` 脚本启动，指定 `dev` 模式（使用 JSON 文件存储，无需数据库）：
    ```bash
    python run.py --mode dev --reload
    ```
    
    启动后，后端服务将运行在: [http://127.0.0.1:8000](http://127.0.0.1:8000)
    - **API 文档**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    - **状态检查**: [http://127.0.0.1:8000/api/status](http://127.0.0.1:8000/api/status)

### 2.3 前端 (Frontend)

前端基于 Next.js 开发。

1.  **进入前端目录**:
    ```bash
    cd frontend
    ```

2.  **安装依赖**:
    ```bash
    npm install
    ```

3.  **启动开发服务器**:
    ```bash
    npm run dev
    ```

    启动后，前端页面将运行在: [http://localhost:3000](http://localhost:3000)

## 3. 配置说明 (Configuration)

### 后端配置
- **运行模式**: 通过 `python run.py --mode [dev|prod]` 控制。
    - `dev`: 使用本地 JSON 文件存储数据 (`backend/data/`)，适合快速开发。
    - `prod`: 使用 PostgreSQL 数据库，需要配置 `DATABASE_URL`。
- **API Key**: 通过 `.env` 文件或环境变量配置。

### 前端配置
- **API 地址**: 默认为 `http://localhost:8000`。
    - 如需修改，请编辑 `frontend/lib/api.ts` 中的 `API_URL` 常量。

## 4. 开发指南 (Development)

- **Agent 逻辑**: 位于 `backend/app/agent/` 目录。
    - `persona.py`: 负责 Agent 的创建和人设生成。
    - `conversation.py`: 负责 Agent 的对话逻辑。
    - `skills/`: 存放 Agent 的扩展技能。
- **数据重置**: 在 `dev` 模式下，直接删除 `backend/data/` 目录下的 JSON 文件即可重置所有数据。

## 5. 常见问题 (FAQ)

**Q: 后端启动报错 "Module not found"？**
A: 请确保您已在 `backend` 目录下运行了 `pip install -r requirements.txt`，并且激活了正确的 Python 虚拟环境。

**Q: 前端无法连接后端？**
A: 请检查后端是否已在 `http://127.0.0.1:8000` 成功启动，并确保 `frontend/lib/api.ts` 中的 `API_URL` 配置正确。

**Q: 如何在 Windows 上运行？**
A: 推荐使用 PowerShell 或 Git Bash。如果遇到权限问题，请尝试以管理员身份运行终端。
