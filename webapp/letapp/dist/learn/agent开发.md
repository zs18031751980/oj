# AI Agent 开发入门指南

## 课程目标

帮助你理解什么是 AI Agent（智能体），掌握 Agent 的核心概念、架构设计，以及如何从零开始开发一个简单的 AI Agent。无论你是前端开发者还是后端开发者，这门课都能帮你进入 AI Agent 开发的大门。

> **什么是 AI Agent？** AI Agent 是一个能够自主感知环境、思考决策并执行行动的智能程序。它不仅仅是"问答机器人"，而是能像人类助手一样，理解复杂任务、拆解步骤、调用工具、最终完成任务。例如：帮你查天气、订机票、写代码、管理日历的 AI 助手，本质上都是 Agent。

---

## 推荐内容

### 1. Agent 核心概念

#### 什么是 Agent
传统 AI 应用是"你问一句，它答一句"的被动模式。而 Agent 是主动的——你给它一个目标，它自己决定怎么做。

**传统 AI vs Agent**：
| 特性 | 传统 AI（LLM 直接调用） | AI Agent |
|------|------------------------|----------|
| 交互方式 | 一问一答 | 给定目标，自主完成 |
| 记忆能力 | 无（每次对话独立） | 有短期和长期记忆 |
| 工具使用 | 不能 | 可以调用 API、执行代码、操作文件 |
| 规划能力 | 无 | 能拆解任务、制定计划 |
| 执行方式 | 直接生成文本 | 思考→行动→观察→再思考的循环 |

#### Agent 的核心组件
一个完整的 Agent 系统包含以下组件：

```
┌─────────────────────────────────────────┐
│             用户输入（目标）               │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│              1. 感知模块                  │
│          （理解用户意图 + 获取上下文）      │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│              2. 规划模块                  │
│      （拆解任务 → 制定步骤 → 选择策略）     │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│              3. 执行模块                  │
│   ┌──────────┐  ┌──────────┐  ┌────────┐ │
│   │ 调用 LLM  │  │ 调用工具  │  │ 执行代码│ │
│   └──────────┘  └──────────┘  └────────┘ │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│              4. 记忆模块                  │
│   ┌──────────┐  ┌──────────┐  ┌────────┐ │
│   │ 短期记忆  │  │ 长期记忆  │  │ 向量数据库│ │
│   └──────────┘  └──────────┘  └────────┘ │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│              5. 反馈模块                  │
│        （观察结果 → 调整计划 → 继续执行）   │
└─────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│              最终输出（结果）              │
└─────────────────────────────────────────┘
```

---

### 2. 主流 Agent 框架

#### LangChain
LangChain 是最流行的 Agent 开发框架，它提供了丰富的工具集成和 Agent 管理能力。

```python
# 安装：pip install langchain langchain-openai
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.tools import tool

# 1. 定义工具
@tool
def search(query: str) -> str:
    """搜索互联网获取信息"""
    # 这里调用搜索 API
    return f"搜索结果是：关于'{query}'的..."

@tool
def calculate(expression: str) -> str:
    """执行数学计算"""
    return str(eval(expression))

# 2. 初始化 LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)

# 3. 创建 Agent
agent = initialize_agent(
    tools=[search, calculate],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
)

# 4. 运行 Agent
result = agent.invoke("2024年全球人口是多少？比2023年增长了多少百分比？")
print(result)
```

#### 核心概念：ReAct 模式
ReAct（Reasoning + Acting）是 Agent 的思考模式：
1. **Thought（思考）**：Agent 分析当前情况，决定下一步做什么
2. **Action（行动）**：执行一个具体操作（调用工具、查询知识库等）
3. **Observation（观察）**：获取操作结果
4. **循环**：根据观察继续思考，直到完成任务

