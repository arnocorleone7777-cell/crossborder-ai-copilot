# CrossBorder Copilot

跨境电商 BI 诊断与创意工作台。把经营信号、可审计的指标证据和下一轮素材实验放在同一个界面中。

**完整本地链路已实现：React / TypeScript / ECharts → FastAPI SSE → LangGraph → 两个真实 MCP stdio 服务 → 只读 SQLite 或 MySQL → 脚本与 Pillow 海报。**

数据均为合成演示数据，不能代表真实商家或达人。在线站点是浏览器演示；Python、MySQL 和局域网 Ollama 在完整本地项目中运行。

## 快速开始

需要 Python 3.11+、Node.js 22+。已在 macOS、Python 3.14、Node 24 环境验证。

```sh
cd crossborder-ai-copilot
sh scripts/start.sh
```

打开 <http://127.0.0.1:8000>。脚本创建独立环境、安装依赖、生成带随机数据库密码的 `.env`、构建前端并启动服务。按 Ctrl+C 停止。SQLite 首次启动会自动生成数据，不需要 Docker、API 密钥或模型。

推荐演示问题：**“分析 TikTok 无线卷发棒的 ROAS 为什么下滑，并生成新开场脚本。”**

初次可依次查看：经营总览 → 优先关注 → 深度诊断与创意建议 → 查看脚本与海报 → 分析记录。报告支持 CSV，脚本支持复制，创意包支持 JSON，海报支持 PNG 下载。

## 接入 Ollama

