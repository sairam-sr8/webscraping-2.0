"""
Database utilities for TripAdvisor data.
Handles storing and retrieving hotel and review data.
"""
import os
import json
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

import pandas as pd

logger = logging.getLogger("TripAdvisorDatabase")

class Database:
    """SQLite database for TripAdvisor data."""
    
    def __init__(self, db_path: str = "data/tripadvisor.db"):
        """
        Initialize the database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create hotels table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hotels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    location TEXT,
                    url TEXT UNIQUE,
                    rating REAL,
                    total_reviews INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create reviews table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hotel_id INTEGER,
                    title TEXT,
                    content TEXT,
                    reviewer TEXT,
                    rating REAL,
                    date TEXT,
                    sentiment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hotel_id) REFERENCES hotels (id)
                )
            ''')
            
            # Create search_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    search_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
        
        finally:
            if conn:
                conn.close()
    
    def save_hotel(self, hotel_data: Dict[str, any]) -> int:
        """
        Save hotel data to the database.
        
        Args:
            hotel_data: Dictionary containing hotel information
            
        Returns:
            Hotel ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if hotel already exists
            cursor.execute(
                "SELECT id FROM hotels WHERE url = ?",
                (hotel_data.get('url', ''),)
            )
            result = cursor.fetchone()
            
            if result:
                # Update existing hotel
                hotel_id = result[0]
                cursor.execute(
                    """
                    UPDATE hotels
                    SET name = ?, location = ?, rating = ?, total_reviews = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        hotel_data.get('name', ''),
                        hotel_data.get('location', ''),
                        hotel_data.get('rating', 0),
                        hotel_data.get('total_reviews', 0),
                        hotel_id
                    )
                )
                logger.info(f"Updated hotel: {hotel_data.get('name', '')}")
            else:
                # Insert new hotel
                cursor.execute(
                    """
                    INSERT INTO hotels (name, location, url, rating, total_reviews)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        hotel_data.get('name', ''),
                        hotel_data.get('location', ''),
                        hotel_data.get('url', ''),
                        hotel_data.get('rating', 0),
                        hotel_data.get('total_reviews', 0)
                    )
                )
                hotel_id = cursor.lastrowid
                logger.info(f"Inserted new hotel: {hotel_data.get('name', '')}")
            
            conn.commit()
            return hotel_id
        
        except Exception as e:
            logger.error(f"Error saving hotel: {e}")
            return -1
        
        finally:
            if conn:
                conn.close()
    
    def save_reviews(self, hotel_id: int, reviews: List[Dict[str, any]]) -> bool:
        """
        Save reviews to the database.
        
        Args:
            hotel_id: ID of the hotel
            reviews: List of review dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if not reviews:
            logger.warning("No reviews to save")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert reviews
            for review in reviews:
                # Check if review already exists
                cursor.execute(
                    """
                    SELECT id FROM reviews
                    WHERE hotel_id = ? AND reviewer = ? AND date = ? AND content = ?
                    """,
                    (
                        hotel_id,
                        review.get('reviewer', ''),
                        review.get('date', ''),
                        review.get('content', '')
                    )
                )
                result = cursor.fetchone()
                
                if not result:
                    # Insert new review
                    cursor.execute(
                        """
                        INSERT INTO reviews (hotel_id, title, content, reviewer, rating, date, sentiment)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            hotel_id,
                            review.get('title', ''),
                            review.get('content', ''),
                            review.get('reviewer', ''),
                            review.get('rating', 0),
                            review.get('date', ''),
                            review.get('sentiment', '')
                        )
                    )
            
            conn.commit()
            logger.info(f"Saved {len(reviews)} reviews for hotel ID {hotel_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving reviews: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
    
    def save_search_history(self, url: str, search_type: str = "hotel") -> bool:
        """
        Save search history to the database.
        
        Args:
            url: URL that was searched
            search_type: Type of search (hotel, region, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert search history
            cursor.execute(
                "INSERT INTO search_history (url, search_type) VALUES (?, ?)",
                (url, search_type)
            )
            
            conn.commit()
            logger.info(f"Saved search history: {url}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving search history: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
    
    def get_hotel_by_url(self, url: str) -> Optional[Dict[str, any]]:
        """
        Get hotel data by URL.
        
        Args:
            url: URL of the hotel
            
        Returns:
            Dictionary containing hotel information or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get hotel data
            cursor.execute(
                "SELECT * FROM hotels WHERE url = ?",
                (url,)
            )
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error getting hotel by URL: {e}")
            return None
        
        finally:
            if conn:
                conn.close()
    
    def get_reviews_by_hotel_id(self, hotel_id: int) -> pd.DataFrame:
        """
        Get reviews by hotel ID.
        
        Args:
            hotel_id: ID of the hotel
            
        Returns:
            DataFrame containing reviews
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get reviews
            query = "SELECT * FROM reviews WHERE hotel_id = ?"
            df = pd.read_sql_query(query, conn, params=(hotel_id,))
            
            logger.info(f"Retrieved {len(df)} reviews for hotel ID {hotel_id}")
            return df
        
        except Exception as e:
            logger.error(f"Error getting reviews by hotel ID: {e}")
            return pd.DataFrame()
        
        finally:
            if conn:
                conn.close()
    
    def get_search_history(self, limit: int = 10) -> pd.DataFrame:
        """
        Get search history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            DataFrame containing search history
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get search history
            query = "SELECT * FROM search_history ORDER BY timestamp DESC LIMIT ?"
            df = pd.read_sql_query(query, conn, params=(limit,))
            
            logger.info(f"Retrieved {len(df)} search history entries")
            return df
        
        except Exception as e:
            logger.error(f"Error getting search history: {e}")
            return pd.DataFrame()
        
        finally:
            if conn:
                conn.close()
    
    def get_all_hotels(self) -> pd.DataFrame:
        """
        Get all hotels.
        
        Returns:
            DataFrame containing all hotels
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all hotels
            query = "SELECT * FROM hotels ORDER BY name"
            df = pd.read_sql_query(query, conn)
            
            logger.info(f"Retrieved {len(df)} hotels")
            return df
        
        except Exception as e:
            logger.error(f"Error getting all hotels: {e}")
            return pd.DataFrame()
        
        finally:
            if conn:
                conn.close()
    
    def get_hotels_by_location(self, location: str) -> pd.DataFrame:
        """
        Get hotels by location.
        
        Args:
            location: Location to search for
            
        Returns:
            DataFrame containing hotels in the specified location
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get hotels by location
            query = "SELECT * FROM hotels WHERE location LIKE ? ORDER BY name"
            df = pd.read_sql_query(query, conn, params=(f"%{location}%",))
            
            logger.info(f"Retrieved {len(df)} hotels in location '{location}'")
            return df
        
        except Exception as e:
            logger.error(f"Error getting hotels by location: {e}")
            return pd.DataFrame()
        
        finally:
            if conn:
                conn.close()
    
    def delete_hotel(self, hotel_id: int) -> bool:
        """
        Delete a hotel and its reviews.
        
        Args:
            hotel_id: ID of the hotel to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete reviews first (due to foreign key constraint)
            cursor.execute("DELETE FROM reviews WHERE hotel_id = ?", (hotel_id,))
            
            # Delete hotel
            cursor.execute("DELETE FROM hotels WHERE id = ?", (hotel_id,))
            
            conn.commit()
            logger.info(f"Deleted hotel ID {hotel_id} and its reviews")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting hotel: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
    
    def clear_search_history(self) -> bool:
        """
        Clear search history.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear search history
            cursor.execute("DELETE FROM search_history")
            
            conn.commit()
            logger.info("Cleared search history")
            return True
        
        except Exception as e:
            logger.error(f"Error clearing search history: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