```python
# ReAct 模式的典型流程
# User: "北京和上海哪个城市人口更多？相差多少？"

# Thought: 我需要查询北京和上海的人口数据
# Action: search("北京人口 2024")
# Observation: 北京人口 2188.6 万

# Thought: 现在查询上海人口
# Action: search("上海人口 2024")
# Observation: 上海人口 2475.8 万

# Thought: 上海人口更多，相差 2475.8 - 2188.6 = 287.2 万
# Action: calculate("2475.8 - 2188.6")
# Observation: 287.2

# Final Answer: 上海人口比北京多，相差约 287.2 万人
```

#### CrewAI
CrewAI 专注于"多 Agent 协作"，让多个 Agent 像团队一样协同工作：

```python
# 安装：pip install crewai
from crewai import Agent, Task, Crew, Process

# 创建多个 Agent
researcher = Agent(
    role="研究员",
    goal="搜集和分析信息",
    backstory="你是一名资深研究员，擅长从各种来源找到准确信息",
    verbose=True,
)

writer = Agent(
    role="写手",
    goal="撰写高质量的文章",
    backstory="你是一名专业写手，能把复杂内容写得通俗易懂",
    verbose=True,
)

# 创建任务
research_task = Task(
    description="研究 AI Agent 的最新发展趋势",
    agent=researcher,
)

write_task = Task(
    description="根据研究成果，撰写一篇面向初学者的 AI Agent 教程",
    agent=writer,
)

# 组建团队并执行
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,  # 顺序执行
)

result = crew.kickoff()
print(result)
```

#### AutoGen（微软）
AutoGen 是微软推出的多 Agent 对话框架，适合构建复杂的多 Agent 系统：

```python
# 安装：pip install pyautogen
import autogen

# 配置 LLM
config_list = [
    {
        "model": "gpt-4",
        "api_key": "your-api-key",
    }
]

# 创建助手 Agent
assistant = autogen.AssistantAgent(
    name="助手",
    llm_config={"config_list": config_list},
)

# 创建用户代理
user_proxy = autogen.UserProxyAgent(
    name="用户",
    human_input_mode="NEVER",
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    },
)

# 发起对话
user_proxy.initiate_chat(
    assistant,
    message="写一个 Python 脚本来分析这份销售数据，并生成可视化图表",
)
```

---

### 3. 动手实现一个简易 Agent

下面我们从头实现一个简单的 Agent，不依赖任何框架，帮助你理解 Agent 的本质：

```python
import json
import requests
from typing import Dict, Any

class SimpleAgent:
    """一个简单的 AI Agent 实现"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.messages = []  # 对话历史（记忆）
        self.tools = {}     # 注册的工具

    def register_tool(self, name: str, func, description: str):
        """注册一个工具"""
        self.tools[name] = {
            "func": func,
            "description": description,
        }

    def call_llm(self, prompt: str) -> str:
        """调用大语言模型"""
        self.messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": self.messages,
            "temperature": 0.7,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
        )
        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def execute_tool(self, tool_name: str, args: str) -> str:
        """执行工具"""
        if tool_name not in self.tools:
            return f"错误：找不到工具 '{tool_name}'"

        try:
            tool = self.tools[tool_name]
            result = tool["func"](args)
            return str(result)
        except Exception as e:
            return f"工具执行失败：{str(e)}"

    def run(self, task: str, max_steps: int = 10) -> str:
        """执行任务"""
        system_prompt = f"""你是一个 AI Agent，可以通过以下工具来完成任务：

{chr(10).join([f'- {name}: {info["description"]}' for name, info in self.tools.items()])}

请按以下格式回复：
THOUGHT: 你的思考过程
ACTION: 工具名称（如果需要执行工具）
ACTION_INPUT: 工具的参数
OBSERVATION: 工具执行结果
...（可以重复思考-行动-观察）
FINAL_ANSWER: 最终答案

如果任务完成，直接输出 FINAL_ANSWER。
如果不需要使用工具，直接输出 FINAL_ANSWER。"""

        self.messages.append({"role": "system", "content": system_prompt})
        step = 0

        while step < max_steps:
            step += 1
            response = self.call_llm(
                f"当前步骤 {step}/{max_steps}。任务：{task}\n请继续执行。"
            )

            # 检查是否应该终止
            if "FINAL_ANSWER:" in response:
                final = response.split("FINAL_ANSWER:")[-1].strip()
                return final

            # 解析工具调用
            if "ACTION:" in response and "ACTION_INPUT:" in response:
                try:
                    action = response.split("ACTION:")[1].split("\n")[0].strip()
                    action_input = response.split("ACTION_INPUT:")[1].strip()
                    observation = self.execute_tool(action, action_input)
                    self.messages.append({
                        "role": "system",
                        "content": f"OBSERVATION: {observation}",
                    })
                except Exception as e:
                    self.messages.append({
                        "role": "system",
                        "content": f"OBSERVATION: 解析工具调用失败：{str(e)}",
                    })

        return "已达到最大执行步数，任务可能未完成。"


# ===== 使用示例 =====

# 1. 定义工具函数
def search_weather(city: str) -> str:
    """查询天气（模拟）"""
    weather_data = {
        "北京": "晴，25°C",
        "上海": "多云，28°C",
        "广州": "阵雨，30°C",
    }
    return weather_data.get(city, f"未找到 {city} 的天气数据")

def calculate(expression: str) -> str:
    """执行数学计算"""
    try:
        return str(eval(expression))
    except:
        return "计算表达式有误"

# 2. 创建 Agent
agent = SimpleAgent(api_key="your-api-key")

# 3. 注册工具
agent.register_tool("weather", search_weather, "查询某个城市的天气，参数：城市名称")
agent.register_tool("calc", calculate, "执行数学计算，参数：数学表达式")

# 4. 执行任务
result = agent.run("北京今天天气怎么样？比上海高多少度？")
print(result)
```

