# 交付验证记录

验证日期：2026-11-07（Australia/Sydney）。

## 自动化与界面

- `pytest -q`：61 passed；第三方 LangSmith 在 Python 3.14 上有弃用提示，不影响本次运行。
- TypeScript 编译及 Vite 生产构建成功；ECharts 独立包约 569 KB / gzip 193 KB，仍有大包提示。
- 1440px 桌面和 390px 手机宽度已检查筛选、诊断与创意展示。
- 测试隔离个人 `.env`，默认使用 SQLite、模板与词法检索；模型协议测试使用模拟响应，不会偷偷调用用户 GPU。
- 模型输出的英文文案、中文拍摄指引、四段时间顺序、口播长度和已知宣传用语检查均有行为测试。

## 真实 Windows Ollama

- `/api/tags` 检测到 `qwen2:7b` 和 `nomic-embed-text:latest`；服务返回版本 0.40.15。
- Qwen2 实际返回 JSON Schema 约束的 SQLPlan，经 Pydantic 与 SQLGlot 校验后通过 MCP 执行。
- Nomic 实际返回 768 维向量，FAISS IndexFlatIP 检索实际运行，使用 search_query / search_document 前缀。
- SQLite 完整链路约 13.05 秒，SQL 一次尝试成功；MySQL 完整链路约 14.17 秒，同样一次查询成功。耗时为当次观测，不代表性能保证。
- 两条链路均返回 4 段脚本、2 张 1080×1350 海报；字段语言与时间顺序已校验。
- 部分模型宣传用语经确定性规则替换为中性文案，并显示“Ollama 生成 + 文案规则校正”；字段路径保存在 editorial_adjustments，原样保留其他模型输出。
- 原始语言与宣传措辞不合格的测试运行明确失败或进入修正，没有放宽 SQL 策略来获得成功。
- 初始 localhost 拒绝连接、局域网访问超时均已解决；实际地址与当前启用的 Ollama / semantic 模式仅保存在忽略的 `.env`。

## MySQL 与容器

- MySQL 8.4 与 Web 容器健康检查通过，数据共 3,255 行。
- MySQL → MCP → Qwen2 → Nomic + FAISS → 脚本 / Pillow PNG 完整链路成功。
- 异常 SKU-104 / TikTok_US 当前 ROAS 0.853925330149328，与 SQLite 和浏览器计算一致。
- reader 账号 SELECT 正常，直接 UPDATE 被 MySQL 拒绝（1142）；权限验证语句使用 1=0，没有改变数据。
- 原有基础镜像已成功构建。当前 Docker VM 可访问 Windows LAN 服务，但无法访问 PyPI；新增向量依赖由 Mac 从官方 PyPI 下载 Linux aarch64 / Python 3.12 wheel，在临时构建上下文离线安装。
- 验证镜像的运行代码与项目一致，包含 faiss-cpu 1.15.1、numpy 2.5.4；仓库 Dockerfile 保持常规网络安装方式，没有硬编码临时 wheel 路径。
- 本机镜像已经可供 docker compose up -d --no-build 启动。重新构建需恢复 Docker 到包仓库的网络，或自行提供离线依赖。

## 交付边界

- 在线 Site 是明确标注的浏览器演示，真实 Windows 模型由本地 FastAPI 后端访问。
- 真实店铺平台数据接入、广告发布与生产负载验证尚未进行，当前数据均为合成数据。
- 个别语言与宣传用语规则不是完整广告审查；生成内容仍为待验证草稿。
- 密码、真实服务地址、运行数据库、生成图片和依赖缓存不进入源码仓库或源码包。
