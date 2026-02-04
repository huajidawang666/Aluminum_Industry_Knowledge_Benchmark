# Aluminum Industry Knowledge Benchmark: 铝工业知识评测基准

> **注意**：本项目正在建设中。下文包含当前实现模块、进度以及如何运行核心脚本的示例（bash）。

## 1. 项目概述

本项目旨在构建一套用于评估大语言模型（LLMs）在铝工业领域知识水平的基准数据集（问答对、推理题）。来源优先采用教材、专著与综述，例如《铝冶炼工艺》。

主要目标：
- 使用可复现的管道从 PDF -> OCR 文本 -> LLM 生成题目 -> 人工校验 -> 最终数据集。
- 提供工具脚本以加速预处理、OCR、切分与数据合并工作流。

## 2. 当前进度（更新于 2026-02-04）

- PDF 拆分（按页）: 已实现（`raw/SlicePDF.py`） ✅
- OCR 集成（上传/下载与解压）: 已实现（`raw/OCR.py`，依赖外部服务） ✅
- 基于提示词调用 LLM 生成问题: 已实现（`dataset/dataset.py`） ✅
- 文本拆分/分块（Markdown header 拆分）: 已实现（`raw/splitter.py`） ✅
- 合并问题与人工标注: 已实现基础工具（`utils/process_json.py`） ✅
- 待完成：数据清洗、批量人工校验界面、最终导出与评估脚本 ⏳

## 3. 代码与文件清单（关键项）

```
Aluminum_Industry_Knowledge_Benchmark/
├── dataset/                      # 数据集相关脚本
│   └── dataset.py                # 从文本构建 LLM 提示并调用生成题目
├── materials/                    # 原始资料与处理结果
│   ├── labeled/                  # 分块标签
│   ├── ocr/                      # OCR 结果
│   ├── processed/                # 拆分后的页面
│   ├── raw/                      # 原始 PDF 文件
│   └── split_markdown/           # Markdown 分块
├── output/                       # 生成的题目/中间结果
├── raw/                          # 预处理与 OCR 脚本
│   ├── SlicePDF.py               # 将 PDF 拆分为按页 PDF 文件
│   ├── OCR.py                    # 上传/下载并解压 OCR 结果
│   └── splitter.py               # Markdown header 分块工具
├── schemes/
│   └── 方案.md / 详细方案.md      # 项目计划与设计说明
├── utils/
│   └── process_json.py           # 合并问题与标签（生成最终数据集）
├── requirements.txt              # Python 依赖
└── README.md                     # 本文件
```

## 4. 快速上手（bash 示例）

1) 安装依赖（建议在虚拟环境中运行）

```bash
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) 拆分 PDF（把 `path/to/doc.pdf` 换成你的文件）

```bash
python -m raw.SlicePDF "path/to/doc.pdf"
```

输出位置示例：`materials/processed/<doc_stem>/page_001.pdf` 等

3) 运行 OCR（注意：脚本使用外部 API，需配置令牌）

```bash
python raw/OCR.py
```

4) 从文本生成题目（示例：事实类/单选+判断）

```bash
python dataset/dataset.py "path/to/text.txt" \
    --mode objective \
    --output output/objective.json
# optional choices:
    --api-key YOUR_API_KEY_HERE \
    --base-url YOUR_API_BASE_URL_HERE \
    --single-choice 5 \
    --true-false 5 \
    --model gpt-4o-mini \
    --temperature 0.7 \
    --max-tokens 512 
```

或生成推理类题目：

```bash
python dataset/dataset.py "path/to/text.txt" \
    --mode reasoning \
    --output output/reasoning.json
# optional choices:
    --api-key YOUR_API_KEY_HERE \
    --base-url YOUR_API_BASE_URL_HERE
    --reasoning-count 5 \
    --model gpt-4o-mini \
    --temperature 0.7 \
    --max-tokens 512 \
```

5) 合并问题与人工标注（如果已分别保存）

```bash
python utils/process_json.py questions.json labels.json --output output/final_dataset.json
```

## 5. 重要注意事项

- 请不要在代码仓库中硬编码任何 API 密钥或凭证（例如 OpenAI/其他服务密钥）。
- `dataset/dataset.py` 及 `raw/OCR.py` 中含有示例调用或占位，请确保在部署前将秘钥迁移到环境变量（如 `OPENAI_API_KEY`）或安全的凭证存储中。
- 模型生成的题目必须要人工复核后方可进入数据集；当前 pipeline 假设“LLM 生成 -> 人工校验 -> 合并”。

## 6. 下一步 / 待办

- 完成数据清洗与格式标准化脚本
- 搭建一个简单的人工校验界面（或 CSV 导出/导入流程）
- 扩展评估脚本以运行 LLMs 对最终数据集的测评

## 7. 联系与贡献

欢迎以 Issue 或 PR 方式贡献。若需要加入专有/受限资料，请先在本地处理并遵守版权与合规要求。

---

（本文件最后更新：2026-02-04）

```
