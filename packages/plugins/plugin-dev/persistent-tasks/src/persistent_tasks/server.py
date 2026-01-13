"""MCP server for persistent task management."""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from persistent_tasks.storage import (
    TaskStore,
    TaskStatus,
    Priority,
    get_tasks_file,
)


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("persistent-tasks")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="add_task",
                description="Add a new task with optional priority and dependencies",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "priority": {"type": "string", "enum": ["high", "medium", "low"], "default": "medium"},
                        "dependencies": {"type": "array", "items": {"type": "integer"}, "default": []},
                        "description": {"type": "string", "default": ""},
                    },
                    "required": ["title"],
                },
            ),
            Tool(
                name="list_tasks",
                description="List all tasks with optional status filter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["pending", "in-progress", "review", "done", "deferred", "cancelled"]},
                        "blocked": {"type": "boolean", "description": "Only show blocked tasks"},
                    },
                },
            ),
            Tool(
                name="get_task",
                description="Get a specific task by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="update_task",
                description="Update task fields (status, priority, title, description, dependencies)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Task ID"},
                        "status": {"type": "string", "enum": ["pending", "in-progress", "review", "done", "deferred", "cancelled"]},
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "dependencies": {"type": "array", "items": {"type": "integer"}},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="next_task",
                description="Get the next task to work on based on priority and dependencies",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start": {"type": "boolean", "description": "Mark task as in-progress"},
                    },
                },
            ),
            Tool(
                name="remove_task",
                description="Remove a task by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        try:
            store = TaskStore(get_tasks_file())
        except RuntimeError as e:
            return [TextContent(type="text", text=f"Storage error: {e}")]

        try:
            if name == "add_task":
                task = store.add_task(
                    title=arguments["title"],
                    priority=Priority(arguments.get("priority", "medium")),
                    dependencies=arguments.get("dependencies", []),
                    description=arguments.get("description", ""),
                )
                return [TextContent(type="text", text=f"Added task #{task.id}: {task.title}")]

            elif name == "list_tasks":
                tasks = store.tasks
                status_filter = arguments.get("status")
                if status_filter:
                    tasks = [t for t in tasks if t.status.value == status_filter]
                if arguments.get("blocked"):
                    tasks = [t for t in tasks if store.is_blocked(t)]

                if not tasks:
                    return [TextContent(type="text", text="No tasks found.")]

                lines = []
                for t in tasks:
                    blocked = " [BLOCKED]" if store.is_blocked(t) else ""
                    deps = f" (deps: {t.dependencies})" if t.dependencies else ""
                    lines.append(f"#{t.id} [{t.status.value}] [{t.priority.value}] {t.title}{deps}{blocked}")
                return [TextContent(type="text", text="\n".join(lines))]

            elif name == "get_task":
                task = store.get_task(arguments["task_id"])
                if not task:
                    return [TextContent(type="text", text=f"Task #{arguments['task_id']} not found")]
                blocked = " [BLOCKED]" if store.is_blocked(task) else ""
                return [TextContent(type="text", text=f"#{task.id} [{task.status.value}] [{task.priority.value}] {task.title}{blocked}\n{task.description or '(no description)'}")]

            elif name == "update_task":
                task_id = arguments["task_id"]
                # Copy updates without task_id to avoid mutating input
                updates = {k: v for k, v in arguments.items() if k != "task_id"}
                # Convert string enums to actual enums
                if "status" in updates:
                    updates["status"] = TaskStatus(updates["status"])
                if "priority" in updates:
                    updates["priority"] = Priority(updates["priority"])
                task = store.update_task(task_id, **updates)
                if not task:
                    return [TextContent(type="text", text=f"Task #{task_id} not found")]
                return [TextContent(type="text", text=f"Updated task #{task.id}: {task.title}")]

            elif name == "next_task":
                task = store.find_next_task()
                if not task:
                    return [TextContent(type="text", text="No actionable tasks. All done or blocked.")]
                if arguments.get("start"):
                    task = store.update_task(task.id, status=TaskStatus.IN_PROGRESS) or task
                return [TextContent(type="text", text=f"Next: #{task.id} [{task.status.value}] {task.title}\n{task.description or ''}")]

            elif name == "remove_task":
                task = store.get_task(arguments["task_id"])
                if not task:
                    return [TextContent(type="text", text=f"Task #{arguments['task_id']} not found")]
                title = task.title
                store.remove_task(arguments["task_id"])
                return [TextContent(type="text", text=f"Removed #{arguments['task_id']}: {title}")]

            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except ValueError as e:
            return [TextContent(type="text", text=f"Error: {e}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Internal error: {type(e).__name__}: {e}")]

    return server


async def main() -> None:
    """Run the MCP server."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
