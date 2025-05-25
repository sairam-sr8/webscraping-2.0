# TripAdvisor Scraper Pro

A professional, state-of-the-art web scraping application for extracting, analyzing, and visualizing hotel reviews from TripAdvisor.

## Features

- **Advanced Web Scraping**: Extract hotel information and reviews with robust error handling and multiple fallback selectors
- **Multi-Strategy Scraping**: Support for both requests-based and Selenium-based scraping for JavaScript-rendered content
- **Anti-Blocking Measures**: User-agent rotation, proxy support, and rate limiting to avoid IP blocks
- **Data Processing**: Clean and analyze scraped data with sentiment analysis
- **Data Visualization**: Interactive charts and graphs for review analysis
- **Database Storage**: SQLite database for storing and retrieving hotel and review data
- **Export Options**: Export data to Excel, CSV, JSON, and HTML reports
- **Modern UI**: Beautiful Streamlit interface with responsive design
- **Region Scraping**: Scrape multiple hotels from a region or country
- **Search & Filter**: Search and filter reviews by text and rating

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tripadvisor-scraper-pro.git
cd tripadvisor-scraper-pro
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and navigate to http://localhost:8501

3. Use the sidebar to:
   - Scrape a single hotel by URL
   - Scrape multiple hotels from a region
   - Load previously scraped data from the database

4. View and analyze the results in the main panel

5. Export the data in your preferred format

## Project Structure

```
tripadvisor-scraper-pro/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Project dependencies
├── data/                   # Data storage directory
│   └── tripadvisor.db      # SQLite database
├── scraper/                # Scraper modules
│   ├── __init__.py
│   └── tripadvisor.py      # Core scraper implementation
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── database.py         # Database utilities
│   └── export.py           # Export utilities
└── ui/                     # UI components
    ├── __init__.py
    └── components.py       # Streamlit UI components
```

## Advanced Options

### Proxy Support

To use proxy rotation:
1. Check the "Use Proxy Rotation" option in the sidebar
2. Enter your proxy list (one per line) in the format:
   ```
   http://user:pass@proxy.example.com:8080
   https://proxy2.example.com:8080
   ```

### Selenium Support

For JavaScript-rendered content:
1. Check the "Use Selenium" option when scraping a hotel
2. Ensure you have Chrome installed on your system

## Data Analysis

The application provides several data analysis features:

- **Rating Distribution**: View the distribution of ratings
- **Sentiment Analysis**: See the breakdown of positive, neutral, and negative reviews
- **Timeline Analysis**: Track review trends over time
- **Top Reviewers**: Identify the most frequent reviewers

## Export Options

Export your data in multiple formats:

- **Excel**: Spreadsheet format for data analysis
- **CSV**: Comma-separated values for compatibility
- **JSON**: Structured data for API integration
- **HTML Report**: Interactive report with visualizations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Always respect TripAdvisor's Terms of Service and robots.txt file. Use responsibly and ethically.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
