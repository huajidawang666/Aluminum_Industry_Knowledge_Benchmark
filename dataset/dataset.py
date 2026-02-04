"""工具脚本：根据铝冶炼提示词模板调用 ChatGPT API 生成题目数据

功能：
- 根据输入文本自动拼装客观题（单选/判断）或推理题提示词
- 可选直接调用 OpenAI Chat Completions API，期望返回 Json 题目列表
- 支持 dry-run，仅输出提示词，便于人工验证

注意：
- 需要配置 OPENAI_API_KEY 环境变量
- 默认模型为 gpt-4o-mini，可通过 --model 覆盖
- 生成结果需要人工复核后再进入标注/合并流程
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

try:
   from openai import OpenAI
except ImportError as exc:  # pragma: no cover - 提示依赖缺失
   raise SystemExit(
      "缺少 openai 依赖，请先运行 `pip install -r requirements.txt`"
   ) from exc


# --------------------------- prompt builders ---------------------------

def build_objective_prompt(
    input_text: str, single_choice: int = 5, true_false: int = 5
) -> str:
    """生成事实类/工艺类客观题提示词。"""

    return f"""# Role
你是一位有30年工作经验的资深严谨的铝冶炼工业考核专家。

# Task
请阅读下方【参考文本】，从中提取关键知识点，生成{single_choice}道单选题和{true_false}道判断题。

# Input Context
\"\"\"
{input_text}
\"\"\"

# Constraints
1. 严格限制来源：你生成的每一个问题、答案、解析，都必须100%来源于上述【参考文本】，不得使用外部知识。
2. 准确性：干扰选项必须有迷惑性，但不能违背基本物理化学常数（除非文本中提及）。
3. 溯源：在“解析”中必须引用原文具体句子作为证据。

# Output Format(Json)
[
   {{
      "id":1,
      "type":1,  # 1 代表单选题
      "question":"题目描述...,A. ...,B. ...,C. ...,D. ...",
      "answer":"C",
      "explanation":"解析内容...",
      "source_quote":"原文引用的句子..."
   }},
   {{
      "id":2,
      "type":2,  # 2 代表判断题
      "question":"题目描述...",
      "answer":false,
      "explanation":"解析内容...",
      "source_quote":"原文依据..."
   }}
]
"""


def build_reasoning_prompt(input_text: str, count: int = 5) -> str:
    """生成推理类（故障诊断/因果分析）主观题提示词。"""

    return f"""# Role
你是一位有30年工作经验的资深严谨的铝冶炼工业考核专家。

# Task
请阅读下方【参考文本】，根据其中描述的工艺原理、异常现象或操作规程，生成{count}道“故障诊断”或因果分析类简答题。

# Input Context
\"\"\"
{input_text}
\"\"\"

# Constraints
1. 严格限制来源：题目、答案、解析必须100%来源于【参考文本】，不得使用外部知识。
2. 科学性、逻辑性：
   - 题目应描述一种现象，要求回答原因或处理措施。
   - 如果文本仅有现象无原因，请返回 NULL。
   - 参考答案需包含推理步骤。
3. 溯源：解析中必须引用原文句子作为证据。

# Output Format(Json)
   {{
      "id":1,
      "type":3,  # 3 代表简答题
      "question":"在【参考文本】描述的工况下，如果出现...现象，说明了什么问题？应该如何处理？",
      "answer":"参考答案及要点...",
      "explanation":"解析内容...（1. 原因分析：...；2. 处理措施：...）",
      "source_quote":"原文依据..."
   }}
