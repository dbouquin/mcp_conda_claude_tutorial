"""
NYTimes Books API wrapper.

This module handles all interactions with the NYTimes Books API, keeping the MCP
server code focused on protocol handling.
"""

import httpx
import os
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class NYTimesBookAPI:
    """
    A wrapper for the NYTimes Books API.
    
    The Books API provides access to NYTimes Best Sellers lists.
    It requires an API key which should be provided via environment variable.
    """
    
    BASE_URL = "https://api.nytimes.com/svc/books/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            api_key: NYTimes API key. If not provided, will look for 
                    NYTIMES_API_KEY environment variable.
                    
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("NYTIMES_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "NYTimes API key is required. Set NYTIMES_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        # Create HTTP client with a reasonable timeout
        self.client = httpx.Client(timeout=30.0)
    
    def get_best_sellers(
        self, 
        list_name: str = "combined-print-and-e-book-fiction",
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get books from a specific Best Sellers list.
        
        This is one of the most reliable endpoints in the Books API.
        
        Args:
            list_name: The encoded name of the list (e.g., 'hardcover-fiction').
            date: The date of the list in YYYY-MM-DD format. If not provided,
                 returns the most recent list. Use 'current' for the latest.
                 
        Returns:
            A dictionary containing the best sellers list
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Use 'current' if no date specified
        if not date:
            date = "current"
        
        # Build the URL - this is the documented format
        url = f"{self.BASE_URL}/lists/{date}/{list_name}.json"
        params = {"api-key": self.api_key}
        
        logger.info(f"Fetching best sellers - URL: {url}")
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", {})
            
            # Handle both single result and list of results
            if isinstance(results, list) and len(results) > 0:
                results = results[0]
            
            return {
                "list_name": results.get("list_name", ""),
                "display_name": results.get("display_name", ""),
                "bestsellers_date": results.get("bestsellers_date", ""),
                "published_date": results.get("published_date", ""),
                "books": self._format_bestseller_books(results.get("books", []))
            }
            
        except httpx.HTTPError as e:
            logger.error(f"Error querying NYTimes API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_best_sellers_overview(self) -> Dict[str, Any]:
        """
        Get an overview of all Best Sellers lists.
        
        This returns the top 5 books for each Best Sellers list.
        
        Returns:
            A dictionary containing overview of all lists
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        url = f"{self.BASE_URL}/lists/overview.json"
        params = {"api-key": self.api_key}
        
        logger.info("Fetching best sellers overview")
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", {})
            
            lists = results.get("lists", [])
            
            return {
                "bestsellers_date": results.get("bestsellers_date", ""),
                "published_date": results.get("published_date", ""),
                "num_lists": len(lists),
                "lists": self._format_overview_lists(lists)
            }
            
        except httpx.HTTPError as e:
            logger.error(f"Error querying NYTimes API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def _format_bestseller_books(self, books: List[Dict]) -> List[Dict]:
        """
        Format best seller book information.
        
        Args:
            books: Raw book data from the API
            
        Returns:
            A list of formatted book dictionaries
        """
        formatted = []
        
        for book in books:
            formatted_book = {
                "rank": book.get("rank", 0),
                "rank_last_week": book.get("rank_last_week", 0),
                "weeks_on_list": book.get("weeks_on_list", 0),
                "title": book.get("title", "Unknown Title"),
                "author": book.get("author", "Unknown Author"),
                "description": book.get("description", ""),
                "publisher": book.get("publisher", ""),
                "primary_isbn13": book.get("primary_isbn13", ""),
                "primary_isbn10": book.get("primary_isbn10", ""),
                "amazon_url": book.get("amazon_product_url", "")
            }
            formatted.append(formatted_book)
        
        return formatted
    
    def _format_overview_lists(self, lists: List[Dict]) -> List[Dict]:
        """
        Format overview lists information.
        
        Args:
            lists: Raw list data from the API
            
        Returns:
            A list of formatted list dictionaries
        """
        formatted = []
        
        for lst in lists:
            formatted_list = {
                "list_id": lst.get("list_id", 0),
                "list_name": lst.get("list_name", ""),
                "display_name": lst.get("display_name", ""),
                "updated": lst.get("updated", ""),
                "books": self._format_bestseller_books(lst.get("books", []))
            }
            formatted.append(formatted_list)
        
        return formatted
    
    def close(self):
        """Close the HTTP client connection."""
        self.client.close()