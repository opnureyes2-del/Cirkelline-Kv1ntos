"""Test if knowledge filters actually work"""
import asyncio
from my_os import knowledge, get_private_knowledge_filters

async def test_filters():
    print("\n🧪 TESTING KNOWLEDGE FILTERS\n")

    # Ivo's user_id
    ivo_id = "cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e"

    # Rasmus's user_id
    rasmus_id = "2c0a495c-3e56-4f12-ba68-a2d89e2deb71"

    # Test filter for Ivo
    ivo_filters = get_private_knowledge_filters(ivo_id)
    print(f"Ivo's filters: {ivo_filters}")

    # Search with Ivo's filters
    print("\nSearching with Ivo's filters...")
    try:
        # Try searching knowledge with filters
        results = await knowledge.async_search(
            query="uploaded file",
            filters=ivo_filters
        )
        print(f"   Found {len(results)} results for Ivo")
        for r in results:
            print(f"   - {r}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

    # Test filter for Rasmus
    rasmus_filters = get_private_knowledge_filters(rasmus_id)
    print(f"\nRasmus's filters: {rasmus_filters}")

    # Search with Rasmus's filters
    print("\nSearching with Rasmus's filters...")
    try:
        results = await knowledge.async_search(
            query="uploaded file",
            filters=rasmus_filters
        )
        print(f"   Found {len(results)} results for Rasmus")
        for r in results:
            print(f"   - {r}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_filters())
