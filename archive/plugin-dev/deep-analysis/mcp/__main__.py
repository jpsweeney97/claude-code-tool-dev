"""Entry point for running as a module: python -m server"""

from server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
