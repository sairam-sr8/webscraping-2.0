"""
TripAdvisor Scraper Pro - Main Application
A professional web scraping tool for extracting and analyzing hotel reviews from TripAdvisor.
"""
import os
import logging
import threading
import time
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

import streamlit as st
import pandas as pd
from tqdm import tqdm

from scraper.tripadvisor import TripAdvisorScraper, TripAdvisorDataProcessor
from utils.export import DataExporter
from utils.database import Database
from ui.components import Header, Sidebar, DataViewer, ExportTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TripAdvisorApp")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'hotel_info' not in st.session_state:
    st.session_state.hotel_info = {}
if 'summary' not in st.session_state:
    st.session_state.summary = {}
if 'scraping_status' not in st.session_state:
    st.session_state.scraping_status = None
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'export_format' not in st.session_state:
    st.session_state.export_format = "Excel"

# Initialize database
db = Database()

def scrape_hotel(url: str, max_pages: int = 5, use_selenium: bool = False):
    """
    Scrape hotel reviews from TripAdvisor.
    
    Args:
        url: URL of the hotel on TripAdvisor
        max_pages: Maximum number of pages to scrape
        use_selenium: Whether to use Selenium for JavaScript-rendered content
    """
    try:
        # Update scraping status
        st.session_state.scraping_status = "Initializing scraper..."
        st.session_state.progress = 10
        
        # Get proxy settings from session state
        use_proxies = st.session_state.get('use_proxies', False)
        proxy_list = []
        if use_proxies:
            proxy_text = st.session_state.get('proxy_list', '')
            if proxy_text:
                proxy_list = [line.strip() for line in proxy_text.split('\n') if line.strip()]
        
        # Initialize scraper
        scraper = TripAdvisorScraper(use_selenium=use_selenium, use_proxies=use_proxies, proxy_list=proxy_list)
        
        # Update scraping status
        st.session_state.scraping_status = "Scraping hotel reviews..."
        st.session_state.progress = 20
        
        # Scrape hotel reviews
        df, hotel_info = scraper.scrape_hotel(url, max_pages)
        
        # Update scraping status
        st.session_state.scraping_status = "Processing data..."
        st.session_state.progress = 70
        
        # Process data
        processor = TripAdvisorDataProcessor()
        df = processor.clean_data(df)
        df = processor.analyze_sentiment(df)
        summary = processor.generate_summary(df)
        
        # Update scraping status
        st.session_state.scraping_status = "Saving to database..."
        st.session_state.progress = 80
        
        # Save to database
        hotel_data = {
            'name': hotel_info.get('name', ''),
            'location': hotel_info.get('location', ''),
            'url': url,
            'rating': hotel_info.get('rating', 0),
            'total_reviews': hotel_info.get('total_reviews', 0)
        }
        hotel_id = db.save_hotel(hotel_data)
        
        if hotel_id > 0:
            # Convert DataFrame to list of dictionaries
            reviews = df.to_dict('records')
            db.save_reviews(hotel_id, reviews)
        
        # Save search history
        db.save_search_history(url, "hotel")
        
        # Update session state
        st.session_state.df = df
        st.session_state.hotel_info = hotel_info
        st.session_state.summary = summary
        
        # Update scraping status
        st.session_state.scraping_status = "Scraping completed successfully!"
        st.session_state.progress = 100
        
        # Close scraper
        scraper.close()
    
    except Exception as e:
        logger.error(f"Error scraping hotel: {e}")
        st.session_state.scraping_status = f"Error: {str(e)}"
        st.session_state.progress = 0

