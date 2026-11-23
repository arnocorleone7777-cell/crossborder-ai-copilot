CrossBorder-Copilot | 跨境电商 BI 智能诊断与 AIGC 全栈工作台基于 FastMCP (stdio)、LangGraph、SQLGlot AST 确定性安全护栏、Ollama (Qwen2-7B + nomic-embed-text) 与 React 18 + TypeScript 构建的端到端 AI 全栈系统。1. 核心架构与技术亮点 (Architecture)代码段graph LR
    A[React 18 + TS 前端<br/>SSE 流式工作台] -->|POST /api/chat/stream| B[FastAPI 网关<br/>Semaphore 并发限流]
    B --> C[LangGraph StateGraph<br/>多步状态编排引擎]
    C --> D{SQLGlot AST 护栏<br/>只读与白名单校验}
    D -->|校验失败/报错 <3次| C
    D -->|通过| E[FastMCP: BI-MySQL Server<br/>stdio 独立进程通信]
    E --> F[根因归因与漏斗分析]
    F --> G[FastMCP: AIGC-Skills Server<br/>FAISS 检索 + PIL 海报 + 合规校正]
    G -->|SSE 结构化事件流| A
标准化 MCP 协议解耦： 基于官方 FastMCP 通过标准 stdio 传输层独立拉起 BI-MySQL 与 AIGC-Skills 两个工具进程，实现 Agent 推理与底层执行环境的物理隔离。Harness Engineering（确定性安全护栏）： 引入 SQLGlot 对大模型生成的 SQL 进行 AST 抽象语法树静态校验，100% 拦截非 SELECT 写操作、表名幻觉及无 LIMIT 慢查询；结合 LangGraph 条件边实现报错自愈（Self-Correction）闭环。本地算力调度与防幻觉规则引擎： 接入局域网 Ollama 部署的 Qwen2-7B（4-bit 量化）与 FAISS 向量索引（nomic-embed-text）；后置中性文案规则校验器，自动拦截并修正未经证实的营销夸大话术。生成式前端工作台（Generative UI）： 基于 React 18 + TypeScript + Vite 构建，通过 SSE 实时渲染分析步骤、双周期 ROAS/CTR 对比折线图、15 秒分镜脚本与双风格（Concept A/B）视觉海报。2. 界面与实测指标 (Demo & Benchmarks)评估维度本地实测数据 (Qwen2-7B + RTX 4060 节点)工程保障机制SQL 查询执行耗时51 ms（单次通过 AST 校验与执行）SQLGlot AST 静态解析 + 自动 LIMIT 注入端到端全链路耗时14.17 秒（含 BI 归因 + 脚本 + 双版海报合成）asyncio.Semaphore(3) 显存并发控制 + 10s SSE 心跳保活合规防幻觉校验自动定位并修正 4 处越界话术字段后置确定性中性规则校正器（输出审计日志）经营总览与异常信号诊断创意工作室：TikTok 分镜脚本与 A/B 视觉概念海报自动生成3. 快速启动 (Quick Start)Bash# 后端启动
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 前端启动
cd frontend && npm install && npm run dev