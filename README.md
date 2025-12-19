# EUA 2 Futures Price Scraper

A Python tool to scrape historical EUA 2 Futures price data from the ICE (Intercontinental Exchange) website and store it in a CSV file.

## Overview

This scraper extracts historical price and date data for EUA 2 Futures from the ICE website (https://www.ice.com/products/83048353/EUA-2-Futures/data). The tool uses Playwright to handle dynamic JavaScript content and attempts to extract data as far back as available.

## Features

- Scrapes historical EUA 2 Futures prices from ICE website
- Handles dynamic JavaScript content using Playwright
- Exports data to CSV format
- Attempts multiple extraction strategies for robustness
- Removes duplicate entries
- Sorts data chronologically

## Requirements

- Python 3.7 or higher
- Playwright browser automation library
- Matplotlib for data visualization

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd eua2-scraper
```

2. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
python -m playwright install chromium
```

**Note:** The virtual environment is already created in this repository. To activate it:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Usage

### Scraping Data

**Recommended: Use the main scraper script** (always updates CSV with new data):
```bash
python scrape_eua2.py
```

This script:
- Scrapes new data from the ICE website
- Merges with existing data in `eua2_futures_data.csv`
- Preserves all historical data
- Shows summary of new and total records
- Automatically updates the visualization (`eua2_futures_visualization.png`)

**Important:** To get the latest updated data, you need to run the scraper again. The scraper does not automatically update data in the background. Each time you run `scrape_eua2.py`, it will:
1. Check for new data on the ICE website
2. Merge any new data points with your existing CSV file
3. Update the CSV file with the latest information

**Example workflow for regular updates:**
```bash
# Run daily/weekly to get latest prices
python scrape_eua2.py

# Then visualize the updated data
python visualize.py
```

**Alternative: Run scraper directly** (overwrites CSV):
```bash
python scraper.py
```

### Visualizing Data

After scraping data, create a professional visualization:

```bash
python visualize.py
```

This creates/updates `eua2_futures_visualization.png` with a clean, professional line chart showing:
- Historical price trend with gradient fill
- Highlighted minimum and maximum price points
- Average price line
- Clear date formatting on x-axis
- Optimized y-axis scale for better readability

**Note:** The visualization is automatically updated (overwritten) each time you run the script, so you always have the latest version without accumulating multiple files.

**Other options**:
```bash
# Custom CSV file
python visualize.py --csv path/to/your/data.csv

# Save without displaying
python visualize.py --no-show

# Custom output file
python visualize.py --output my_visualization.png
```

### Programmatic Usage

You can also use the scraper as a Python module:

```python
from scraper import EUA2FuturesScraper

# Create scraper instance
scraper = EUA2FuturesScraper(output_file="my_data.csv")

# Scrape data (tries multiple time spans for maximum historical data)
data = scraper.scrape_data(try_multiple_spans=True)

# Save to CSV
if data:
    scraper.save_to_csv(data)
```

The script will:
1. Navigate to the ICE EUA 2 Futures data page with different time spans
2. Extract historical price data using multiple strategies
3. Remove duplicates and sort chronologically
4. Save the data to `eua2_futures_data.csv`

### Output Format

The CSV file contains two columns:
- `date`: Date in YYYY-MM-DD format
- `price`: Closing/settlement price for that date

Example:
```csv
date,price
2023-01-01,85.50
2023-01-02,86.20
2023-01-03,85.90
```

## How It Works

This section explains the technical details of how the scraper extracts data from the ICE website.

### Architecture Overview

The scraper uses **Playwright**, a browser automation library, to interact with the ICE website as a real browser would. This approach is necessary because the ICE website loads data dynamically using JavaScript, which requires a full browser environment to execute.

### Scraping Process

#### 1. **Browser Initialization**

The scraper launches a headless Chromium browser with:
- A realistic user agent string to avoid detection
- A standard viewport size (1920x1080)
- Network request monitoring enabled

#### 2. **Multiple Time Span Strategy**

To maximize historical data collection, the scraper tries multiple time span values:
- **span=1**: Most recent data
- **span=2**: Medium-term history
- **span=3**: Extended history (default)
- **span=5**: Long-term history
- **span=10**: Maximum available history

Each span value is tried sequentially, and all extracted data is combined to build a comprehensive dataset.

#### 3. **Data Extraction Strategies**

The scraper employs four different extraction strategies, trying them in order until data is found:

##### Strategy 1: API Response Interception
- **How it works**: Monitors all network requests made by the page
- **What it looks for**: API endpoints containing keywords like `api`, `data`, `chart`, `price`, `market`, `historical`, or `timeseries`
- **Extraction method**: Intercepts JSON responses and parses them for price/date pairs
- **Advantages**: Most reliable method when available, gets raw data directly

##### Strategy 2: JavaScript Variable Extraction
- **How it works**: Executes JavaScript code in the page context to search for data
- **What it looks for**: 
  - Common variable names (`chartData`, `priceData`, `historicalData`, etc.)
  - Chart library data structures (Highcharts, Chart.js)
  - DOM elements with data attributes
- **Extraction method**: Accesses JavaScript objects and arrays containing price data
- **Advantages**: Works when data is stored in JavaScript variables

##### Strategy 3: Page Content Parsing
- **How it works**: Searches the HTML source code for embedded data
- **What it looks for**:
  - JSON data in `<script>` tags
  - Data attributes in HTML elements
  - Inline JavaScript with data structures
- **Extraction method**: Uses regex patterns and JSON parsing to extract data
- **Advantages**: Works when data is embedded in the page HTML

##### Strategy 4: Chart Element Interaction
- **How it works**: Interacts with chart elements by hovering over different points
- **What it looks for**: Chart tooltips that display price information
- **Extraction method**: Simulates mouse movements and extracts tooltip text
- **Advantages**: Fallback method when other strategies fail

### Data Processing Pipeline

#### 1. **Data Parsing**
Once raw data is extracted, the scraper normalizes it:
- **Date normalization**: Converts various date formats (Unix timestamps, date strings, etc.) to `YYYY-MM-DD` format
- **Price normalization**: Ensures prices are floating-point numbers
- **Validation**: Filters out invalid data (negative prices, future dates, etc.)

#### 2. **Deduplication**
- Removes duplicate entries based on date
- If multiple prices exist for the same date, keeps the most recent one
- Ensures data integrity

#### 3. **Chronological Sorting**
- Sorts all data points by date
- Ensures the CSV file is in chronological order

### CSV Update Mechanism

The scraper implements an intelligent update system:

#### Loading Existing Data
1. Checks if `eua2_futures_data.csv` exists
2. If it exists, loads all existing records
3. Handles both clean CSV format and malformed nested list formats (for backward compatibility)
4. Validates and normalizes existing data

#### Merging New Data
1. Combines existing data with newly scraped data
2. Removes duplicates (keeps newer data when conflicts occur)
3. Sorts the merged dataset chronologically
4. Validates all entries before saving

#### Saving Clean CSV
1. Writes data in clean, standardized format:
   - Dates in `YYYY-MM-DD` format
   - Prices formatted to 2 decimal places
   - Proper CSV escaping
2. Overwrites the file with the complete, cleaned dataset
3. Ensures no malformed rows remain

### Error Handling

The scraper includes robust error handling:
- **Network errors**: Continues with next span value if one fails
- **Parsing errors**: Skips invalid data points and continues
- **Browser crashes**: Gracefully closes browser and reports error
- **Missing data**: Provides clear error messages and suggestions
- **Multiple strategies**: If one extraction method fails, tries the next automatically

### Performance Considerations

- **Headless mode**: Runs without GUI for faster execution
- **Parallel span processing**: Could be optimized for parallel requests (currently sequential)
- **Caching**: Existing CSV data is loaded once and reused
- **Memory management**: Browser instances are properly closed after use

### Limitations and Workarounds

1. **Dynamic Content**: The ICE website uses JavaScript to load data, which is why Playwright is necessary
2. **Rate Limiting**: The scraper includes delays between requests to avoid overwhelming the server
3. **Website Changes**: Multiple extraction strategies provide resilience against website structure changes
4. **Data Availability**: Historical data depends on what ICE provides on their public pages

### Technical Stack

- **Playwright**: Browser automation and JavaScript execution
- **Matplotlib**: Data visualization and chart generation
- **Python CSV module**: CSV file handling
- **Python datetime**: Date parsing and formatting
- **AST module**: Safe evaluation of JavaScript data structures
- **Regular expressions**: Pattern matching for data extraction

## Troubleshooting

If the scraper fails to extract data:

1. **Website Structure Changed**: The ICE website may have updated its structure. Check the website manually to see if the data is still accessible.

2. **Rate Limiting**: The website may be rate-limiting requests. Try running the scraper again after a delay.

3. **Browser Issues**: Ensure Playwright browsers are properly installed:
   ```bash
   playwright install chromium
   ```

4. **Network Issues**: Check your internet connection and ensure the ICE website is accessible.

## Limitations

- The scraper depends on the ICE website structure remaining relatively stable
- Some data may require authentication or subscription to access
- Historical data availability depends on what ICE provides on their public pages
- The scraper runs in headless mode by default; you can modify it to run in headed mode for debugging

## Legal and Ethical Considerations

- This scraper is for educational and personal use
- Ensure compliance with ICE's Terms of Service
- Respect rate limits and don't overload their servers
- Consider using official ICE Data Services APIs for commercial use

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is for educational purposes. Please ensure compliance with ICE's Terms of Service when using this tool.

## Author

Created for scraping EUA 2 Futures historical data from ICE.