---

### 4. Agent 开发最佳实践

#### 工具设计原则
好的工具是 Agent 高效工作的基础：

1. **单一职责**：每个工具只做一件事
   - 好：`search_web(query)`、`send_email(to, subject, body)`
   - 不好：`do_everything(task_description)`

2. **清晰的描述**：工具的描述直接影响 Agent 能否正确使用它
   ```python
   @tool
   def get_weather(city: str) -> str:
       """获取指定城市的当前天气情况。
       参数 city: 城市名称，如"北京"、"上海"
       返回：天气描述字符串，包含温度、天气状况等"""
       ...
   ```

3. **错误处理**：工具应该能优雅地处理错误
   ```python
   @tool
   def search_database(query: str) -> str:
       try:
           results = db.search(query)
           return format_results(results)
       except Exception as e:
           return f"查询出错：{str(e)}。请尝试使用不同的关键词。"
   ```

#### Prompt 工程技巧
Agent 的行为很大程度上取决于系统提示词：

```python
SYSTEM_PROMPT = """你是一个专业的编程助手 Agent。

## 你的能力
- 你可以编写、调试和优化代码
- 你可以执行终端命令
- 你可以读写文件

## 工作方式
1. 先理解用户的需求
2. 制定实现方案
3. 分步执行
4. 验证结果

## 重要规则
- 执行任何有风险的操作前，先询问用户确认
- 如果遇到错误，分析原因并尝试修复
- 保持代码简洁、注释清晰
- 优先使用已有的工具和库

## 输出格式
THOUGHT: <你的思考>
ACTION: <工具名称>
ACTION_INPUT: <参数>
OBSERVATION: <结果>
...循环直到任务完成
FINAL_ANSWER: <最终结果>"""
```

#### 安全考虑
开发 Agent 时需要注意安全问题：

```python
class SafeAgent:
    """安全的 Agent 实现"""

    def __init__(self):
        self.allowed_commands = [
            "ls", "cat", "pwd", "echo",
            "python", "node", "npm test",
        ]
        self.blocked_patterns = [
            "rm -rf", "sudo", "chmod 777",
            "> /dev", "mkfs", "dd if=",
        ]

    def validate_command(self, command: str) -> bool:
        """验证命令是否安全"""
        # 检查是否在黑名单中
        for pattern in self.blocked_patterns:
            if pattern in command.lower():
                return False

        # 检查是否在白名单中
        base_cmd = command.strip().split()[0]
        return base_cmd in self.allowed_commands

    def execute_safely(self, command: str) -> str:
        """安全执行命令"""
        if not self.validate_command(command):
            return f"命令 '{command}' 被安全策略阻止"

        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            return "命令执行超时"
        except Exception as e:
            return f"执行出错：{str(e)}"
```

