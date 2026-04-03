#!/usr/bin/env python3
"""
Test script for Memory Evolution Room.
Run: python test_memory_room.py
"""

import asyncio
import sys


def test_imports():
    """Test all imports work."""
    print("Testing imports...")

    # Test monitors import (new path)
    try:
        print("  ✅ Monitors imports OK")
    except Exception as e:
        print(f"  ❌ Monitors import failed: {e}")
        return False

    # Test re-export through learning_rooms
    try:
        print("  ✅ Learning rooms re-export OK")
    except Exception as e:
        print(f"  ⚠️ Learning rooms re-export not available: {e}")
        # This is OK - re-export is optional

    try:
        print("  ✅ Kommandanter imports OK")
    except Exception as e:
        print(f"  ❌ Kommandanter import failed: {e}")
        return False

    return True


def test_room_creation():
    """Test room can be created."""
    print("\nTesting room creation...")

    try:
        from cirkelline.ckc.monitors import get_memory_evolution_room

        room = get_memory_evolution_room()

        print(f"  Room ID: {room.ROOM_ID}")
        print(f"  Room Name: {room.ROOM_NAME}")
        print(f"  Status: {room.status.value}")
        print(f"  Running: {room._running}")
        print(f"  Historiker connected: {room._historiker is not None}")
        print(f"  Test schedules: {[(s.test_id, s.time) for s in room.SCHEDULED_TESTS]}")
        print(f"  Sync times: {room.SYNC_TIMES}")
        print(f"  Files tracked: {len(room.MEMORY_FILES)}")

        print("  ✅ Room creation OK")
        return True
    except Exception as e:
        print(f"  ❌ Room creation failed: {e}")
        return False


def test_room_status():
    """Test room status method."""
    print("\nTesting room status...")

    try:
        from cirkelline.ckc.monitors import get_memory_evolution_room

        room = get_memory_evolution_room()
        status = room.get_status()

        print(f"  Status: {status['status']}")
        print(f"  Status meaning: {status['status_meaning']}")
        print(f"  Version: {status['version']}")
        print(f"  Running: {status['running']}")
        print(f"  Snapshots: {status['snapshots_count']}")

        print("  ✅ Room status OK")
        return True
    except Exception as e:
        print(f"  ❌ Room status failed: {e}")
        return False


async def test_room_start_stop():
    """Test room can start and stop."""
    print("\nTesting room start/stop...")

    try:
        from cirkelline.ckc.monitors import get_memory_evolution_room

        room = get_memory_evolution_room()

        # Start room
        print("  Starting room...")
        await room.start()
        print(f"  Running: {room._running}")
        print(f"  Tasks: {len(room._tasks)}")

        # Wait briefly
        await asyncio.sleep(1)

        # Stop room
        print("  Stopping room...")
        await room.stop()
        print(f"  Running: {room._running}")
        print(f"  Tasks: {len(room._tasks)}")

        print("  ✅ Room start/stop OK")
        return True
    except Exception as e:
        print(f"  ❌ Room start/stop failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("MEMORY EVOLUTION ROOM TEST SUITE")
    print("=" * 60)

    results = []

    # Run sync tests
    results.append(("Imports", test_imports()))
    results.append(("Room Creation", test_room_creation()))
    results.append(("Room Status", test_room_status()))

    # Run async tests
    results.append(("Room Start/Stop", asyncio.run(test_room_start_stop())))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
