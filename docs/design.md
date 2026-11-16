# Paper Trace 实现与验收

按照用户六层设计：Postgres 16 + pgvector 1024 维 / Python 3.11 FastAPI / Next.js。
PDF 原文存本地；文本按自然块切分，500 字符、50 重叠；每个切块保存相交文本行的归一化矩形数组。
稠密和英语词法检索各召回 15，RRF k=60，硅基流动精排 5，最高分阈值默认 0.35。
生成 JSON 后进行 Pydantic 和候选引用白名单校验；阈值拒答及模型服务错误分别返回明确状态。
PDF 阅读组件通过归一化坐标映射 scaled position，引用点击滚动。
评测固定 25 条问题（20 条论文事实，5 条超纲），同时记录召回、拒答、延迟，可选生成与裁判。
3 秒入库为性能目标，实际值由 ingest.py 输出；网络延迟、限流和硬件影响结果。

验收：pytest、Next production build、真实论文入库、API 查询与拒答、25 条评测、浏览器引用定位。

参考：https://github.com/run-llama/sec-insights 的 ViewPdf.tsx / VirtualizedPdf.tsx / multi-line-highlight.tsx。
上游以 react-pdf 和模糊文本匹配实现多行高亮；本项目按用户要求采用 react-pdf-highlighter 和入库矩形，实现独立的论文场景界面。未复制上游源码。
