# Paper Trace

论文问答与原文证据工作台：左侧提问、右侧 PDF、点击引用定位文本行。

技术栈：Docker Compose · PostgreSQL 16 + pgvector · Python 3.11 / FastAPI · Next.js / react-pdf-highlighter。

## 启动

启动 Docker Desktop（macOS 可执行 `docker desktop start`），等待 Docker 就绪后，在仓库根目录执行。首次运行：

```sh
cp .env.example .env
# 编辑 .env，填写 SILICONFLOW_API_KEY
make sample
make up
make ingest
```

打开 http://localhost:3000 。API 文档：http://localhost:8000/docs 。密钥保存在 Git 忽略的 `.env`，仅由后端读取。

后续启动（复用已有 `.env`、PDF 与数据库索引）：

```sh
docker desktop start
make up
```

查看服务状态与日志：

```sh
docker compose ps
docker compose logs -f
```

```sh
make eval                         # 25 条真实 API 检索对比
# 可选：同时生成回答并运行 LLM 裁判，产生额外调用费用
docker compose exec api python evaluate.py --document-id 1 --dataset /evaluation/dataset.json --output /evaluation/results-judge.json --judge
```

## 停止

在仓库根目录执行：

```sh
make down                         # 等价于 docker compose down，停止并移除项目容器
docker desktop stop              # 关闭 Docker Desktop 后台及其引擎
```

数据库卷、原始 PDF、`.env` 和构建镜像保留，下次运行 `docker desktop start` 与 `make up` 即可继续使用。Docker Desktop 停止时会一并关闭其余 Docker 工作负载；macOS 也可通过菜单栏 Docker 图标选择 Quit Docker Desktop。

本地开发模式：在运行 FastAPI 和 Next.js 的两个终端分别按 `Ctrl+C`，再在仓库根目录执行 `make down` 和 `docker desktop stop`。

## 本地开发

```sh
docker compose up -d db
cd backend
uv sync --python 3.11
uv run ingest.py ../data/pdfs/attention-is-all-you-need.pdf
uv run uvicorn app.main:app --reload
# 另一终端
cd frontend
npm ci
npm run dev
```

添加论文：把可提取文本的 PDF 放进 `data/pdfs/`，运行 `docker compose exec api python ingest.py /data/pdfs/文件名.pdf`，刷新页面后选择文档。重复导入以事务替换切块；扫描件需要先 OCR。

## 数据链路

1. PyMuPDF 按自然文本块提取行与坐标，500 字符切分，50 字符重叠；每块绑定页码与归一化行矩形数组。
2. 4 路并发、每批 16 段调用 `BAAI/bge-m3`，校验 1024 维，事务批量写入。
3. 余弦 Top-15 与英语全文 Top-15 并行召回，RRF(k=60) 去重，`BAAI/bge-reranker-v2-m3` 精排 Top-5。
4. 最高相关性分数低于 0.35 时拒答；`deepseek-ai/DeepSeek-V3` JSON Mode 生成，Pydantic 校验与引用白名单验证。
5. 后端将引用还原成数据库中的页码、行矩形和原文；前端缩放高亮并滚动。

英文全文索引适用于示例英文论文；中文问题主要依赖多语言向量召回。坐标精度为相交文本行矩形，切块边界落在行中时会高亮完整文本行。

JSON Mode 约束输出格式，应用校验会将异常格式和越界引用作为错误返回。相关性阈值与证据提示降低幻觉风险，答案正确性仍需评测。

## 验证与指标

```sh
cd backend && uv run pytest -q
cd frontend && npm run build
```

`evaluation/dataset.json` 包含 20 条事实问题和 5 条超纲问题。`evaluate.py` 输出 page_hit_at_5（页级召回代理指标）、超纲拒答准确率、可回答问题接受率、平均延迟，`--judge` 添加正确性与证据支撑评分。页级指标比切块级证据命中更宽松，适合第一轮基线。

纯向量余弦分数与精排相关性分数具有独立刻度；当前阈值供演示使用，严谨比较需要分别在独立验证集上校准。LLM 裁判使用同一生成模型，有同源偏差。

`ingest.py` 输出解析、向量化、完整入库耗时。15 页 3 秒是待测目标；README 与简历应采用实际环境结果。

实测：15 页 / 556 切块完整入库 3.72 秒；25 题中混合精排超纲拒答 5/5，可回答接受 18/20。详细限制与逐题结果见 [评测记录](docs/evaluation.md)。

## 参考

参考 [run-llama/sec-insights](https://github.com/run-llama/sec-insights) 的对话 / PDF 双栏交互和多行引用高亮。该项目使用 react-pdf 与文本匹配；本项目以独立页面及 react-pdf-highlighter 实现坐标高亮。实现细节见 [设计记录](docs/design.md)。

示例：[Attention Is All You Need](https://arxiv.org/abs/1706.03762)，PDF 从 arXiv 下载，原文版权归权利人。

服务默认绑定本机，当前版本面向本地单用户使用。