def scrape_region(url: str, max_hotels: int = 5, max_pages_per_hotel: int = 3):
    """
    Scrape hotels from a region on TripAdvisor.
    
    Args:
        url: URL of the region on TripAdvisor
        max_hotels: Maximum number of hotels to scrape
        max_pages_per_hotel: Maximum number of pages to scrape per hotel
    """
    try:
        # Update scraping status
        st.session_state.scraping_status = "Initializing scraper..."
        st.session_state.progress = 5
        
        # Get proxy settings from session state
        use_proxies = st.session_state.get('use_proxies', False)
        proxy_list = []
        if use_proxies:
            proxy_text = st.session_state.get('proxy_list', '')
            if proxy_text:
                proxy_list = [line.strip() for line in proxy_text.split('\n') if line.strip()]
        
        # Initialize scraper
        scraper = TripAdvisorScraper(use_selenium=True, use_proxies=use_proxies, proxy_list=proxy_list)
        
        # Update scraping status
        st.session_state.scraping_status = "Finding hotels in the region..."
        st.session_state.progress = 10
        
        # Scrape hotel URLs from the region
        hotel_urls = scraper.scrape_hotels_by_region(url, max_hotels)
        
        if not hotel_urls:
            st.session_state.scraping_status = "No hotels found in the region."
            st.session_state.progress = 0
            scraper.close()
            return
        
        # Initialize processor
        processor = TripAdvisorDataProcessor()
        
        # Initialize combined DataFrame
        combined_df = pd.DataFrame()
        
        # Scrape each hotel
        for i, hotel_url in enumerate(hotel_urls):
            try:
                # Update scraping status
                progress_pct = 10 + (i / len(hotel_urls)) * 80
                st.session_state.scraping_status = f"Scraping hotel {i+1} of {len(hotel_urls)}: {hotel_url}"
                st.session_state.progress = progress_pct
                
                # Scrape hotel reviews
                df, hotel_info = scraper.scrape_hotel(hotel_url, max_pages_per_hotel)
                
                # Process data
                df = processor.clean_data(df)
                df = processor.analyze_sentiment(df)
                
                # Save to database
                hotel_data = {
                    'name': hotel_info.get('name', ''),
                    'location': hotel_info.get('location', ''),
                    'url': hotel_url,
                    'rating': hotel_info.get('rating', 0),
                    'total_reviews': hotel_info.get('total_reviews', 0)
                }
                hotel_id = db.save_hotel(hotel_data)
                
                if hotel_id > 0:
                    # Convert DataFrame to list of dictionaries
                    reviews = df.to_dict('records')
                    db.save_reviews(hotel_id, reviews)
                
                # Save search history
                db.save_search_history(hotel_url, "hotel")
                
                # Combine DataFrames
                if not df.empty:
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
            
            except Exception as e:
                logger.error(f"Error scraping hotel {hotel_url}: {e}")
                continue
        
        # Update scraping status
        st.session_state.scraping_status = "Processing combined data..."
        st.session_state.progress = 90
        
        # Process combined data
        if not combined_df.empty:
            summary = processor.generate_summary(combined_df)
            
            # Update session state
            st.session_state.df = combined_df
            st.session_state.hotel_info = {'name': 'Multiple Hotels', 'location': 'Various Locations'}
            st.session_state.summary = summary
        
        # Update scraping status
        st.session_state.scraping_status = "Scraping completed successfully!"
        st.session_state.progress = 100
        
        # Close scraper
        scraper.close()
    
    except Exception as e:
        logger.error(f"Error scraping region: {e}")
        st.session_state.scraping_status = f"Error: {str(e)}"
        st.session_state.progress = 0

def load_from_db(location_filter: str = ""):
    """
    Load hotel and review data from the database.
    
    Args:
        location_filter: Filter hotels by location
    """
    try:
        # Update status
        st.session_state.scraping_status = "Loading data from database..."
        st.session_state.progress = 50
        
        # Get hotels from database
        if location_filter:
            hotels_df = db.get_hotels_by_location(location_filter)
        else:
            hotels_df = db.get_all_hotels()
        
        if hotels_df.empty:
            st.session_state.scraping_status = "No hotels found in the database."
            st.session_state.progress = 0
            return
        
        # Let user select a hotel
        st.session_state.hotels_df = hotels_df
        
        # Update status
        st.session_state.scraping_status = "Data loaded successfully!"
        st.session_state.progress = 100
    
    except Exception as e:
        logger.error(f"Error loading from database: {e}")
        st.session_state.scraping_status = f"Error: {str(e)}"
        st.session_state.progress = 0

