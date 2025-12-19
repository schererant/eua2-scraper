#!/usr/bin/env python3
"""
EUA 2 Futures Price Scraper
Scrapes historical price data from ICE website for EUA 2 Futures
"""

import ast
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright, Page


class EUA2FuturesScraper:
    """Scraper for EUA 2 Futures data from ICE website"""
    
    def __init__(self, output_file: str = "eua2_futures_data.csv"):
        self.output_file = output_file
        self.base_url = "https://www.ice.com/products/83048353/EUA-2-Futures/data"
        self.market_id = "8322696"
        self.data_points: List[Dict] = []
        
    def scrape_data(self, try_multiple_spans: bool = True) -> List[Dict]:
        """
        Scrape historical data from ICE website
        
        Args:
            try_multiple_spans: Try different span values to get more historical data
            
        Returns:
            List of dictionaries containing date and price data
        """
        print("Starting EUA 2 Futures data scraper...")
        
        all_data = []
        spans_to_try = [3, 1, 2, 5, 10] if try_multiple_spans else [3]
        
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            for span in spans_to_try:
                print(f"\n--- Trying span={span} ---")
                
                # Collect network responses
                api_responses = []
                
                def handle_response(response):
                    url = response.url
                    # Look for API endpoints that might contain price data
                    if any(keyword in url.lower() for keyword in ['api', 'data', 'chart', 'price', 'market', 'historical', 'timeseries']):
                        api_responses.append(response)
                
                page.on("response", handle_response)
                
                try:
                    # Navigate to the page with different span values
                    url = f"{self.base_url}?marketId={self.market_id}&span={span}"
                    print(f"Navigating to: {url}")
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    # Wait for the page to fully load and make API calls
                    print("Waiting for page to load and API calls to complete...")
                    time.sleep(8)
                    
                    # Try multiple strategies to extract data
                    data = []
                    
                    # Strategy 1: Extract from intercepted API responses
                    print("Strategy 1: Extracting from API responses...")
                    for response in api_responses:
                        try:
                            if response.status == 200:
                                content_type = response.headers.get('content-type', '')
                                if 'json' in content_type:
                                    json_data = response.json()
                                    extracted = self._parse_json_data(json_data)
                                    if extracted:
                                        print(f"  Found {len(extracted)} data points from {response.url}")
                                        data.extend(extracted)
                        except Exception as e:
                            continue
                    
                    # Strategy 2: Try to extract from page JavaScript/globals
                    if not data:
                        print("Strategy 2: Extracting from page JavaScript...")
                        page_data = self._extract_from_javascript(page)
                        if page_data:
                            data.extend(page_data)
                            print(f"  Found {len(page_data)} data points from JavaScript")
                    
                    # Strategy 3: Try to find data in page content/scripts
                    if not data:
                        print("Strategy 3: Extracting from page content...")
                        content_data = self._extract_from_page_content(page)
                        if content_data:
                            data.extend(content_data)
                            print(f"  Found {len(content_data)} data points from page content")
                    
                    # Strategy 4: Try to interact with chart elements
                    if not data:
                        print("Strategy 4: Attempting to extract from chart...")
                        chart_data = self._extract_from_chart_interaction(page)
                        if chart_data:
                            data.extend(chart_data)
                            print(f"  Found {len(chart_data)} data points from chart")
                    
                    if data:
                        all_data.extend(data)
                        print(f"✓ Extracted {len(data)} data points for span={span}")
                    else:
                        print(f"⚠ No data extracted for span={span}")
                    
                    # Remove response handler before next iteration
                    page.remove_listener("response", handle_response)
                    
                except Exception as e:
                    print(f"Error during scraping for span={span}: {e}")
                    continue
            
            browser.close()
        
        if all_data:
            # Remove duplicates
            seen = set()
            unique_data = []
            for item in all_data:
                key = (item.get('date'), item.get('price'))
                if key not in seen:
                    seen.add(key)
                    unique_data.append(item)
            
            print(f"\n✓ Successfully extracted {len(unique_data)} unique data points total")
            self.data_points = unique_data
            return unique_data
        else:
            print("\n⚠ Warning: No data extracted with any method.")
            print("  The website structure may have changed or require authentication.")
            return []
    
    
    def _extract_from_javascript(self, page: Page) -> List[Dict]:
        """Extract data from JavaScript variables and functions"""
        data = []
        
        try:
            # Try to execute JavaScript to find data
            js_code = """
            () => {
                const results = [];
                
                // Common variable names that might contain chart data
                const possibleVars = [
                    'chartData', 'priceData', 'historicalData', 'data', 'series',
                    'priceSeries', 'marketData', 'futuresData', 'euaData',
                    'chart', 'graph', 'dataset', 'values', 'points'
                ];
                
                // Check window object
                for (const varName of possibleVars) {
                    try {
                        if (window[varName] && typeof window[varName] !== 'function') {
                            results.push({source: 'window.' + varName, data: window[varName]});
                        }
                    } catch(e) {}
                }
                
                // Check for chart libraries (Highcharts, Chart.js, etc.)
                if (window.Highcharts && window.Highcharts.charts) {
                    for (let chart of window.Highcharts.charts) {
                        if (chart && chart.series) {
                            for (let series of chart.series) {
                                if (series.data) {
                                    results.push({source: 'Highcharts', data: series.data});
                                }
                            }
                        }
                    }
                }
                
                if (window.Chart && window.Chart.instances) {
                    for (let chartId in window.Chart.instances) {
                        let chart = window.Chart.instances[chartId];
                        if (chart.data && chart.data.datasets) {
                            results.push({source: 'Chart.js', data: chart.data.datasets});
                        }
                    }
                }
                
                // Try to find data in DOM elements with data attributes
                const elementsWithData = document.querySelectorAll('[data-series], [data-chart], [data-values]');
                for (let el of elementsWithData) {
                    try {
                        const dataAttr = el.getAttribute('data-series') || 
                                       el.getAttribute('data-chart') || 
                                       el.getAttribute('data-values');
                        if (dataAttr) {
                            const parsed = JSON.parse(dataAttr);
                            results.push({source: 'DOM data attribute', data: parsed});
                        }
                    } catch(e) {}
                }
                
                return results;
            }
            """
            
            js_results = page.evaluate(js_code)
            
            for result in js_results:
                extracted = self._parse_json_data(result.get('data'))
                if extracted:
                    data.extend(extracted)
                    
        except Exception as e:
            print(f"Error extracting from JavaScript: {e}")
        
        return data
    
    def _extract_from_chart_interaction(self, page: Page) -> List[Dict]:
        """Try to extract data by interacting with the chart"""
        data = []
        
        try:
            # Look for chart elements and try to get tooltip data
            chart_selectors = [
                'canvas',
                '[class*="chart"]',
                '[id*="chart"]',
                '[class*="graph"]',
                '[id*="graph"]',
                'svg',
            ]
            
            for selector in chart_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        # Try to hover over chart to trigger tooltip data
                        for element in elements:
                            try:
                                # Hover over different points
                                box = element.bounding_box()
                                if box:
                                    # Try hovering at different x positions
                                    for x_offset in [0.1, 0.3, 0.5, 0.7, 0.9]:
                                        page.mouse.move(box['x'] + box['width'] * x_offset, 
                                                       box['y'] + box['height'] * 0.5)
                                        time.sleep(0.1)
                                        
                                        # Try to find tooltip with data
                                        tooltip = page.query_selector('[class*="tooltip"], [id*="tooltip"]')
                                        if tooltip:
                                            tooltip_text = tooltip.inner_text()
                                            # Try to parse date and price from tooltip
                                            parsed = self._parse_tooltip_text(tooltip_text)
                                            if parsed:
                                                data.append(parsed)
                            except:
                                continue
                except:
                    continue
                    
        except Exception as e:
            print(f"Error extracting from chart interaction: {e}")
        
        return data
    
    def _parse_tooltip_text(self, text: str) -> Optional[Dict]:
        """Parse tooltip text to extract date and price"""
        import re
        
        # Common patterns: "Date: 2023-01-01, Price: 85.50" or "2023-01-01: €85.50"
        date_patterns = [
            r'(\d{4}[-/]\d{2}[-/]\d{2})',
            r'(\d{2}[-/]\d{2}[-/]\d{4})',
        ]
        
        price_patterns = [
            r'[\d,]+\.?\d*',
            r'€\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)',
        ]
        
        date_match = None
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_match = match.group(1)
                break
        
        price_match = None
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                price_match = match.group(1) if match.groups() else match.group(0)
                break
        
        if date_match and price_match:
            try:
                # Normalize date
                date_str = date_match.replace('/', '-')
                # Normalize price (remove commas, currency symbols)
                price = float(price_match.replace(',', ''))
                return {'date': date_str, 'price': price}
            except:
                pass
        
        return None
    
    def _save_debug_info(self, page: Page):
        """Save debug information for troubleshooting"""
        try:
            debug_dir = Path('debug')
            debug_dir.mkdir(exist_ok=True)
            
            # Save page HTML
            html = page.content()
            with open(debug_dir / 'page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Save page screenshot
            page.screenshot(path=str(debug_dir / 'screenshot.png'))
            
            print(f"  Debug info saved to {debug_dir}/")
        except Exception as e:
            print(f"  Could not save debug info: {e}")
    
    def _extract_from_page_content(self, page: Page) -> List[Dict]:
        """Try to extract data from page content and scripts"""
        data = []
        
        try:
            # Get page content
            content = page.content()
            
            # Look for JSON data in script tags
            import re
            json_patterns = [
                r'var\s+\w+\s*=\s*(\{.*?\});',
                r'data:\s*(\[.*?\])',
                r'prices:\s*(\[.*?\])',
                r'values:\s*(\[.*?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    try:
                        json_data = json.loads(match)
                        extracted = self._parse_json_data(json_data)
                        if extracted:
                            data.extend(extracted)
                    except:
                        continue
            
            # Also check for data in window object
            try:
                page_data = page.evaluate("""
                    () => {
                        const data = [];
                        // Try common variable names
                        const vars = ['chartData', 'priceData', 'historicalData', 'data', 'series'];
                        for (const varName of vars) {
                            if (window[varName]) {
                                data.push({name: varName, value: window[varName]});
                            }
                        }
                        return data;
                    }
                """)
                
                for item in page_data:
                    extracted = self._parse_json_data(item.get('value'))
                    if extracted:
                        data.extend(extracted)
            except:
                pass
                
        except Exception as e:
            print(f"Error extracting from page content: {e}")
        
        return data
    
    
    def _parse_json_data(self, data: any) -> List[Dict]:
        """Parse JSON data to extract price and date information"""
        extracted = []
        
        if not data:
            return extracted
        
        try:
            # Handle different data structures
            if isinstance(data, list):
                for item in data:
                    parsed = self._parse_data_item(item)
                    if parsed:
                        extracted.append(parsed)
            elif isinstance(data, dict):
                # Check common keys
                for key in ['data', 'series', 'values', 'prices', 'points', 'items']:
                    if key in data:
                        items = data[key]
                        if isinstance(items, list):
                            for item in items:
                                parsed = self._parse_data_item(item)
                                if parsed:
                                    extracted.append(parsed)
                
                # Also try to parse the dict itself
                parsed = self._parse_data_item(data)
                if parsed:
                    extracted.append(parsed)
                    
        except Exception as e:
            print(f"Error parsing JSON data: {e}")
        
        return extracted
    
    def _parse_data_item(self, item: any) -> Optional[Dict]:
        """Parse a single data item to extract date and price"""
        if not isinstance(item, (dict, list)):
            return None
        
        try:
            # Common field names for dates
            date_fields = ['date', 'time', 'timestamp', 'x', 'datetime', 't']
            # Common field names for prices
            price_fields = ['price', 'value', 'y', 'close', 'last', 'settlement']
            
            date_value = None
            price_value = None
            
            if isinstance(item, dict):
                # Try to find date
                for field in date_fields:
                    if field in item:
                        date_value = item[field]
                        break
                
                # Try to find price
                for field in price_fields:
                    if field in item:
                        price_value = item[field]
                        break
                
                # If it's a list-like structure [timestamp, value]
                if date_value is None and price_value is None and len(item) == 2:
                    values = list(item.values())
                    if len(values) == 2:
                        date_value = values[0]
                        price_value = values[1]
            
            elif isinstance(item, list) and len(item) >= 2:
                date_value = item[0]
                price_value = item[1]
            
            if date_value and price_value:
                # Normalize date to YYYY-MM-DD format
                date_obj = None
                
                if isinstance(date_value, (int, float)):
                    # Might be Unix timestamp (in milliseconds or seconds)
                    if date_value > 1e10:
                        date_value = date_value / 1000
                    date_obj = datetime.fromtimestamp(date_value)
                else:
                    # Try to parse date string
                    date_str = str(date_value).strip()
                    date_formats = [
                        '%Y-%m-%d',
                        '%a %b %d %H:%M:%S %Y',  # "Mon Jun 30 00:00:00 2025"
                        '%Y-%m-%d %H:%M:%S',
                        '%m/%d/%Y',
                        '%d/%m/%Y',
                    ]
                    for fmt in date_formats:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            break
                        except:
                            continue
                    
                    # If still not parsed, try regex
                    if not date_obj:
                        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
                        if date_match:
                            try:
                                date_obj = datetime(int(date_match.group(1)), 
                                                   int(date_match.group(2)), 
                                                   int(date_match.group(3)))
                            except:
                                pass
                
                if not date_obj:
                    return None
                
                # Format date as YYYY-MM-DD
                date_str = date_obj.strftime('%Y-%m-%d')
                
                # Normalize price
                try:
                    price = float(price_value)
                    # Skip invalid prices (market IDs, etc.)
                    if price <= 0 or price > 1000000:
                        return None
                except:
                    return None
                
                return {
                    'date': date_str,
                    'price': price
                }
                
        except Exception as e:
            pass
        
        return None
    
    def load_existing_csv(self) -> List[Dict]:
        """
        Load existing data from CSV file if it exists
        Handles both normal CSV format and malformed nested list format
        
        Returns:
            List of dictionaries containing existing date and price data
        """
        existing_data = []
        output_path = Path(self.output_file)
        
        if not output_path.exists():
            return existing_data
        
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    date_str = row.get('date', '').strip()
                    price_str = row.get('price', '').strip()
                    
                    # Remove surrounding quotes if present
                    date_str = date_str.strip('"').strip("'")
                    price_str = price_str.strip('"').strip("'")
                    
                    # Check if the date column contains a list (malformed data)
                    if date_str.startswith('[[') or date_str.startswith('['):
                        # Try to parse the nested list structure
                        try:
                            parsed_data = ast.literal_eval(date_str)
                            if isinstance(parsed_data, list):
                                for item in parsed_data:
                                    if isinstance(item, list) and len(item) >= 2:
                                        date_val = str(item[0])
                                        price_val = float(item[1])
                                        # Parse date string to YYYY-MM-DD format
                                        try:
                                            from datetime import datetime
                                            date_obj = datetime.strptime(date_val, '%a %b %d %H:%M:%S %Y')
                                            date_formatted = date_obj.strftime('%Y-%m-%d')
                                            existing_data.append({
                                                'date': date_formatted,
                                                'price': price_val
                                            })
                                        except:
                                            # If date parsing fails, try to use as-is
                                            existing_data.append({
                                                'date': date_val,
                                                'price': price_val
                                            })
                        except:
                            continue
                    else:
                        # Normal CSV format - skip if price looks like a market ID (very large number)
                        if date_str and price_str:
                            try:
                                price = float(price_str.replace(',', ''))
                                # Skip if price is suspiciously large (like a market ID) or invalid
                                if price > 1000000 or price <= 0:
                                    continue
                                # Validate date format (should be YYYY-MM-DD)
                                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                                    # Try to parse and reformat
                                    try:
                                        date_obj = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                                        date_str = date_obj.strftime('%Y-%m-%d')
                                    except:
                                        # Try other formats
                                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                                            try:
                                                date_obj = datetime.strptime(date_str, fmt)
                                                date_str = date_obj.strftime('%Y-%m-%d')
                                                break
                                            except:
                                                continue
                                existing_data.append({
                                    'date': date_str,
                                    'price': price
                                })
                            except:
                                continue
        except Exception as e:
            print(f"Warning: Could not load existing CSV: {e}")
        
        return existing_data
    
    def cleanup_csv(self) -> int:
        """
        Clean up the CSV file by removing malformed rows and ensuring proper format
        
        Returns:
            Number of records after cleanup
        """
        output_path = Path(self.output_file)
        if not output_path.exists():
            return 0
        
        # Load all data (this will parse malformed rows)
        existing_data = self.load_existing_csv()
        
        if not existing_data:
            return 0
        
        # Save cleaned data back
        self.save_to_csv(existing_data, update_existing=False)
        return len(existing_data)
    
    def save_to_csv(self, data: Optional[List[Dict]] = None, update_existing: bool = True) -> str:
        """
        Save scraped data to CSV file, merging with existing data if update_existing is True
        
        Args:
            data: Optional data to save. If None, uses self.data_points
            update_existing: If True, merge with existing CSV data. If False, overwrite.
            
        Returns:
            Path to the saved CSV file
        """
        if data is None:
            data = self.data_points
        
        if not data:
            raise ValueError("No data to save")
        
        output_path = Path(self.output_file)
        
        # Load existing data if updating
        if update_existing and output_path.exists():
            existing_data = self.load_existing_csv()
            print(f"Found {len(existing_data)} existing data points in CSV")
            
            # Merge data: combine existing and new, then deduplicate
            all_data = existing_data + data
            
            # Create a dictionary keyed by date to handle duplicates (keep latest price)
            data_dict = {}
            for item in all_data:
                date = item.get('date')
                if date:
                    # If date already exists, keep the one with the newer data (prefer new over old)
                    if date not in data_dict or date in [d.get('date') for d in data]:
                        data_dict[date] = item
            
            # Convert back to list
            merged_data = list(data_dict.values())
            print(f"Merged with existing data: {len(merged_data)} total unique data points")
        else:
            merged_data = data
        
        # Sort by date
        merged_data = sorted(merged_data, key=lambda x: x.get('date', ''))
        
        # Remove duplicates based on date (final pass)
        seen_dates = set()
        unique_data = []
        for item in merged_data:
            date = item.get('date')
            if date and date not in seen_dates:
                seen_dates.add(date)
                unique_data.append(item)
        
        # Write to CSV - ensure clean format
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if unique_data:
                fieldnames = ['date', 'price']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                # Write clean, properly formatted rows
                for item in unique_data:
                    # Ensure date is in YYYY-MM-DD format
                    date_str = item.get('date', '')
                    date_obj = None
                    
                    # Handle different date formats
                    if isinstance(date_str, datetime):
                        date_obj = date_str
                    elif isinstance(date_str, str):
                        # Try to parse various date formats
                        date_formats = [
                            '%Y-%m-%d',
                            '%a %b %d %H:%M:%S %Y',  # "Mon Jun 30 00:00:00 2025"
                            '%Y-%m-%d %H:%M:%S',
                            '%m/%d/%Y',
                            '%d/%m/%Y',
                        ]
                        for fmt in date_formats:
                            try:
                                date_obj = datetime.strptime(date_str.strip(), fmt)
                                break
                            except:
                                continue
                        
                        # If still not parsed, try regex
                        if not date_obj:
                            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
                            if date_match:
                                try:
                                    date_obj = datetime(int(date_match.group(1)), 
                                                       int(date_match.group(2)), 
                                                       int(date_match.group(3)))
                                except:
                                    pass
                    else:
                        continue
                    
                    if not date_obj:
                        continue
                    
                    # Format date as YYYY-MM-DD
                    date_formatted = date_obj.strftime('%Y-%m-%d')
                    
                    # Ensure price is a float
                    price = item.get('price', 0)
                    if not isinstance(price, (int, float)):
                        try:
                            price = float(price)
                        except:
                            continue
                    
                    # Only write valid data (skip market IDs and invalid prices)
                    if date_formatted and price > 0 and price < 1000000:
                        writer.writerow({
                            'date': date_formatted,
                            'price': f'{price:.2f}'
                        })
        
        # Count new records (dates that are in the newly scraped data)
        new_dates = set(d.get('date') for d in data)
        new_count = len([d for d in unique_data if d.get('date') in new_dates])
        
        if update_existing and output_path.exists():
            print(f"Saved {len(unique_data)} total data points to {output_path} ({new_count} new/updated)")
        else:
            print(f"Saved {len(unique_data)} data points to {output_path}")
        
        return str(output_path)


def main():
    """Main function to run the scraper"""
    scraper = EUA2FuturesScraper()
    
    try:
        # Scrape the data
        data = scraper.scrape_data()
        
        if data:
            # Save to CSV
            output_file = scraper.save_to_csv(data)
            print(f"\n✓ Successfully scraped and saved data to {output_file}")
            print(f"  Total records: {len(data)}")
            if data:
                print(f"  Date range: {data[0].get('date')} to {data[-1].get('date')}")
        else:
            print("\n✗ No data was extracted. The website structure may have changed.")
            print("  Please check the website manually or update the scraper.")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

