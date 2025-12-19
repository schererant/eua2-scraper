#!/usr/bin/env python3
"""
EUA 2 Futures Scraper
Scrapes historical price data and updates the CSV file with new data.
Always merges with existing data to maintain complete historical record.
"""

from scraper import EUA2FuturesScraper
from visualize import EUA2DataVisualizer
from pathlib import Path

def main():
    # Create scraper instance
    csv_file = "eua2_futures_data.csv"
    scraper = EUA2FuturesScraper(output_file=csv_file)
    
    # Check if CSV already exists and clean it up
    csv_path = Path(csv_file)
    existing_count = 0
    if csv_path.exists():
        print("Cleaning up existing CSV file...")
        existing_count = scraper.cleanup_csv()
        if existing_count > 0:
            existing_data = scraper.load_existing_csv()
            print(f"Found existing CSV with {existing_count} clean data points")
            print(f"  Date range: {existing_data[0]['date']} to {existing_data[-1]['date']}")
    
    # Scrape data (tries multiple time spans for maximum historical data)
    print("\nScraping new data from ICE website...")
    data = scraper.scrape_data(try_multiple_spans=True)
    
    if data:
        # Save to CSV, merging with existing data
        output_file = scraper.save_to_csv(data, update_existing=True)
        
        # Load final data to show complete summary
        final_data = scraper.load_existing_csv()
        
        print(f"\n{'='*60}")
        print(f"✓ Data update complete!")
        print(f"{'='*60}")
        print(f"\nCSV file: {output_file}")
        print(f"\nSummary:")
        print(f"  New records scraped: {len(data)}")
        print(f"  Total records in CSV: {len(final_data)}")
        if final_data:
            print(f"  Date range: {final_data[0]['date']} to {final_data[-1]['date']}")
            prices = [d['price'] for d in final_data]
            print(f"  Price range: €{min(prices):.2f} - €{max(prices):.2f}")
            print(f"  Average price: €{sum(prices)/len(prices):.2f}")
        
        # Update visualization
        print(f"\n{'='*60}")
        print("Updating visualization...")
        print(f"{'='*60}")
        try:
            visualizer = EUA2DataVisualizer(csv_file=csv_file)
            visualizer.load_data()
            visualizer.create_visualization(show_plot=False)
            print("✓ Visualization updated successfully")
        except Exception as e:
            print(f"⚠ Warning: Could not update visualization: {e}")
    else:
        print("\n✗ No new data was extracted.")
        if existing_count > 0:
            print(f"  Existing CSV file unchanged ({existing_count} records)")
            # Still try to update visualization with existing data
            print("\nUpdating visualization with existing data...")
            try:
                visualizer = EUA2DataVisualizer(csv_file=csv_file)
                visualizer.load_data()
                visualizer.create_visualization(show_plot=False)
                print("✓ Visualization updated successfully")
            except Exception as e:
                print(f"⚠ Warning: Could not update visualization: {e}")
        else:
            print("  Please check the website or update the scraper.")

if __name__ == "__main__":
    main()

