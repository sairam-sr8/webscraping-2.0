"""
TripAdvisor Scraper - Core Module
Advanced web scraper for TripAdvisor with robust error handling, rate limiting, and proxy support.
"""
import logging
import random
import time
from typing import Dict, List, Optional, Tuple, Union
import re
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd
# Robust import for fake_useragent
try:
    from fake_useragent import UserAgent
    _FAKE_UA_AVAILABLE = True
except ImportError:
    import warnings
    _FAKE_UA_AVAILABLE = False
    warnings.warn("fake_useragent not installed. Falling back to static user agents. To enable advanced anti-blocking, install with: pip install fake-useragent")
    # Fallback static user-agents
    _STATIC_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
    ]
    import random

def get_random_user_agent():
    if _FAKE_UA_AVAILABLE:
        return UserAgent().random
    else:
        return random.choice(_STATIC_USER_AGENTS)

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TripAdvisorScraper")

class TripAdvisorScraper:
    """Advanced TripAdvisor web scraper with multiple scraping strategies."""
    
    def __init__(self, use_selenium: bool = False, use_proxies: bool = False, proxy_list: List[str] = None):
        """
        Initialize the TripAdvisor scraper.
        
        Args:
            use_selenium: Whether to use Selenium for JavaScript-rendered content
            use_proxies: Whether to use proxy rotation
            proxy_list: List of proxy URLs (if use_proxies is True)
        """
        self.use_selenium = use_selenium
        self.use_proxies = use_proxies
        self.proxy_list = proxy_list or []
        self.user_agent = UserAgent()
        self.driver = None
        self.session = requests.Session()
        
        # Initialize Selenium if needed
        if self.use_selenium:
            self._initialize_selenium()
    
    def _initialize_selenium(self):
        """Initialize Selenium WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={self.user_agent.random}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            raise
    
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the proxy list."""
        if not self.use_proxies or not self.proxy_list:
            return None
        
        proxy = random.choice(self.proxy_list)
        return {
            "http": proxy,
            "https": proxy
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate random headers for HTTP requests."""
        return {
            "User-Agent": self.user_agent.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError))
    )
    def _fetch_page_content(self, url: str) -> str:
        """
        Fetch page content with retry logic and proxy support.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
        """
        logger.info(f"Fetching URL: {url}")
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(2, 5))
        
        if self.use_selenium:
            try:
                self.driver.get(url)
                # Wait for the page to load
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return self.driver.page_source
            except Exception as e:
                logger.error(f"Selenium fetch failed: {e}")
                raise
        else:
            try:
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    proxies=self._get_random_proxy(),
                    timeout=30
                )
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.error(f"Request fetch failed: {e}")
                raise
    
    def _extract_hotel_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract hotel information from the soup object.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary containing hotel information
        """
        hotel_info = {}
        
        # Extract hotel name with multiple fallback selectors
        try:
            hotel_name_elem = soup.find('h1', id='HEADING')
            if hotel_name_elem and hotel_name_elem.text.strip():
                hotel_info['name'] = hotel_name_elem.text.strip()
            else:
                # Fallback selectors
                hotel_name_elem = soup.find('h1', class_='QdLfr b d Pn')
                if hotel_name_elem:
                    hotel_info['name'] = hotel_name_elem.text.strip()
                else:
                    logger.warning("Could not find hotel name")
                    hotel_info['name'] = "N/A"
        except Exception as e:
            logger.error(f"Error extracting hotel name: {e}")
            hotel_info['name'] = "N/A"
        
        # Extract hotel location with multiple fallback selectors
        try:
            location_elems = soup.find_all('span', class_='biGQs _P pZUbB KxBGd')
            if location_elems and len(location_elems) > 1:
                hotel_info['location'] = location_elems[1].text.strip()
            else:
                # Fallback selectors
                location_elem = soup.find('div', class_='AYHFM')
                if location_elem:
                    hotel_info['location'] = location_elem.text.strip()
                else:
                    logger.warning("Could not find hotel location")
                    hotel_info['location'] = "N/A"
        except Exception as e:
            logger.error(f"Error extracting hotel location: {e}")
            hotel_info['location'] = "N/A"
        
        # Extract total reviews count
        try:
            reviews_elem = soup.find('span', class_='biGQs _P pZUbB KxBGd')
            if reviews_elem:
                reviews_text = reviews_elem.text
                if "reviews" in reviews_text.lower():
                    hotel_info['total_reviews'] = reviews_text.split()[0].replace(',', '')
                else:
                    hotel_info['total_reviews'] = "0"
            else:
                logger.warning("Could not find total reviews")
                hotel_info['total_reviews'] = "0"
        except Exception as e:
            logger.error(f"Error extracting total reviews: {e}")
            hotel_info['total_reviews'] = "0"
        
        # Extract hotel rating
        try:
            rating_elem = soup.find('div', class_='grdwI P')
            if rating_elem:
                hotel_info['rating'] = rating_elem.text.strip()
            else:
                # Fallback selector
                rating_elem = soup.find('span', class_='uwJeR P')
                if rating_elem:
                    hotel_info['rating'] = rating_elem.text.strip()
                else:
                    logger.warning("Could not find hotel rating")
                    hotel_info['rating'] = "N/A"
        except Exception as e:
            logger.error(f"Error extracting hotel rating: {e}")
            hotel_info['rating'] = "N/A"
        
        return hotel_info
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract reviews from the soup object.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of dictionaries containing review information
        """
        reviews = []
        
        try:
            # Extract review containers
            review_containers = soup.find_all('div', class_='YibKl MC R2 Gi z Z BB pBbQr')
            
            if not review_containers:
                # Fallback selector
                review_containers = soup.find_all('div', class_='review-container')
            
            if not review_containers:
                logger.warning("No review containers found")
                return reviews
            
            for container in review_containers:
                review = {}
                
                # Extract review title
                try:
                    title_elem = container.find('span', class_='JbGkU Cj')
                    if title_elem:
                        review['title'] = title_elem.text.strip()
                    else:
                        # Fallback selector
                        title_elem = container.find('span', class_='noQuotes')
                        if title_elem:
                            review['title'] = title_elem.text.strip()
                        else:
                            review['title'] = "N/A"
                except Exception as e:
                    logger.error(f"Error extracting review title: {e}")
                    review['title'] = "N/A"
                
                # Extract review content
                try:
                    content_elem = container.find('span', class_='orRIx Ci _a C')
                    if content_elem:
                        review['content'] = content_elem.text.strip()
                    else:
                        # Fallback selector
                        content_elem = container.find('p', class_='partial_entry')
                        if content_elem:
                            review['content'] = content_elem.text.strip()
                        else:
                            review['content'] = "N/A"
                except Exception as e:
                    logger.error(f"Error extracting review content: {e}")
                    review['content'] = "N/A"
                
                # Extract reviewer and date
                try:
                    reviewer_date_elem = container.find('div', class_='tVWyV _Z o S4 H3 Ci')
                    if reviewer_date_elem and 'wrote a review' in reviewer_date_elem.text:
                        parts = reviewer_date_elem.text.split('wrote a review')
                        review['reviewer'] = parts[0].strip()
                        review['date'] = parts[1].strip()
                    else:
                        # Fallback selector
                        reviewer_elem = container.find('div', class_='info_text pointer_cursor')
                        date_elem = container.find('span', class_='ratingDate')
                        
                        if reviewer_elem:
                            review['reviewer'] = reviewer_elem.text.strip()
                        else:
                            review['reviewer'] = "N/A"
                            
                        if date_elem:
                            review['date'] = date_elem.text.replace('Reviewed', '').strip()
                        else:
                            review['date'] = "N/A"
                except Exception as e:
                    logger.error(f"Error extracting reviewer and date: {e}")
                    review['reviewer'] = "N/A"
                    review['date'] = "N/A"
                
                # Extract rating
                try:
                    rating_elem = container.find('div', class_='kmMXA _T Gi')
                    if rating_elem:
                        title_attr = rating_elem.find('title')
                        if title_attr:
                            review['rating'] = title_attr.text[:3].strip()
                        else:
                            review['rating'] = "N/A"
                    else:
                        # Fallback selector
                        rating_elem = container.find('span', class_='ui_bubble_rating')
                        if rating_elem and 'class' in rating_elem.attrs:
                            bubble_class = rating_elem['class']
                            for cls in bubble_class:
                                if cls.startswith('bubble_'):
                                    try:
                                        rating_value = int(cls.split('_')[1]) / 10
                                        review['rating'] = str(rating_value)
                                        break
                                    except (IndexError, ValueError):
                                        review['rating'] = "N/A"
                        else:
                            review['rating'] = "N/A"
                except Exception as e:
                    logger.error(f"Error extracting rating: {e}")
                    review['rating'] = "N/A"
                
                # Add the review to the list
                reviews.append(review)
        
        except Exception as e:
            logger.error(f"Error extracting reviews: {e}")
        
        return reviews
    
    def _generate_pagination_urls(self, base_url: str, total_reviews: int, reviews_per_page: int = 10) -> List[str]:
        """
        Generate pagination URLs for the given base URL.
        
        Args:
            base_url: Base URL of the hotel
            total_reviews: Total number of reviews
            reviews_per_page: Number of reviews per page
            
        Returns:
            List of pagination URLs
        """
        try:
            total_reviews = int(total_reviews)
            num_pages = (total_reviews + reviews_per_page - 1) // reviews_per_page
            
            # Limit to a reasonable number of pages to avoid excessive scraping
            num_pages = min(num_pages, 50)
            
            # Parse the base URL to generate pagination URLs
            if "Reviews-" in base_url:
                split_url = base_url.split("Reviews-")
                first_part = split_url[0] + "Reviews-or"
                second_part = "-" + split_url[1]
                
                # Generate pagination URLs
                pagination_urls = [base_url]  # First page
                for i in range(reviews_per_page, num_pages * reviews_per_page, reviews_per_page):
                    pagination_urls.append(f"{first_part}{i}{second_part}")
                
                return pagination_urls
            else:
                logger.warning(f"Could not parse URL for pagination: {base_url}")
                return [base_url]
        except Exception as e:
            logger.error(f"Error generating pagination URLs: {e}")
            return [base_url]
    
    def scrape_hotel(self, url: str, max_pages: int = None) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Scrape hotel information and reviews.
        
        Args:
            url: URL of the hotel on TripAdvisor
            max_pages: Maximum number of pages to scrape (None for all)
            
        Returns:
            Tuple of (DataFrame of reviews, Dictionary of hotel information)
        """
        try:
            # Fetch the first page
            html_content = self._fetch_page_content(url)
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract hotel information
            hotel_info = self._extract_hotel_info(soup)
            logger.info(f"Extracted hotel info: {hotel_info['name']} in {hotel_info['location']}")
            
            # Extract reviews from the first page
            reviews = self._extract_reviews(soup)
            logger.info(f"Extracted {len(reviews)} reviews from the first page")
            
            # Generate pagination URLs
            total_reviews = int(hotel_info.get('total_reviews', 0))
            pagination_urls = self._generate_pagination_urls(url, total_reviews)
            
            # Limit the number of pages if specified
            if max_pages:
                pagination_urls = pagination_urls[:max_pages]
            
            # Skip the first URL as we already scraped it
            pagination_urls = pagination_urls[1:]
            
            # Scrape additional pages
            for page_url in pagination_urls:
                try:
                    logger.info(f"Scraping page: {page_url}")
                    html_content = self._fetch_page_content(page_url)
                    soup = BeautifulSoup(html_content, 'lxml')
                    
                    # Extract reviews from this page
                    page_reviews = self._extract_reviews(soup)
                    logger.info(f"Extracted {len(page_reviews)} reviews from {page_url}")
                    
                    # Add to the list of reviews
                    reviews.extend(page_reviews)
                except Exception as e:
                    logger.error(f"Error scraping page {page_url}: {e}")
            
            # Create a DataFrame from the reviews
            if reviews:
                df = pd.DataFrame(reviews)
                
                # Add hotel information to each row
                df['hotel_name'] = hotel_info.get('name', 'N/A')
                df['hotel_location'] = hotel_info.get('location', 'N/A')
                df['hotel_rating'] = hotel_info.get('rating', 'N/A')
                
                # Reorder columns
                column_order = [
                    'hotel_name', 'hotel_location', 'hotel_rating',
                    'reviewer', 'rating', 'date', 'title', 'content'
                ]
                df = df.reindex(columns=[col for col in column_order if col in df.columns])
                
                logger.info(f"Successfully scraped {len(df)} reviews for {hotel_info.get('name', 'N/A')}")
                return df, hotel_info
            else:
                logger.warning(f"No reviews found for {hotel_info.get('name', 'N/A')}")
                return pd.DataFrame(), hotel_info
        
        except Exception as e:
            logger.error(f"Error scraping hotel {url}: {e}")
            return pd.DataFrame(), {}
    
    def scrape_hotels_by_region(self, region_url: str, max_hotels: int = 10) -> List[str]:
        """
        Scrape hotel URLs from a region page.
        
        Args:
            region_url: URL of the region on TripAdvisor
            max_hotels: Maximum number of hotels to scrape
            
        Returns:
            List of hotel URLs
        """
        try:
            logger.info(f"Scraping hotels from region: {region_url}")
            
            # Fetch the region page
            html_content = self._fetch_page_content(region_url)
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract hotel URLs
            hotel_urls = []
            
            # Try different selectors for hotel links
            hotel_elements = soup.find_all('a', class_='property_title')
            
            if not hotel_elements:
                # Fallback selector
                hotel_elements = soup.find_all('a', class_='review_count')
            
            if not hotel_elements:
                # Another fallback selector
                hotel_elements = soup.find_all('div', class_='listing_title')
                hotel_elements = [div.find('a') for div in hotel_elements if div.find('a')]
            
            for element in hotel_elements[:max_hotels]:
                if 'href' in element.attrs:
                    href = element['href']
                    if href.startswith('/'):
                        hotel_url = f"https://www.tripadvisor.com{href}"
                        hotel_urls.append(hotel_url)
            
            logger.info(f"Found {len(hotel_urls)} hotel URLs from region {region_url}")
            return hotel_urls
        
        except Exception as e:
            logger.error(f"Error scraping hotels from region {region_url}: {e}")
            return []
    
    def close(self):
        """Close the Selenium driver and requests session."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing Selenium WebDriver: {e}")
        
        try:
            self.session.close()
            logger.info("Requests session closed")
        except Exception as e:
            logger.error(f"Error closing requests session: {e}")


class TripAdvisorDataProcessor:
    """Process and analyze TripAdvisor data."""
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess the scraped data.
        
        Args:
            df: DataFrame of scraped reviews
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        # Create a copy to avoid modifying the original
        cleaned_df = df.copy()
        
        # Convert date strings to datetime objects
        try:
            cleaned_df['date'] = pd.to_datetime(cleaned_df['date'], errors='coerce')
        except Exception as e:
            logger.error(f"Error converting dates: {e}")
        
        # Convert ratings to numeric
        try:
            cleaned_df['rating'] = pd.to_numeric(cleaned_df['rating'], errors='coerce')
        except Exception as e:
            logger.error(f"Error converting ratings: {e}")
        
        # Drop duplicates
        cleaned_df.drop_duplicates(subset=['reviewer', 'date', 'content'], keep='first', inplace=True)
        
        # Fill missing values
        cleaned_df.fillna({
            'title': 'No Title',
            'content': 'No Content',
            'reviewer': 'Anonymous',
            'rating': 0.0
        }, inplace=True)
        
        return cleaned_df
    
    @staticmethod
    def analyze_sentiment(df: pd.DataFrame) -> pd.DataFrame:
        """
        Simple sentiment analysis based on ratings.
        
        Args:
            df: DataFrame of reviews
            
        Returns:
            DataFrame with sentiment column
        """
        if df.empty or 'rating' not in df.columns:
            return df
        
        # Create a copy to avoid modifying the original
        result_df = df.copy()
        
        # Add sentiment based on rating
        try:
            def get_sentiment(rating):
                if pd.isna(rating):
                    return 'Unknown'
                rating = float(rating)
                if rating >= 4:
                    return 'Positive'
                elif rating >= 3:
                    return 'Neutral'
                else:
                    return 'Negative'
            
            result_df['sentiment'] = result_df['rating'].apply(get_sentiment)
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
        
        return result_df
    
    @staticmethod
    def generate_summary(df: pd.DataFrame) -> Dict[str, any]:
        """
        Generate a summary of the reviews.
        
        Args:
            df: DataFrame of reviews
            
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {
                'total_reviews': 0,
                'average_rating': 0,
                'sentiment_counts': {},
                'reviews_by_month': {}
            }
        
        summary = {}
        
        try:
            # Total reviews
            summary['total_reviews'] = len(df)
            
            # Average rating
            if 'rating' in df.columns:
                summary['average_rating'] = df['rating'].mean()
            else:
                summary['average_rating'] = 0
            
            # Sentiment counts
            if 'sentiment' in df.columns:
                summary['sentiment_counts'] = df['sentiment'].value_counts().to_dict()
            else:
                summary['sentiment_counts'] = {}
            
            # Reviews by month
            if 'date' in df.columns:
                df_with_date = df.dropna(subset=['date'])
                if not df_with_date.empty:
                    df_with_date['month'] = df_with_date['date'].dt.strftime('%Y-%m')
                    reviews_by_month = df_with_date.groupby('month').size().to_dict()
                    summary['reviews_by_month'] = reviews_by_month
                else:
                    summary['reviews_by_month'] = {}
            else:
                summary['reviews_by_month'] = {}
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
        
        return summary