先在模型所在电脑安装 [Ollama](https://ollama.com/download)，并准备一个支持结构化输出的模型：

```sh
ollama pull qwen2:7b
```

修改本地 `.env`，然后重启后端：

```dotenv
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2:7b
OLLAMA_NUM_CTX=8192
```

如果 Ollama 在局域网另一台机器，把地址改为该机器的实际 IP，并确认从运行后端的电脑可访问。模型名需与 `ollama list` 一致。页面“连接与设置”显示所选模型是否就绪。服务模式由后端配置控制，页面不会静默切换或偷偷下载模型。

`MODEL_PROVIDER=demo` 仍会运行真实 SQL、MCP 和 LangGraph，SQL 和创意文案来自确定性模板。`MODEL_PROVIDER=ollama` 使用 JSON Schema 约束及 Pydantic 校验生成 SQL 与创意文案；模型故障会明确报错，不冒充成功。实测发现小模型会将 ROAS 误作物理列，因此 SQL 提示包含实际字段与经过验证的起始查询，执行仍须经过原有安全边界。

已连接用户的 Windows 局域网 Ollama，实际检测到 `qwen2:7b` 与 `nomic-embed-text:latest`。SQLite 和 MySQL 两条路径均完成真实模型 SQL → MCP 查询 → 定量诊断 → 向量检索 → 英文脚本与海报的闭环实测。实际地址保存在本机忽略的 `.env`，不写入源码。

检查当前配置与实际服务：

```sh
.venv/bin/python -m scripts.check_ollama
# 服务和模型就绪后，再验证真实结构化输出与 SQL 校验
.venv/bin/python -m scripts.check_ollama --probe
```

`127.0.0.1` 和 `localhost` 都指向运行后端的电脑。如果 Ollama 在另一台 Windows 电脑，应使用其局域网 IP，例如 `http://192.168.1.20:11434`。在服务电脑运行 `ollama list` 可核对模型名，运行 `ollama serve` 可启动命令行服务；桌面应用已启动服务时不要重复启动。

跨电脑连接还需要 Ollama 监听该电脑的局域网接口。例如在 Windows PowerShell 中设置 `$env:OLLAMA_HOST = "192.168.1.20:11434"`，再运行 `ollama serve`（IP 必须替换为服务电脑的真实地址）。如有防火墙拦截，只允许当前开发电脑从私有网络访问该端口。配置方式参考 [Ollama 官方网络与环境变量说明](https://docs.ollama.com/faq)。

## 三种运行方式

- **浏览器演示**：使用内置 3,255 条数据在浏览器聚合；不调用 SQL、MCP 或模型。可离线分析、读取内置创意、保存浏览器分析记录。首次载入需要网络访问站点文件。UI 明确标注模式。
- **本地模板模式**：FastAPI → LangGraph → 真实 MCP 子进程 → 带安全校验的 SQL。模板创意由 Pillow 实时合成，两张 1080 × 1350 PNG。
- **Ollama 模式**：在上述真实链路中使用模型生成 SQL、根据验证错误重写 SQL，并生成脚本。定量指标和 ROAS 贡献由确定性代码计算。

Ollama 网络地址不会下发到浏览器。局域网模型由后端访问；访问凭证仅在当前页面内存使用，不写入浏览器存储。

## MySQL 与 Docker

```sh
python3 scripts/init_env.py
docker compose up --build
```

当前开发机已保存经过实测的镜像，可用 `docker compose up -d --no-build` 直接启动。常规重建需要 Docker 能访问包仓库；本次 Docker VM 无法访问 PyPI，因此验证镜像使用从官方 PyPI 预下载的同版本 Linux wheel 完成安装，详情见验证记录。

打开 <http://127.0.0.1:8000>。Compose 包含 MySQL 8.4、幂等种子任务和完整 Web 服务。数据库只开放容器内部网络，Web 默认仅绑定本机。`.env` 中的数据库密码必须是至少 32 位随机十六进制字符串，初始化脚本会自动生成。

应用账号 `copilot_reader` 只有两张业务表的 SELECT 权限；root 仅用于初始化与种子任务，不传给 Web 服务。每次查询使用只读事务、3 秒执行上限和 500 行结果上限。

容器使用独立配置 `OLLAMA_DOCKER_BASE_URL`，默认 `http://host.docker.internal:11434`，避免容器把 127.0.0.1 错当成宿主机。局域网服务需将两个 base URL 都设为服务电脑的真实 IP。若修改已初始化数据库的密码，需要同步更新数据库账户；仅修改 `.env` 不会改变持久化数据库密码。

已在本机 Docker 实机验收：镜像构建、MySQL 8.4 初始化、3,255 行种子数据、Web 健康检查、经 MCP 的完整分析与海报生成均成功。应用账号直接执行 UPDATE 被数据库拒绝（错误码 1142）。

## 语义检索（可选）

可选择关键词检索或语义检索，内置 4 条原创脚本参考，不宣称是已验证的“爆款”。当前用户工作区已启用并实测 Nomic + FAISS；新副本的默认配置仍是词法检索，不假设已有索引或嵌入服务。

```sh
.venv/bin/pip install -r requirements-vector.txt
ollama pull nomic-embed-text
```

设置 `RETRIEVAL_MODE=semantic` 后重启。此时通过 Ollama `/api/embed` 计算向量，用 FAISS 余弦相似度返回参考及分数。缺少依赖或嵌入服务会报错，不会把关键词匹配伪装为语义检索。Docker 镜像默认包含向量依赖，可通过构建参数 `INCLUDE_VECTOR=0` 关闭。语义检索已连接真实 Nomic 模型验证，使用 `search_query:` / `search_document:` 前缀和 768 维向量。

## 创意语言与来源

15 秒草稿固定为 0–3s、3–8s、8–12s、12–15s 四段。海报、口播与屏幕文案为英文，拍摄指引包含中文，口播总长不超过 45 个英文单词。对实测发现的部分未经证实的宣传措辞，规则会只替换命中的公开文案字段，保留其他模型内容，并明确标注“Ollama 生成 + 文案规则校正”及字段路径。这是一组保守的已知问题检查，发布前仍需人工核对。

## 数据与业务口径

固定种子 `20261031`；2026-10-01 至 2026-10-31；5 个商品 × 3 个平台 × 7 个合成达人 × 31 天 = **3,255 行**。数据粒度为“日期 / 商品 / 平台 / 达人”。商品跨平台销售，所以平台放在投放事实表，而不是商品主表。

默认当前期为 10/25–10/31，对照期为 10/18–10/24。两个窗口等长且必须完整覆盖，缺少对照数据时停止诊断。金额均为 USD，日期使用数据源业务日期，不做隐式时区转换。

- 3 秒留存率 = Σ3 秒观看量 / Σ曝光量；这是演示分母口径，不等同所有平台的统一定义。
- CTR = Σ点击 / Σ曝光；CVR = Σ订单 / Σ点击。
- ROAS = ΣGMV / Σ广告费，**不等于利润 ROI**。
- 简化贡献 ROI =（ΣGMV − Σ商品成本 − Σ广告费）/ Σ广告费。未含退款、履约、税费、佣金。
- 比率均先聚合分子与分母，再相除。零分母返回空值，不编造为 0。
- ROAS 周期降幅超过 20% 触发演示关注阈值，不代表统计显著。
- Shapley 对恒等式 `ROAS = 曝光 × CTR × CVR × AOV / 广告费` 做五因素精确分解，贡献之和等于 ROAS 差值。它是会计分解，**不能证明因果**。
- “素材开场吸引力减弱”是可检验假设；受众、竞价、库存、归因延迟等混杂因素仍需排除。

种子中的 SKU-104 / TikTok_US 在 10/25 起被注入留存与点击异常，默认窗口 ROAS 约 **2.79 → 0.85**。真实生成过程记录在种子脚本中；诊断不会读取异常标签。

重新生成演示快照：

```sh
.venv/bin/python -m scripts.export_demo
```

## 开发与验证

```sh
# 后端
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
# 另一终端，前端热更新
npm --prefix frontend run dev
# 检查
sh scripts/check.sh
```

Vite 在 <http://127.0.0.1:5173> 提供界面并代理 API。生产构建由 FastAPI 同源提供。若使用独立 HTTPS 前端，设置后端 `ALLOWED_ORIGINS` 为准确站点来源并配置 `API_TOKEN`、HTTPS 反向代理；浏览器设置中输入 API 地址与凭证。当前个人项目未实现多租户身份与平台账号授权，不应直接用来处理多商户真实数据。

当前 **61 项测试通过**。覆盖 SQL 风险输入、CTE 与列校验、只读执行、指标独立核对、缺失窗口、Shapley 加总、真实 MCP 传输、Pillow 图像尺寸、重试上限、空数据、HTTP SSE、模型结构化输出与真实 FAISS 索引。自动化测试隔离真实服务并使用模拟响应；真实 Windows Ollama、Nomic 与 MySQL 端到端实测另见 [交付验证记录](docs/verification.md)。

## 接口

- `GET /api/health`：模式、数据库类型、所选模型就绪状态。
- `GET /api/dashboard?start=...&end=...&platform=...&sku=...`：确定性报告。
- `POST /api/chat/stream`：请求体 `{"prompt":"...","filters":{"start":"2026-10-25","end":"2026-10-31","platform":"all","sku":"all"},"creative":true}`。
- SSE 事件：`run`、`scope`、`step`、`sql_result`、`notice`、`report`、`assets`、`done`。含 run_id 与序号，每 10 秒保活；断开会取消工作流。没有自动断线重放，避免无意重复生成。
- `GET /api/runs`、`GET /api/runs/{id}`：最近 20 次记录和结果回看。
- `GET /assets/generated/{filename}`：生成图片；与 API 使用同一可选凭证。

页面中的日期与已选范围优先。问题中识别到的商品、SKU 和平台只用于收窄“全部”范围。复杂自然语言日期必须在筛选器中明确；不会悄悄扩大数据访问范围。Ollama 生成的自定义查询与诊断证据查询分别展示，诊断报告只使用经过定义的指标计算。

## 项目结构

```text
backend/
  agent/graph.py           # LangGraph 状态图与有界重试
  db/                     # SQLite / MySQL Schema、确定性数据
  mcp_servers/            # BI 与创意两个官方 FastMCP 服务
  services/               # SQL 策略、数据库、指标、Ollama、创意、记录
  main.py                 # FastAPI、SSE、取消、并发上限、静态站点
frontend/src/             # React / TS / ECharts 工作台与浏览器演示
scripts/                  # 启动、检查、随机配置、数据导出
tests/                    # 安全与业务行为验证
docs/                     # 架构、设计取舍、演示与部署说明
```

进一步说明：[架构与原方案改进](docs/architecture.md)、[演示与验收](docs/demo.md)。

接口参考：[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)、[LangGraph streaming](https://docs.langchain.com/oss/python/langgraph/streaming)、[SQLGlot](https://sqlglot.com/sqlglot.html)、[Ollama 结构化输出](https://docs.ollama.com/capabilities/structured-outputs)。