---

### 5. 多 Agent 协作

#### 为什么需要多 Agent
- **专业化**：每个 Agent 专注于一个领域
- **并行处理**：多个 Agent 同时工作，提高效率
- **质量保证**：一个 Agent 的输出可以被另一个检查和改进

#### 多 Agent 架构模式

**模式一：主管-工人模式**
```
                  ┌──────────┐
                  │  主管Agent │
                  │（分配任务） │
                  └─────┬────┘
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │工人Agent1│   │工人Agent2│   │工人Agent3│
    │  (搜索)  │   │  (分析)  │   │  (生成)  │
    └─────────┘   └─────────┘   └─────────┘
```

**模式二：流水线模式**
```
用户输入 → Agent A(理解) → Agent B(规划) → Agent C(执行) → Agent D(验证) → 输出
```

**模式三：辩论模式**
```
用户输入
    ↓
Agent A(正方) ←→ Agent B(反方)
    ↓
Agent C(裁判/总结)
    ↓
最终输出
```

---

### 6. Agent 的记忆与知识

#### 短期记忆（对话上下文）
Agent 需要记住当前对话中已经说过的话：

```python
from collections import deque

class ShortTermMemory:
    def __init__(self, max_tokens: int = 4000):
        self.messages = deque()
        self.max_tokens = max_tokens
        self.token_count = 0

    def add(self, role: str, content: str):
        estimated_tokens = len(content) // 2  # 粗略估算
        self.messages.append({"role": role, "content": content})
        self.token_count += estimated_tokens

        # 如果超出限制，移除最早的消息
        while self.token_count > self.max_tokens and len(self.messages) > 1:
            oldest = self.messages.popleft()
            self.token_count -= len(oldest["content"]) // 2

    def get_context(self) -> list:
        return list(self.messages)
```

#### 长期记忆（向量数据库）
Agent 需要记住长期的知识，通常使用向量数据库：

```python
# 使用 ChromaDB 作为长期记忆
# 安装：pip install chromadb
import chromadb
from chromadb.utils import embedding_functions

class LongTermMemory:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(
            name="agent_memory",
            embedding_function=embedding_functions.
                OpenAIEmbeddingFunction(api_key="your-key"),
        )

    def remember(self, key: str, content: str, metadata: dict = None):
        """存储一条记忆"""
        self.collection.add(
            documents=[content],
            metadatas=[metadata or {}],
            ids=[key],
        )

    def recall(self, query: str, n_results: int = 5) -> list:
        """根据查询回忆相关记忆"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        return results["documents"][0]

    def forget(self, key: str):
        """删除一条记忆"""
        self.collection.delete(ids=[key])
```

#### 知识库检索（RAG）
RAG（检索增强生成）让 Agent 能利用外部知识：

```python
class RAGAgent:
    """带知识库检索的 Agent"""

    def __init__(self, knowledge_base_path: str):
        self.knowledge_base = self.load_knowledge(knowledge_base_path)

    def load_knowledge(self, path: str) -> Dict[str, str]:
        """加载知识库（简化版）"""
        import os
        knowledge = {}
        for file in os.listdir(path):
            if file.endswith(".md"):
                with open(os.path.join(path, file), "r", encoding="utf-8") as f:
                    knowledge[file] = f.read()
        return knowledge

    def retrieve(self, query: str, top_k: int = 3) -> list:
        """检索相关知识（使用简单的关键词匹配）"""
        # 实际项目中应该使用向量检索
        keywords = set(query.lower().split())
        scores = []

        for doc_name, content in self.knowledge_base.items():
            content_lower = content.lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores.append((score, doc_name, content[:500]))

        scores.sort(reverse=True)
        return [content for _, _, content in scores[:top_k]]

    def generate_with_context(self, query: str) -> str:
        """结合检索结果生成回答"""
        contexts = self.retrieve(query)
        context_text = "\n\n".join(contexts)

        prompt = f"""基于以下知识回答用户的问题：

相关知识：
{context_text}

用户问题：{query}

请用中文回答，如果知识库中没有相关信息，请如实告知。"""

        return self.call_llm(prompt)  # 调用大模型
```

