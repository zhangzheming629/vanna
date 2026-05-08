"""
Vanna PostgreSQL example using PostgreSQL database.

Uses LLM with PostgreSQL database.
This example connects to PostgreSQL and queries table counts.

Run:
  cd d:/code/vanna/src/vanna/examples
  python postgres.py
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

    # Check API key
    if not os.getenv("ANTHROPIC_AUTH_TOKEN"):
        print("[error] ANTHROPIC_AUTH_TOKEN is not set.")
        sys.exit(1)

    # Check PostgreSQL connection info
    required = ["PG_HOST", "PG_DATABASE"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"[error] Missing env vars: {missing}")
        print("Please set: PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE")
        sys.exit(1)


def get_postgres_connection():
    """Create PostgreSQL connection string."""
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    user = os.getenv("PG_USER", "postgres")
    password = os.getenv("PG_PASSWORD", "")
    database = os.getenv("PG_DATABASE", "postgres")

    # Build connection URL
    if password:
        conn_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    else:
        conn_url = f"postgresql+asyncpg://{user}@{host}:{port}/{database}"

    return conn_url


def get_schema() -> str:
    """Get PostgreSQL schema to use.

    Returns:
        Schema name. Default is 'public'. Can be overridden by PG_SCHEMA env var.
    """
    return os.getenv("PG_SCHEMA", "public")


async def main() -> None:
    ensure_env()

    from dotenv import load_dotenv
    load_dotenv()

    model = os.getenv("ANTHROPIC_MODEL", "MiniMax-M2.1")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
    api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")

    print(f"Model: {model}")
    print(f"Base URL: {base_url}")

    # Get PostgreSQL connection info
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_database = os.getenv("PG_DATABASE", "postgres")
    pg_schema = get_schema()  # Get schema

    print(f"PostgreSQL: {pg_host}:{pg_port}/{pg_database}")
    print(f"Schema: {pg_schema}")
    print("\n=== PostgreSQL Demo ===\n")

    from vanna import AgentConfig, Agent, User
    from vanna.integrations.anthropic import AnthropicLlmService
    from vanna.core.registry import ToolRegistry
    from vanna.tools import RunSqlTool
    from vanna.integrations.postgres import PostgresRunner
    from vanna.integrations.local.agent_memory.in_memory import DemoAgentMemory
    from vanna.core.user import UserResolver, RequestContext

    # Create PostgreSQL runner with schema support
    try:
        postgres_runner = PostgresRunner(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
        )
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return

    # Optional: Set schema after connection
    if pg_schema != "public":
        try:
            # Set the search path to use the specified schema
            conn = postgres_runner.psycopg2.connect(
                host=pg_host,
                port=pg_port,
                database=pg_database,
                user=os.getenv("PG_USER"),
                password=os.getenv("PG_PASSWORD"),
            )
            cursor = conn.cursor()
            cursor.execute(f'SET search_path TO {pg_schema}')
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Schema set to: {pg_schema}")
        except Exception as e:
            print(f"Warning: Could not set schema: {e}")

    # Create tool registry with SQL tool
    tool_registry = ToolRegistry()
    tool_registry.register(RunSqlTool(sql_runner=postgres_runner))

    # Create LLM service
    llm = AnthropicLlmService(model=model, api_key=api_key, base_url=base_url)

    # Setup memory and user resolver
    agent_memory = DemoAgentMemory()

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

    # Test question: how many tables
    question = "列出数据库中的表"
    print(f"Question: {question}")
    print("Answer:")

    request_context = RequestContext()

    async for component in agent.send_message(
        request_context=request_context,
        message=question,
        conversation_id="postgres-demo",
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

    print("\n\nDone!")


    # Test question: 分类查询foods
    question = "查询foods表，按category分类显示"
    print(f"Question: {question}")
    print("Answer:")

    request_context = RequestContext()

    async for component in agent.send_message(
        request_context=request_context,
        message=question,
        conversation_id="postgres-demo",
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

    print("\n\nDone!")


if __name__ == "__main__":
    asyncio.run(main())