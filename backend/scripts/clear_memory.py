#!/usr/bin/env python3
"""
CLI script to clear conversation memory and vector database.

Usage:
    python scripts/clear_memory.py --help
    python scripts/clear_memory.py --current         # Clear current conversation only
    python scripts/clear_memory.py --all             # Clear ALL memory (DESTRUCTIVE)
    python scripts/clear_memory.py --persona "Alice" # Clear specific persona memory
"""

import asyncio
import argparse
import sys
import os

# Add the parent directory to the Python path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.conversation_memory import conversation_memory
from app.db.qdrant import qdrant_manager


async def clear_current():
    """Clear only current conversation."""
    print("Clearing current conversation...")
    success = await conversation_memory.clear_current_conversation()
    if success:
        print("✅ Current conversation cleared successfully")
    else:
        print("❌ Failed to clear current conversation")
    return success


async def clear_all():
    """Clear ALL conversation memory including vector database."""
    print("⚠️  WARNING: This will permanently delete ALL conversation history!")
    confirm = input("Type 'CONFIRM' to proceed: ")

    if confirm != 'CONFIRM':
        print("❌ Operation cancelled")
        return False

    print("Clearing all conversation memory...")

    # Initialize database connections
    await qdrant_manager.connect()

    success = await conversation_memory.clear_all_memory()
    if success:
        print("✅ All conversation memory cleared successfully")
    else:
        print("❌ Failed to clear all memory")
    return success


async def clear_persona(persona_name: str):
    """Clear memory for specific persona."""
    print(f"Clearing memory for persona: {persona_name}")

    # Initialize database connections
    await qdrant_manager.connect()

    success = await conversation_memory.clear_persona_memory(persona_name)
    if success:
        print(f"✅ Memory cleared for persona: {persona_name}")
    else:
        print(f"❌ Failed to clear memory for persona: {persona_name}")
    return success


async def show_stats():
    """Show memory statistics."""
    print("Memory Statistics:")
    print("-" * 40)

    # Get conversation memory stats
    stats = conversation_memory.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Check database connection
    await qdrant_manager.connect()
    health = await qdrant_manager.health_check()
    print(f"Vector Database: {'✅ Connected' if health else '❌ Disconnected'}")


async def main():
    parser = argparse.ArgumentParser(
        description="Clear DeskMate conversation memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/clear_memory.py --stats                # Show memory stats
  python scripts/clear_memory.py --current              # Clear current chat only
  python scripts/clear_memory.py --persona "Alice"      # Clear Alice's memory
  python scripts/clear_memory.py --all                  # Clear everything (DESTRUCTIVE)
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--current', action='store_true', help='Clear current conversation only')
    group.add_argument('--all', action='store_true', help='Clear ALL memory (DESTRUCTIVE)')
    group.add_argument('--persona', type=str, help='Clear memory for specific persona')
    group.add_argument('--stats', action='store_true', help='Show memory statistics')

    args = parser.parse_args()

    try:
        if args.stats:
            await show_stats()
        elif args.current:
            await clear_current()
        elif args.all:
            await clear_all()
        elif args.persona:
            await clear_persona(args.persona)

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())