---

### 7. Agent 实战：代码审查助手

下面是一个完整的 Agent 实战案例 —— 自动代码审查助手：

```python
import os
import subprocess
from typing import List

class CodeReviewAgent:
    """代码审查 Agent"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.issues = []

    def analyze_code(self, file_path: str) -> List[str]:
        """分析代码文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 使用 LLM 进行代码审查
        prompt = f"""请审查以下代码，找出潜在的问题：

代码文件：{file_path}

```python
{content}
```

请检查以下方面：
1. 代码风格和命名规范
2. 潜在的安全漏洞
3. 性能问题
4. 错误处理是否完善
5. 代码可维护性

请按以下格式输出：
- 问题类别 | 行号 | 描述 | 建议修改方案"""

        response = self.call_llm(prompt)
        return self.parse_review(response)

    def run_linter(self, file_path: str) -> List[str]:
        """运行静态代码检查"""
        try:
            result = subprocess.run(
                ["pylint", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.split("\n") if result.stdout else []
        except:
            return []

    def run_tests(self, test_path: str) -> bool:
        """运行单元测试"""
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0
        except:
            return False

    def review(self, file_path: str, run_tests: bool = False) -> dict:
        """执行完整的代码审查"""
        report = {
            "file": file_path,
            "linter_issues": [],
            "code_issues": [],
            "test_results": None,
        }

        # 1. 运行 linter
        report["linter_issues"] = self.run_linter(file_path)

        # 2. AI 代码审查
        report["code_issues"] = self.analyze_code(file_path)

        # 3. 运行测试
        if run_tests:
            test_path = file_path.replace(".py", "_test.py")
            if os.path.exists(test_path):
                report["test_results"] = self.run_tests(test_path)

        return report

    def generate_report(self, report: dict) -> str:
        """生成审查报告"""
        lines = []
        lines.append(f"# 代码审查报告：{report['file']}\n")

        if report["linter_issues"]:
            lines.append("## Linter 发现的问题")
            for issue in report["linter_issues"][:10]:
                if issue.strip():
                    lines.append(f"- {issue.strip()}")

        if report["code_issues"]:
            lines.append("\n## AI 审查发现的问题")
            for issue in report["code_issues"]:
                lines.append(f"- {issue}")

        if report["test_results"] is not None:
            lines.append(f"\n## 测试结果")
            lines.append(f"测试{'通过' if report['test_results'] else '失败'}")

        return "\n".join(lines)

    def call_llm(self, prompt: str) -> str:
        """调用大模型（简化版）"""
        # 实际项目中替换为真实的 API 调用
        return "模拟审查结果"
```

---

## 练习建议

1. **从简单的开始**：先使用 LangChain 或直接调用 LLM API，实现一个能回答问题和执行简单计算的 Agent
2. **逐步增加工具**：为你的 Agent 添加更多工具，如天气查询、网页搜索、文件操作等
3. **尝试多 Agent**：使用 CrewAI 创建一个"研究团队"，包含研究员、写手和编辑三个 Agent
4. **接入实际 API**：让你的 Agent 能调用真实的 API（如 GitHub API、Notion API、Slack API 等）
5. **本地知识库**：为 Agent 添加 RAG 能力，让它能基于你自己的文档回答问题
6. **部署上线**：使用 FastAPI 把你的 Agent 包装成一个 Web 服务，提供 API 接口
7. **安全加固**：研究 Agent 的安全性，实现输入验证、命令白名单、速率限制等机制
8. **参与开源**：在 GitHub 上阅读 LangChain、AutoGen 等项目的源码，学习优秀的设计模式
