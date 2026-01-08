"""
Test script to verify hybrid search is working
"""
import asyncio
from my_os import vector_db, knowledge

async def test_hybrid_search():
    print("Testing Hybrid Search Implementation\n")
    print("=" * 60)

    # Test 1: Verify SearchType is set
    print(f"Vector DB Search Type: {vector_db.search_type}")
    assert str(vector_db.search_type) == "SearchType.hybrid", "Search type not set to hybrid!"
    print("✅ Hybrid search type confirmed\n")

    # Test 2: Perform a search query
    print("Performing test search for 'Cirkelline'...")
    results = vector_db.search("Cirkelline", limit=3)

    if results:
        print(f"✅ Search returned {len(results)} results")
        print("\nSample results:")
        for i, result in enumerate(results[:2], 1):
            name = getattr(result, 'name', None) or getattr(result, 'content', 'N/A')
            print(f"{i}. {str(name)[:60]}...")
    else:
        print("⚠️  No results found (knowledge base may be empty)")

    print("\n" + "=" * 60)
    print("Hybrid Search Test Complete!")
    print("\nWhat hybrid search does:")
    print("• Semantic search: Finds meaning/concepts")
    print("• Keyword search: Finds exact term matches")
    print("• Combined: Better, more comprehensive results")

if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
