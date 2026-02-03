# Aluminum Industry Knowledge Benchmark: 铝工业知识评测基准

> **注意**：本项目目前正在建设中。仅部分实现了预处理、OCR和问题生成模块。

## 1. 项目概述

AlElec 是一个致力于构建用于评测大语言模型（LLMs）在铝工业领域知识水平的基准数据集的项目。

我们的目标是创建一套来源于教材、专著和综述（例如《铝冶炼工艺》）等权威来源的标准化问答对。数据集涵盖铝冶金的各个方面，包括：
- 历史与发展
- 性质与用途
- 原料与前处理工艺
- 电解原理与工艺流程
- 设备与关键部件
- 工艺参数与控制
- 环境治理
- 智能制造

数据集构建流程遵循 **“LLM辅助生成 + 人工校验”** 的工作流。

## 2. 方法论

构建流程包含以下阶段：
1.  **数据收集**：收集权威PDF文档（存储在 `materials/` 中）。
2.  **预处理**：将PDF文档拆分为单页，以利于细粒度的OCR和后续处理。
3.  **OCR与数字化**：使用OCR工具将PDF页面转换为机器可读文本。
4.  **问题生成**：使用LLM（通过RAG技术）从提取的文本中生成结构化问题（涵盖事实类、工艺类、推理类）。

## 3. 项目结构

```
AlElec/
├── dataset/                # 数据集管理脚本
│   └── dataset.py          # 基于提示词调用LLM生成问题的脚本
├── materials/              # 源PDF文件资料
│   ├── raw/                # 原始PDF输入
│   └── processed/          # 预处理/拆分后的PDF页面及OCR缓存
├── output/                 # 生成的问题和结果
├── raw/                    # 预处理和OCR脚本
│   ├── SlicePDF.py         # 用于将PDF拆分为单页文件的脚本
│   └── OCR.py              # 对拆分后的页面执行OCR识别的脚本
├── utils/
│   └── process_json.py     # 用于合并问题和标签的工具
├── input.txt               # 输入提示词或文本数据
├── questions.json          # 示例/临时生成的问题文件
├── requirements.txt        # Python依赖
└── 方案.md                 # 详细的项目计划和设计文档
```

## 4. 使用方法

### 前置要求
安装所需的依赖项：
```bash
pip install -r requirements.txt
```

### 第一步：预处理（拆分PDF）
将源PDF拆分为单独的页面进行处理。
```bash
# 示例
python -m raw.SlicePDF "path/to/your/document.pdf"
```
运行后，将在 `materials/processed/` 目录下创建一个与文件名同名的文件夹，其中包含拆分后的按页PDF文件。

### 第二步：光学字符识别（OCR）
运行OCR脚本将拆分后的PDF转换为文本数据。
```bash
python raw/OCR.py
```
*注意：该脚本目前通过API接口调用外部OCR服务，请确保配置了正确的访问令牌。*

### 第三步：问题生成
从处理后的文本中自动生成问题。

```bash
# 生成事实类/工艺类客观题（单选+判断）
python dataset/dataset.py "path/to/text.txt" --mode objective --output output/objective.json

# 生成推理类主观题（故障诊断/因果分析）
python dataset/dataset.py "path/to/text.txt" --mode reasoning --output output/reasoning.json
```

*提示：可以通过 `python dataset/dataset.py --help` 查看更多参数选项。*

### 第四步：数据合并（可选）
如果需要将生成的问题与人工标注的标签合并。
```bash
python utils/process_json.py
```

## 5. 路线图
- [x] PDF 预处理（页面拆分）
- [x] OCR 集成
- [x] 基础问题生成
- [ ] 数据清洗与格式统一
- [ ] 人工校验接口/工具
- [ ] 最终数据集组装与导出

## 许可协议
[License Information]
