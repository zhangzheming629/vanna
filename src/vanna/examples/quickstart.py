"""
Vanna example using AnthropicLlmService

Loads environment from .env

Run:
  cd d:/code/vanna/src/vanna/examples
  python quickstart.py
"""

import asyncio
import importlib.util
import os
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================
# CRITICAL: Setup path BEFORE any vanna imports
# ============================================
# Add src (PARENT of vanna) at position 0
src_path = r"d:\code\vanna\src"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Clear any cached vanna modules BEFORE importing anything
for mod in list(sys.modules):
    if mod.startswith('vanna'):
        del sys.modules[mod]

# Now test if ToolRegistry has register
try:
    from vanna.core.registry import ToolRegistry
    tr = ToolRegistry()
    if hasattr(tr, 'register'):
        print("Using source vanna (with register)")
    else:
        print("Warning: source doesn't have register method")
except Exception as e:
    print(f"Error: {e}")


def ensure_env() -> None:
    if importlib.util.find_spec("dotenv") is not None:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)
    else:
        print("[warn] python-dotenv not installed.")

    if not os.getenv("ANTHROPIC_AUTH_TOKEN"):
        print("[error] ANTHROPIC_AUTH_TOKEN is not set.")
        sys.exit(1)


async def main() -> None:
    ensure_env()

    from dotenv import load_dotenv
    load_dotenv()

    model = os.getenv("ANTHROPIC_MODEL", "MiniMax-M2.1")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
    api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")

    print(f"Model: {model}")
    print(f"Base URL: {base_url}")
    print("\n=== Agent Demo ===\n")

    from vanna import AgentConfig, Agent, User
    from vanna.integrations.anthropic import AnthropicLlmService
    from vanna.core.registry import ToolRegistry
    from vanna.tools import ListFilesTool, ReadFileTool, WriteFileTool, SearchFilesTool
    from vanna.integrations.local import LocalFileSystem
    from vanna.integrations.local.agent_memory.in_memory import DemoAgentMemory
    from vanna.core.user import UserResolver, RequestContext

    llm = AnthropicLlmService(model=model, api_key=api_key, base_url=base_url)
    file_system = LocalFileSystem("./data")
    tool_registry = ToolRegistry()
    # 注册文件操作工具
    tool_registry.register(ListFilesTool(file_system=file_system))
    tool_registry.register(ReadFileTool(file_system=file_system))
    tool_registry.register(WriteFileTool(file_system=file_system))
    tool_registry.register(SearchFilesTool(file_system=file_system))
    agent_memory = DemoAgentMemory()

    # LocalFileSystem 会为每个用户创建一个隔离的目录
    # 当前用户 ID 是 "anonymous"，所以：
    # anonymous → SHA256 哈希 → 2f183a4e64493af3

    #     目录结构
    # data/
    # ├── 2f183a4e64493af3/    # 用户 "anonymous" 的目录
    # │   └── 午饭清单.md       # 创建的文件
    # ├── [其他用户hash]/       # 其他用户的目录
    # │   └── ...

    # 作用
    # 这是一个 用户隔离 机制：

    # 每个用户只能看到自己的文件
    # 用户A创建的文件不会暴露给用户B
    # 通过用户ID哈希实现目录隔离

    class SimpleUserResolver(UserResolver):
        async def resolve_user(self, context: RequestContext) -> User:
            return User(id="anonymous", username="anonymous")

    user_resolver = SimpleUserResolver()

    agent = Agent(
        llm_service=llm,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
        config=AgentConfig(stream_responses=True, auto_save_conversations=False),
    )

    request_context = RequestContext()
    # question = "Say OK"
    question = "直接创建一个md格式的文件，内容是午饭清单"
    
    print(f"Question: {question}\nAnswer: ", end="")

    async for component in agent.send_message(
        request_context=request_context,
        message=question,
        conversation_id="demo",
    ):
        rich = getattr(component, "rich_component", None)
        if rich:
            content = (getattr(rich, "content", None) or
                      getattr(rich, "text", None) or
                      getattr(rich, "markdown", None))
            if content:
                print(content, end="", flush=True)

    print("\n\nDone!")


if __name__ == "__main__":
    asyncio.run(main())