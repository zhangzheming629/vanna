"""
Vanna SQLite example using SQLite database.

Uses LLM with SQLite database.
This example demonstrates SQL queries with SQLite database.

Run:
  cd d:/code/vanna/src/vanna/examples
  python sqllite.py
"""

import asyncio
import importlib.util
import os
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================
# Setup path BEFORE any vanna imports
# ============================================
src_path = r"d:\code\vanna\src"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Clear any cached vanna modules
for mod in list(sys.modules):
    if mod.startswith('vanna'):
        del sys.modules[mod]


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
    print("\n=== SQLite Demo ===\n")

    from vanna import AgentConfig, Agent, User
    from vanna.integrations.anthropic import AnthropicLlmService
    from vanna.core.registry import ToolRegistry
    from vanna.tools import RunSqlTool, VisualizeDataTool
    from vanna.integrations.sqlite import SqliteRunner
    from vanna.integrations.local.agent_memory.in_memory import DemoAgentMemory
    from vanna.core.user import UserResolver, RequestContext


    # 定义数据库文件路径
    # Chinook.sqlite 是一个非常有名的示例数据库（Sample Database），专门用来学习和测试 SQL
    db_path = "d:/code/vanna/Chinook.sqlite"
    # 如果文件不存在，就创建它并初始化表
    if not os.path.exists(db_path):
        import sqlite3
        print(f"Creating sample database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 执行 SQL，创建 Customer 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Customer (
                CustomerId INTEGER PRIMARY KEY,
                FirstName TEXT,
                LastName TEXT,
                Email TEXT,
                Country TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Invoice (
                InvoiceId INTEGER PRIMARY KEY,
                CustomerId INTEGER,
                InvoiceDate TEXT,
                Total REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Track (
                TrackId INTEGER PRIMARY KEY,
                Name TEXT,
                Composer TEXT,
                Milliseconds INTEGER,
                UnitPrice REAL
            )
        """)

        # Insert sample data
        customers = [
            (1, "John", "Doe", "john@email.com", "USA"),
            (2, "Jane", "Smith", "jane@email.com", "UK"),
            (3, "Bob", "Johnson", "bob@email.com", "Canada"),
            (4, "Alice", "Williams", "alice@email.com", "USA"),
            (5, "Charlie", "Brown", "charlie@email.com", "Australia"),
        ]
        cursor.executemany("INSERT INTO Customer VALUES (?, ?, ?, ?, ?)", customers)

        invoices = [
            (1, 1, "2024-01-01", 100.0),
            (2, 2, "2024-01-02", 200.0),
            (3, 1, "2024-01-03", 150.0),
            (4, 3, "2024-01-04", 300.0),
            (5, 2, "2024-01-05", 250.0),
        ]
        cursor.executemany("INSERT INTO Invoice VALUES (?, ?, ?, ?)", invoices)

        tracks = [
            (1, "Hello World", "John Doe", 180000, 0.99),
            (2, "Python Song", "Jane Smith", 200000, 1.29),
            (3, "Code Blues", "Bob Johnson", 240000, 0.99),
            (4, "Algorithm Jazz", "Alice Williams", 300000, 1.49),
            (5, "Binary Reggae", "Charlie Brown", 190000, 0.99),
        ]
        cursor.executemany("INSERT INTO Track VALUES (?, ?, ?, ?, ?)", tracks)

        conn.commit()
        conn.close()
        print("Sample database created!\n")

    print(f"Using database: {db_path}\n")

    # Create LLM service
    llm = AnthropicLlmService(model=model, api_key=api_key, base_url=base_url)

    # Create SQLite runner and tool
    sqlite_runner = SqliteRunner(database_path=db_path)
    tool_registry = ToolRegistry()
    tool_registry.register(RunSqlTool(sql_runner=sqlite_runner))

    # Setup memory
    agent_memory = DemoAgentMemory()

    # User resolver
    class SimpleUserResolver(UserResolver):
        async def resolve_user(self, context: RequestContext) -> User:
            return User(id="user123", username="testuser")

    user_resolver = SimpleUserResolver()

    # Create Agent
    agent = Agent(
        llm_service=llm,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
        config=AgentConfig(
            stream_responses=True,
            auto_save_conversations=False,
        ),
    )

    # Test queries
    # questions = [
    #     "Show me all tables in the database",
    #     "List the first 3 customers",
    #     "How many invoices are there",
    # ]

    questions = [
        "列出数据库中所有的表",
        "列出前3名客户",
        "列出这里有多少发票记录",
    ]

    for q in questions:
        print(f"Question: {q}")
        print("Answer:")

        request_context = RequestContext()

        async for component in agent.send_message(
            request_context=request_context,
            message=q,
            conversation_id="sql-demo",
        ):
            rich = getattr(component, "rich_component", None)
            if rich:
                content = (
                    getattr(rich, "content", None) or
                    getattr(rich, "text", None) or
                    getattr(rich, "markdown", None)
                )
                if content:
                    print(content, end="", flush=True)

        print("\n" + "-" * 50)


if __name__ == "__main__":
    asyncio.run(main())