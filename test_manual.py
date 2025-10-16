"""
Manual test script to verify the NYTimes API wrapper works.

Run this before connecting to Claude Desktop to catch any API issues early.
"""

from src.nytimes_mcp_server.nyt_api import NYTimesBookAPI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_api_key():
    """First, verify the API key is loaded correctly."""
    api_key = os.getenv("NYTIMES_API_KEY")
    if api_key:
        print(f"✓ API key found (length: {len(api_key)} characters)")
        print(f"  First 10 chars: {api_key[:10]}...")
    else:
        print("✗ API key not found!")
        return False
    return True


def test_best_sellers():
    """Test getting books from a best sellers list."""
    api = NYTimesBookAPI()
    
    print("\nTest 1: Get Best Sellers List")
    print("=" * 60)
    
    try:
        results = api.get_best_sellers(
            list_name="combined-print-and-e-book-fiction"
        )
        
        print(f"✓ List: {results['display_name']}")
        print(f"  Date: {results['bestsellers_date']}")
        print(f"  Number of books: {len(results['books'])}")
        print(f"\nTop 3 books:")
        
        for book in results['books'][:3]:
            print(f"\n  #{book['rank']} - {book['title']}")
            print(f"       by {book['author']}")
            print(f"       Weeks on list: {book['weeks_on_list']}")
        
        api.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        api.close()
        return False


def test_overview():
    """Test getting the overview of all lists."""
    api = NYTimesBookAPI()
    
    print("\nTest 2: Get Best Sellers Overview")
    print("=" * 60)
    
    try:
        results = api.get_best_sellers_overview()
        
        print(f"✓ Found {results['num_lists']} lists")
        print(f"  Date: {results['bestsellers_date']}")
        print(f"\nFirst 3 lists:")
        
        for i, lst in enumerate(results['lists'][:3], 1):
            print(f"\n  {i}. {lst['display_name']}")
            print(f"     List name: {lst['list_name']}")
            print(f"     Top book: {lst['books'][0]['title'] if lst['books'] else 'N/A'}")
        
        api.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        api.close()
        return False


def test_history_search():
    """Test searching the best sellers history."""
    api = NYTimesBookAPI()
    
    print("\nTest 3: Search Best Sellers History")
    print("=" * 60)
    
    # Try searching by author
    print("\nSearching for books by Stephen King...")
    
    try:
        results = api.search_best_sellers_history(author="Stephen King")
        
        print(f"✓ Found {results['num_results']} results")
        
        if results['results']:
            first = results['results'][0]
            print(f"\nFirst result:")
            print(f"  Title: {first['title']}")
            print(f"  Author: {first['author']}")
            print(f"  Publisher: {first['publisher']}")
            
            if first['ranks_history']:
                print(f"  Appeared on {len(first['ranks_history'])} list(s)")
        
        api.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        api.close()
        return False


if __name__ == "__main__":
    print("NYTimes Books API - Diagnostic Tests")
    print("=" * 60)
    
    # Test 1: Check API key
    if not test_api_key():
        print("\n⚠️  Fix your API key configuration before continuing")
        exit(1)
    
    # Test 2: Best sellers list (most reliable)
    if not test_best_sellers():
        print("\n⚠️  Basic API connectivity failed")
        print("\nTroubleshooting:")
        print("1. Verify your API key is valid at https://developer.nytimes.com/")
        print("2. Check that you've enabled the Books API for your key")
        print("3. Try regenerating your API key")
        print("4. Wait a few minutes - new keys may take time to activate")
        exit(1)
    
    # Test 3: Overview
    test_overview()
    
    # Test 4: History search
    test_history_search()
    
    print("\n" + "=" * 60)
    print("✓ API tests complete!")
    print("=" * 60)