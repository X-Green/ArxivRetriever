# ArxivRetriever

一个用于抓取会议（当前以 CVPR / ICCV 为主）论文链接，并从 arXiv 拉取论文 ID 与嵌入模型准备的轻量级工具集。

## 当前功能
- conference_crawler.py：从 CVF 开放获取会议页面，抓取论文标题与可用链接（优先 arXiv abs 链接，次选 PDF）。
  - 输出目录：`paper_arxiv_lists/`
  - 输出格式：`{ConferenceName}_paper_ids.json`，JSON 映射：`{ "论文标题": "arxiv_abs_or_pdf_url", ... }`
- main.py：示例性使用 arxiv 库搜索并过滤时间区间内的论文 ID；并展示如何加载 SentenceTransformer 嵌入模型（交互式 shell 结尾，便于实验）。

## 项目结构（相关文件）
- conference_crawler.py — 抓取 CVPR/ICCV 等会议页面并保存 JSON。
- main.py — 使用 arxiv API 获取论文 ID 列表并加载嵌入模型。
- readme.md — 本文件。

## 环境与依赖
Python 3.8+. I used 3.13

First install uv.
```shell
python -m pip install uv
```

Then run the code with uv:

```shell
uv start conference_crawler.py
```
And
```shell
uv start main.py
```
## 快速开始

1. 抓取会议论文（在项目根目录运行）：
   - python conference_crawler.py
   - 输出会被写到 `paper_arxiv_lists/{ConferenceName}_paper_ids.json`

2. 使用 arXiv API 获取论文 ID 并加载嵌入模型：
   - python main.py
   - main.py 示例会调用 getPaperIDList 和 getEncoderModel，最后进入交互式 shell（可以在 shell 中进一步处理 paper_id_list、encoder_model 等对象）。

## 注意事项与提示
- conference_crawler.py 假设目标页面结构与 CVF openaccess 类似（`div#content` 下的 `dl`，`dt.ptitle` 为论文标题，随后 `dd` 含链接）。若页面结构改变，需要调整解析逻辑（BeautifulSoup 部分）。
- 抓取时 respect robots.txt，并在请求间加入适当延迟（脚本中已加 2s 延迟）。
- main.py 中使用的嵌入模型名称 `'Qwen3-Embedding-0.6B'` 仅为示例；如果无法加载，请替换为系统可用的模型名（例如常见的 sentence-transformers 模型）。

## TODO
1. main retriever: 抓取并存储 paper 的摘要、作者、年份等元信息。
2. main retriever: 将 paper 信息向量化并保存向量索引（用于检索）。
3. main retriever: 基于 query 返回相关论文（实现检索逻辑，e.g. FAISS、Annoy）。
4. 抓取更多会议（ICLR、NeurIPS、AAAI、ICML、ECCV 等）以及arxiv上最近提交的新论文。

## 贡献
欢迎通过 Pull Request 提交改进，或在 issues 中提出需要的特性与 bug 报告。
