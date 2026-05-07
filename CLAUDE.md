# Vanna 项目指南

## 项目概述

**Vanna** 是一个将自然语言转换为 SQL 查询的 Python 库（版本 2.0.2）。

### 核心功能
- 自然语言 → SQL → 数据答案
- 企业级安全：用户感知权限、行级安全、审计日志
- 预构建的 `<vanna-chat>` Web 组件
- 流式响应：表格、图表、进度更新

### 技术栈
- **LLM**: OpenAI, Anthropic, Ollama, Azure, Google Gemini, AWS Bedrock, Mistral 等
- **数据库**: PostgreSQL, MySQL, Snowflake, BigQuery, Redshift, SQLite, DuckDB 等
- **Web框架**: FastAPI, Flask
- **Python**: ≥3.9

## 项目结构

```
src/vanna/
├── agents/           # Agent 相关
├── capabilities/   # 核心能力（SQL runner, memory, file system）
├── components/      # UI 组件（rich, simple）
├── core/            # 核心模块
│   ├── agent/      # Agent 实现
│   ├── tool/      # 工具系统
│   ├── user/      # 用户权限系统
│   ├── llm/      # LLM 集成
│   ├── filter/   # 行级安全过滤
│   └── ...
├── integrations/    # 数据库/LLM 集成
├── servers/         # FastAPI/Flask 服务器
└── examples/        # 示例代码
```

## 关键概念

1. **Agent** - 核心推理引擎，处理自然语言并调用工具
2. **Tool** - 可扩展的工具（如 RunSqlTool 执行 SQL）
3. **UserResolver** - 从请求中提取用户身份
4. **行级安全** - 通过 filter 自动过滤查询结果

## 常用命令

```bash
# 安装
pip install vanna

# 运行示例
python -m vanna.examples.anthropic_quickstart

# 开发测试
pytest tests/
```