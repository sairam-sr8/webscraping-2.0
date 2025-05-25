"""
Export utilities for TripAdvisor data.
Handles exporting data to various formats including Excel, CSV, and JSON.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger("TripAdvisorExport")

class DataExporter:
    """Export TripAdvisor data to various formats."""
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, filename: str, sheet_name: str = "Reviews") -> str:
        """
        Export DataFrame to Excel file.
        
        Args:
            df: DataFrame to export
            filename: Name of the Excel file
            sheet_name: Name of the sheet
            
        Returns:
            Path to the exported file
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Add timestamp to filename to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not filename.endswith('.xlsx'):
                filename = f"{filename}.xlsx"
            
            filepath = os.path.join('data', f"{os.path.splitext(filename)[0]}_{timestamp}.xlsx")
            
            # Export to Excel
            df.to_excel(filepath, sheet_name=sheet_name, index=False, engine='openpyxl')
            logger.info(f"Data exported to Excel: {filepath}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return ""
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, filename: str) -> str:
        """
        Export DataFrame to CSV file.
        
        Args:
            df: DataFrame to export
            filename: Name of the CSV file
            
        Returns:
            Path to the exported file
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Add timestamp to filename to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not filename.endswith('.csv'):
                filename = f"{filename}.csv"
            
            filepath = os.path.join('data', f"{os.path.splitext(filename)[0]}_{timestamp}.csv")
            
            # Export to CSV
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Data exported to CSV: {filepath}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return ""
    
    @staticmethod
    def export_to_json(df: pd.DataFrame, filename: str) -> str:
        """
        Export DataFrame to JSON file.
        
        Args:
            df: DataFrame to export
            filename: Name of the JSON file
            
        Returns:
            Path to the exported file
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Add timestamp to filename to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not filename.endswith('.json'):
                filename = f"{filename}.json"
            
            filepath = os.path.join('data', f"{os.path.splitext(filename)[0]}_{timestamp}.json")
            
            # Export to JSON
            df.to_json(filepath, orient='records', date_format='iso', indent=4)
            logger.info(f"Data exported to JSON: {filepath}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return ""
    
    @staticmethod
    def export_summary_report(df: pd.DataFrame, summary: Dict, filename: str) -> str:
        """
        Export a summary report with visualizations.
        
        Args:
            df: DataFrame of reviews
            summary: Dictionary with summary statistics
            filename: Name of the report file
            
        Returns:
            Path to the exported file
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Add timestamp to filename to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not filename.endswith('.html'):
                filename = f"{filename}.html"
            
            filepath = os.path.join('data', f"{os.path.splitext(filename)[0]}_{timestamp}.html")
            
            # Create a subplot figure
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
                    df_with_date['month'] = df_with_date['date'].dt.strftime('%Y-%m')
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
            
            # Write to HTML file
            fig.write_html(filepath)
            logger.info(f"Summary report exported to HTML: {filepath}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting summary report: {e}")
            return ""