def load_hotel_reviews(hotel_id: int):
    """
    Load reviews for a specific hotel from the database.
    
    Args:
        hotel_id: ID of the hotel
    """
    try:
        # Get reviews from database
        df = db.get_reviews_by_hotel_id(hotel_id)
        
        if df.empty:
            st.warning("No reviews found for this hotel.")
            return
        
        # Get hotel info
        hotels_df = st.session_state.get('hotels_df', pd.DataFrame())
        if not hotels_df.empty:
            hotel_row = hotels_df[hotels_df['id'] == hotel_id]
            if not hotel_row.empty:
                hotel_info = hotel_row.iloc[0].to_dict()
            else:
                hotel_info = {}
        else:
            hotel_info = {}
        
        # Process data
        processor = TripAdvisorDataProcessor()
        df = processor.clean_data(df)
        df = processor.analyze_sentiment(df)
        summary = processor.generate_summary(df)
        
        # Update session state
        st.session_state.df = df
        st.session_state.hotel_info = hotel_info
        st.session_state.summary = summary
    
    except Exception as e:
        logger.error(f"Error loading hotel reviews: {e}")
        st.error(f"Error loading hotel reviews: {e}")

def main():
    """Main function to run the Streamlit app."""
    # Render header
    Header.render()
    
    # Render sidebar
    Sidebar.render(
        on_scrape_hotel=lambda url, max_pages, use_selenium: threading.Thread(
            target=scrape_hotel, args=(url, max_pages, use_selenium)
        ).start(),
        on_scrape_region=lambda url, max_hotels, max_pages_per_hotel: threading.Thread(
            target=scrape_region, args=(url, max_hotels, max_pages_per_hotel)
        ).start(),
        on_load_from_db=load_from_db
    )
    
    # Update session state from sidebar
    if 'use_proxies' in st.session_state:
        st.session_state.use_proxies = st.session_state.get('use_proxies', False)
    
    if 'proxy_list' in st.session_state:
        st.session_state.proxy_list = st.session_state.get('proxy_list', '')
    
    if 'export_format' in st.session_state:
        st.session_state.export_format = st.session_state.get('export_format', 'Excel')
    
    # Main content area
    if st.session_state.scraping_status:
        # Display scraping status
        st.info(st.session_state.scraping_status)
        
        # Display progress bar
        if st.session_state.progress > 0:
            st.progress(st.session_state.progress / 100)
    
    # Display database results if available
    if 'hotels_df' in st.session_state and not st.session_state.hotels_df.empty:
        st.subheader("📋 Hotels in Database")
        
        # Display hotels table
        st.dataframe(
            st.session_state.hotels_df[['id', 'name', 'location', 'rating', 'total_reviews']],
            use_container_width=True,
            height=200
        )
        
        # Let user select a hotel
        selected_hotel_id = st.selectbox(
            "Select a Hotel to View Reviews",
            options=st.session_state.hotels_df['id'].tolist(),
            format_func=lambda x: st.session_state.hotels_df[st.session_state.hotels_df['id'] == x]['name'].iloc[0]
        )
        
        if st.button("Load Selected Hotel"):
            load_hotel_reviews(selected_hotel_id)
    
    # Display hotel info and reviews if available
    if not st.session_state.df.empty:
        # Display hotel information
        DataViewer.render_hotel_info(st.session_state.hotel_info)
        
        # Display reviews
        DataViewer.render_reviews(st.session_state.df)
        
        # Display summary
        DataViewer.render_summary(st.session_state.df, st.session_state.summary)
        
        # Display export tools
        ExportTools.render(
            st.session_state.df,
            st.session_state.hotel_info,
            st.session_state.summary,
            st.session_state.export_format
        )

if __name__ == "__main__":
    main()
