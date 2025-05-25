"""
UI components for the TripAdvisor Scraper Streamlit app.
"""
import os
import logging
from typing import Dict, List, Optional, Tuple, Union, Callable

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger("TripAdvisorUI")

class Header:
    """Header component for the Streamlit app."""
    
    @staticmethod
    def render():
        """Render the header component."""
        st.set_page_config(
            page_title="TripAdvisor Scraper Pro",
            page_icon="🌐",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🌐 TripAdvisor Scraper Pro")
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #FF5A5F;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #484848;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #F7F7F7;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FF5A5F;
            color: white;
        }
        .card {
            border-radius: 5px;
            padding: 20px;
            background-color: #F7F7F7;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #FF5A5F;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #484848;
        }
        </style>
        
        <div class="main-header">TripAdvisor Scraper Pro</div>
        <div class="sub-header">Extract, analyze, and visualize hotel reviews from TripAdvisor</div>
        """, unsafe_allow_html=True)


class Sidebar:
    """Sidebar component for the Streamlit app."""
    
    @staticmethod
    def render(on_scrape_hotel: Callable, on_scrape_region: Callable, on_load_from_db: Callable):
        """
        Render the sidebar component.
        
        Args:
            on_scrape_hotel: Callback function for scraping a hotel
            on_scrape_region: Callback function for scraping a region
            on_load_from_db: Callback function for loading data from the database
        """
        with st.sidebar:
            st.title("🔍 Scraper Controls")
            
            # Create tabs for different scraping options
            tab1, tab2, tab3 = st.tabs(["Hotel URL", "Region/Country", "Database"])
            
            with tab1:
                st.subheader("Scrape by Hotel URL")
                hotel_url = st.text_input(
                    "Enter TripAdvisor Hotel URL",
                    placeholder="https://www.tripadvisor.com/Hotel_Review-..."
                )
                max_pages = st.slider(
                    "Maximum Pages to Scrape",
                    min_value=1,
                    max_value=50,
                    value=5,
                    help="Maximum number of review pages to scrape"
                )
                use_selenium = st.checkbox(
                    "Use Selenium (for JavaScript content)",
                    value=False,
                    help="Use Selenium for JavaScript-rendered content"
                )
                
                if st.button("Scrape Hotel", key="scrape_hotel_btn"):
                    if hotel_url and hotel_url.startswith("https://www.tripadvisor"):
                        on_scrape_hotel(hotel_url, max_pages, use_selenium)
                    else:
                        st.error("Please enter a valid TripAdvisor URL")
            
            with tab2:
                st.subheader("Scrape by Region/Country")
                region_url = st.text_input(
                    "Enter TripAdvisor Region URL",
                    placeholder="https://www.tripadvisor.com/Hotels-..."
                )
                max_hotels = st.slider(
                    "Maximum Hotels to Scrape",
                    min_value=1,
                    max_value=20,
                    value=5,
                    help="Maximum number of hotels to scrape from the region"
                )
                max_pages_per_hotel = st.slider(
                    "Maximum Pages per Hotel",
                    min_value=1,
                    max_value=20,
                    value=3,
                    help="Maximum number of review pages to scrape per hotel"
                )
                
                if st.button("Scrape Region", key="scrape_region_btn"):
                    if region_url and region_url.startswith("https://www.tripadvisor"):
                        on_scrape_region(region_url, max_hotels, max_pages_per_hotel)
                    else:
                        st.error("Please enter a valid TripAdvisor Region URL")
            
            with tab3:
                st.subheader("Load from Database")
                st.info("Load previously scraped data from the database")
                
                # Add location filter
                location_filter = st.text_input(
                    "Filter by Location",
                    placeholder="e.g., New York, Paris, etc."
                )
                
                if st.button("Load Data", key="load_data_btn"):
                    on_load_from_db(location_filter)
            
            # Add advanced options
            st.sidebar.markdown("---")
            st.sidebar.subheader("⚙️ Advanced Options")
            
            # Proxy settings
            use_proxies = st.sidebar.checkbox(
                "Use Proxy Rotation",
                value=False,
                help="Rotate between different proxies to avoid IP blocking"
            )
            
            if use_proxies:
                proxy_list = st.sidebar.text_area(
                    "Proxy List (one per line)",
                    placeholder="http://user:pass@proxy.example.com:8080\nhttps://proxy2.example.com:8080"
                )
            
            # Export options
            st.sidebar.markdown("---")
            st.sidebar.subheader("📊 Export Options")
            
            export_format = st.sidebar.selectbox(
                "Export Format",
                options=["Excel", "CSV", "JSON", "All Formats"],
                index=0
            )
            
            # About section
            st.sidebar.markdown("---")
            st.sidebar.info(
                "**TripAdvisor Scraper Pro**\n\n"
                "A professional web scraping tool for extracting and analyzing "
                "hotel reviews from TripAdvisor.\n\n"
                "© 2025 | Version 1.0.0"
            )


class DataViewer:
    """Data viewer component for the Streamlit app."""
    
    @staticmethod
    def render_hotel_info(hotel_info: Dict[str, any]):
        """
        Render hotel information.
        
        Args:
            hotel_info: Dictionary containing hotel information
        """
        if not hotel_info:
            st.warning("No hotel information available")
            return
        
        st.subheader("📌 Hotel Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{hotel_info.get('name', 'N/A')}</div>
                    <div class="metric-label">Hotel Name</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{hotel_info.get('location', 'N/A')}</div>
                    <div class="metric-label">Location</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{hotel_info.get('rating', 'N/A')}</div>
                    <div class="metric-label">Rating</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    @staticmethod
    def render_reviews(df: pd.DataFrame):
        """
        Render reviews table.
        
        Args:
            df: DataFrame containing reviews
        """
        if df.empty:
            st.warning("No reviews available")
            return
        
        st.subheader("📝 Reviews")
        
        # Add search and filter options
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search in Reviews", placeholder="Enter search term...")
        
        with col2:
            min_rating = st.select_slider(
                "Minimum Rating",
                options=[0, 1, 2, 3, 4, 5],
                value=0
            )
        
        # Filter the DataFrame
        filtered_df = df.copy()
        
        if search_term:
            mask = (
                filtered_df['title'].str.contains(search_term, case=False, na=False) |
                filtered_df['content'].str.contains(search_term, case=False, na=False) |
                filtered_df['reviewer'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if min_rating > 0 and 'rating' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['rating'] >= min_rating]
        
        # Show the filtered DataFrame
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400
        )
        
        st.info(f"Showing {len(filtered_df)} of {len(df)} reviews")
    
    @staticmethod
    def render_summary(df: pd.DataFrame, summary: Dict[str, any]):
        """
        Render summary statistics and visualizations.
        
        Args:
            df: DataFrame containing reviews
            summary: Dictionary with summary statistics
        """
        if df.empty or not summary:
            st.warning("No data available for summary")
            return
        
        st.subheader("📊 Summary Statistics")
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{summary.get('total_reviews', 0)}</div>
                    <div class="metric-label">Total Reviews</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            avg_rating = summary.get('average_rating', 0)
            avg_rating_formatted = f"{avg_rating:.1f}" if avg_rating else "N/A"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{avg_rating_formatted}</div>
                    <div class="metric-label">Average Rating</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            sentiment_counts = summary.get('sentiment_counts', {})
            positive_count = sentiment_counts.get('Positive', 0)
            positive_pct = (positive_count / summary.get('total_reviews', 1)) * 100 if summary.get('total_reviews', 0) > 0 else 0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{positive_pct:.1f}%</div>
                    <div class="metric-label">Positive Reviews</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col4:
            reviews_by_month = summary.get('reviews_by_month', {})
            latest_month = max(reviews_by_month.keys()) if reviews_by_month else "N/A"
            latest_count = reviews_by_month.get(latest_month, 0) if reviews_by_month else 0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{latest_count}</div>
                    <div class="metric-label">Latest Month Reviews</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Create visualizations
        st.subheader("📈 Visualizations")
        
        tab1, tab2, tab3 = st.tabs(["Ratings", "Sentiment", "Timeline"])
        
        with tab1:
            if 'rating' in df.columns:
                # Rating distribution
                rating_counts = df['rating'].value_counts().sort_index()
                fig = px.bar(
                    x=rating_counts.index,
                    y=rating_counts.values,
                    labels={'x': 'Rating', 'y': 'Count'},
                    title='Rating Distribution',
                    color=rating_counts.values,
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            if 'sentiment' in df.columns:
                # Sentiment analysis
                sentiment_counts = df['sentiment'].value_counts()
                fig = px.pie(
                    values=sentiment_counts.values,
                    names=sentiment_counts.index,
                    title='Sentiment Analysis',
                    color=sentiment_counts.index,
                    color_discrete_map={
                        'Positive': 'green',
                        'Neutral': 'yellow',
                        'Negative': 'red'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            if 'date' in df.columns:
                # Reviews over time
                df_with_date = df.dropna(subset=['date'])
                if not df_with_date.empty:
                    df_with_date['month'] = pd.to_datetime(df_with_date['date']).dt.strftime('%Y-%m')
                    reviews_by_month = df_with_date.groupby('month').size().reset_index(name='count')
                    reviews_by_month = reviews_by_month.sort_values('month')
                    
                    fig = px.line(
                        reviews_by_month,
                        x='month',
                        y='count',
                        markers=True,
                        labels={'month': 'Month', 'count': 'Number of Reviews'},
                        title='Reviews Over Time'
                    )
                    st.plotly_chart(fig, use_container_width=True)


class ExportTools:
    """Export tools component for the Streamlit app."""
    
    @staticmethod
    def render(df: pd.DataFrame, hotel_info: Dict[str, any], summary: Dict[str, any], export_format: str):
        """
        Render export tools.
        
        Args:
            df: DataFrame containing reviews
            hotel_info: Dictionary containing hotel information
            summary: Dictionary with summary statistics
            export_format: Export format (Excel, CSV, JSON, or All Formats)
        """
        if df.empty:
            st.warning("No data available for export")
            return
        
        st.subheader("💾 Export Data")
        
        # Create export filename based on hotel name
        hotel_name = hotel_info.get('name', 'hotel').replace(' ', '_')
        filename = f"{hotel_name}_reviews"
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        col1, col2, col3 = st.columns(3)
        
        if export_format in ["Excel", "All Formats"]:
            with col1:
                excel_path = os.path.join('data', f"{filename}.xlsx")
                df.to_excel(excel_path, index=False, engine='openpyxl')
                
                with open(excel_path, 'rb') as f:
                    st.download_button(
                        label="Download Excel",
                        data=f,
                        file_name=f"{filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        
        if export_format in ["CSV", "All Formats"]:
            with col2:
                csv_path = os.path.join('data', f"{filename}.csv")
                df.to_csv(csv_path, index=False)
                
                with open(csv_path, 'rb') as f:
                    st.download_button(
                        label="Download CSV",
                        data=f,
                        file_name=f"{filename}.csv",
                        mime="text/csv"
                    )
        
        if export_format in ["JSON", "All Formats"]:
            with col3:
                json_path = os.path.join('data', f"{filename}.json")
                df.to_json(json_path, orient='records', date_format='iso', indent=4)
                
                with open(json_path, 'rb') as f:
                    st.download_button(
                        label="Download JSON",
                        data=f,
                        file_name=f"{filename}.json",
                        mime="application/json"
                    )
        
        # Generate and export summary report
        st.markdown("---")
        st.subheader("📑 Summary Report")
        
        # Create a summary report with visualizations
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Rating Distribution", 
                "Sentiment Analysis",
                "Reviews Over Time",
                "Top Reviewers"
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "scatter"}, {"type": "bar"}]
            ]
        )
        
        # Rating distribution
        if 'rating' in df.columns:
            rating_counts = df['rating'].value_counts().sort_index()
            fig.add_trace(
                go.Bar(
                    x=rating_counts.index,
                    y=rating_counts.values,
                    name="Ratings",
                    marker_color='royalblue'
                ),
                row=1, col=1
            )
            fig.update_xaxes(title_text="Rating", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=1, col=1)
        
        # Sentiment analysis
        if 'sentiment' in df.columns:
            sentiment_counts = df['sentiment'].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=sentiment_counts.index,
                    values=sentiment_counts.values,
                    name="Sentiment",
                    marker_colors=['green', 'yellow', 'red']
                ),
                row=1, col=2
            )
        
        # Reviews over time
        if 'date' in df.columns:
            df_with_date = df.dropna(subset=['date'])
            if not df_with_date.empty:
                df_with_date['month'] = pd.to_datetime(df_with_date['date']).dt.strftime('%Y-%m')
                reviews_by_month = df_with_date.groupby('month').size().reset_index(name='count')
                reviews_by_month = reviews_by_month.sort_values('month')
                
                fig.add_trace(
                    go.Scatter(
                        x=reviews_by_month['month'],
                        y=reviews_by_month['count'],
                        mode='lines+markers',
                        name="Reviews",
                        line=dict(color='green', width=2)
                    ),
                    row=2, col=1
                )
                fig.update_xaxes(title_text="Month", row=2, col=1)
                fig.update_yaxes(title_text="Count", row=2, col=1)
        
        # Top reviewers
        if 'reviewer' in df.columns:
            top_reviewers = df['reviewer'].value_counts().head(10)
            fig.add_trace(
                go.Bar(
                    x=top_reviewers.index,
                    y=top_reviewers.values,
                    name="Reviewers",
                    marker_color='orange'
                ),
                row=2, col=2
            )
            fig.update_xaxes(title_text="Reviewer", row=2, col=2)
            fig.update_yaxes(title_text="Count", row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title_text=f"TripAdvisor Review Analysis - {summary.get('total_reviews', 0)} Reviews",
            height=800,
            width=1200,
            showlegend=False
        )
        
        # Display the figure
        st.plotly_chart(fig, use_container_width=True)
        
        # Export the summary report
        html_path = os.path.join('data', f"{filename}_report.html")
        fig.write_html(html_path)
        
        with open(html_path, 'rb') as f:
            st.download_button(
                label="Download Summary Report",
                data=f,
                file_name=f"{filename}_report.html",
                mime="text/html"
            )