"""

# --------------------------- helpers ---------------------------

def load_text(path: str | Path) -> str:
   content = Path(path).read_text(encoding="utf-8").strip()
   if not content:
      raise ValueError("输入文本为空，请检查文件内容。")
   return content


def strip_code_fences(text: str) -> str:
   """移除 markdown ``` 包裹，便于 JSON 解析。"""

   fence_pattern = re.compile(r"^```[a-zA-Z]*\n|```$", re.MULTILINE)
   return fence_pattern.sub("", text).strip()


def parse_json_content(content: str) -> Any:
   cleaned = strip_code_fences(content)
   try:
      return json.loads(cleaned)
   except json.JSONDecodeError as exc:
      raise ValueError(
         f"模型返回内容不是合法 JSON，请人工检查：\n{content}"
      ) from exc


def save_json(data: Any, path: str | Path) -> None:
   Path(path).parent.mkdir(parents=True, exist_ok=True)
   Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")


def call_chat_completion(prompt: str, model: str, temperature: float, max_tokens: int, api_key: str, base_url: str) -> str:
   """调用 OpenAI Chat Completions API。"""
   client = OpenAI(base_url=base_url,api_key=api_key)
   response = client.chat.completions.create(
      model=model,
      messages=[{"role": "user", "content": prompt}],
      temperature=temperature,
      max_tokens=max_tokens,
   )
   return response.choices[0].message.content or ""


# --------------------------- CLI ---------------------------


def main() -> None:
   parser = argparse.ArgumentParser(
      description="根据输入文本生成铝冶炼考核题提示词并可调用 ChatGPT API。"
   )
   parser.add_argument("input", help="包含参考文本的文件路径")
   parser.add_argument(
      "--mode",
      choices=["objective", "reasoning"],
      default="objective",
      help="生成模式：objective=单选+判断，reasoning=故障诊断简答",
   )
   parser.add_argument("--single-choice", type=int, default=5, help="单选题数量")
   parser.add_argument("--true-false", type=int, default=5, help="判断题数量")
   parser.add_argument("--reasoning-count", type=int, default=5, help="推理题数量")
   parser.add_argument(
      "--model", default="gpt-4o-mini", help="调用的 OpenAI 模型名称"
   )
   parser.add_argument("--temperature", type=float, default=0.2, help="采样温度")
   parser.add_argument("--max-tokens", type=int, default=2000, help="最大返回 tokens")
   parser.add_argument(
      "--output",
      default="./output/result.json",
      type=str,
      help="结果输出路径（Json）。若未指定则打印到 ./output/result.json。",
   )
   parser.add_argument(
      "--dry-run",
      action="store_true",
      help="仅生成提示词，不调用 API，便于人工检查。",
   )
   parser.add_argument(
      "--print-prompt",
      action="store_true",
      help="打印提示词内容（无论是否 dry-run）。",
   )
   parser.add_argument(
      "--api-key",
      type=str,
      default=None,
      help="OpenAI API Key，若未指定则使用环境变量 OPENAI_API_KEY。",
   )
   parser.add_argument(
      "--base-url",
      type=str,
      default="https://api.openai.com/v1",
      help="OpenAI API 基础 URL，默认为官方地址。",
   )

   args = parser.parse_args()

   input_text = load_text(args.input)

   if args.mode == "objective":
      prompt = build_objective_prompt(input_text, args.single_choice, args.true_false)
   else:
      prompt = build_reasoning_prompt(input_text, args.reasoning_count)

   if args.print_prompt or args.dry_run:
      print("\n----- PROMPT BEGIN -----\n")
      print(prompt)
      print("\n----- PROMPT END -----\n")

   if args.dry_run:
      return

   # 调用 API
   content = call_chat_completion(
      prompt=prompt,
      model=args.model,
      temperature=args.temperature,
      max_tokens=args.max_tokens,
      api_key=args.api_key or os.getenv("OPENAI_API_KEY"),
      base_url=args.base_url,
   )

   if not content:
      raise RuntimeError("模型未返回内容，请重试或检查参数。")

   parsed = parse_json_content(content)

   if args.output:
      save_json(parsed, args.output)
      print(f"已保存结果到 {args.output}")
   else:
      print(json.dumps(parsed, ensure_ascii=False, indent=4))

if __name__ == "__main__":
   main()