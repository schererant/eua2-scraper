#!/usr/bin/env python3
"""
EUA 2 Futures Data Visualization
Creates visualizations of historical price data
"""

import csv
import ast
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Use a modern style if available
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    try:
        plt.style.use('seaborn-darkgrid')
    except:
        plt.style.use('default')

# Professional color palette
COLORS = {
    'primary': '#1a237e',      # Deep blue
    'secondary': '#3949ab',    # Medium blue
    'accent': '#5c6bc0',        # Light blue
    'gradient_start': '#283593',
    'gradient_end': '#7986cb',
    'positive': '#2e7d32',      # Green
    'negative': '#c62828',      # Red
    'neutral': '#616161',       # Gray
    'background': '#f5f5f5',
    'text': '#212121',
    'grid': '#e0e0e0'
}


class EUA2DataVisualizer:
    """Visualizer for EUA 2 Futures price data"""
    
    def __init__(self, csv_file: str = "eua2_futures_data.csv"):
        self.csv_file = csv_file
        self.data: List[Dict] = []
        
    def load_data(self) -> List[Dict]:
        """Load and parse data from CSV file"""
        data = []
        
        if not Path(self.csv_file).exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                date_str = row.get('date', '').strip()
                price_str = row.get('price', '').strip()
                
                # Skip empty rows
                if not date_str and not price_str:
                    continue
                
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
                                    date_val = item[0]
                                    price_val = item[1]
                                    # Convert to strings for parsing
                                    parsed = self._parse_date_price(str(date_val), str(price_val))
                                    if parsed:
                                        data.append(parsed)
                    except Exception as e:
                        continue
                else:
                    # Normal CSV format - skip if price looks like a market ID (very large number)
                    try:
                        price_float = float(price_str.replace(',', ''))
                        # If price is suspiciously large (like a market ID), skip this row
                        if price_float > 1000000:
                            continue
                    except:
                        pass
                    
                    parsed = self._parse_date_price(date_str, price_str)
                    if parsed:
                        data.append(parsed)
        
        # Sort by date
        data.sort(key=lambda x: x['date'])
        
        # Remove duplicates
        seen_dates = set()
        unique_data = []
        for item in data:
            date_key = item['date'].strftime('%Y-%m-%d')
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                unique_data.append(item)
        
        self.data = unique_data
        return unique_data
    
    def _parse_date_price(self, date_str: str, price_str: str) -> Optional[Dict]:
        """Parse date and price strings into a dictionary"""
        try:
            # Parse date - handle various formats
            date_obj = None
            
            # Try parsing as datetime string
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%a %b %d %H:%M:%S %Y',  # "Mon Jun 30 00:00:00 2025"
                '%Y-%m-%d %H:%M:%S',
            ]
            
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    break
                except:
                    continue
            
            if not date_obj:
                # Try to extract date from string using regex
                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
                if date_match:
                    date_obj = datetime(int(date_match.group(1)), 
                                       int(date_match.group(2)), 
                                       int(date_match.group(3)))
            
            if not date_obj:
                return None
            
            # Parse price
            try:
                price = float(price_str.replace(',', ''))
            except:
                return None
            
            return {
                'date': date_obj,
                'price': price
            }
            
        except Exception as e:
            return None
    
    def create_visualization(self, output_file: Optional[str] = None, 
                           show_plot: bool = True) -> str:
        """
        Create a professional line chart visualization
        
        Args:
            output_file: Optional path to save the plot. Default: eua2_futures_visualization.png
            show_plot: Whether to display the plot interactively
            
        Returns:
            Path to saved visualization file
        """
        if not self.data:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Set default output file (overwrites existing)
        if output_file is None:
            output_file = "eua2_futures_visualization.png"
        
        dates = [d['date'] for d in self.data]
        prices = [d['price'] for d in self.data]
        
        # Create figure with professional styling
        fig, ax = plt.subplots(figsize=(16, 8), facecolor='white')
        fig.patch.set_facecolor('white')
        ax.set_facecolor(COLORS['background'])
        
        # Calculate statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        min_idx = prices.index(min_price)
        max_idx = prices.index(max_price)
        
        # Create gradient fill
        ax.fill_between(dates, prices, alpha=0.25, color=COLORS['primary'])
        
        # Main price line with smooth appearance
        ax.plot(dates, prices, linewidth=3.5, color=COLORS['primary'], 
               label='EUA 2 Futures Price', zorder=3, antialiased=True)
        
        # Highlight min and max points
        ax.scatter([dates[min_idx]], [min_price], s=250, color=COLORS['negative'], 
                  zorder=5, edgecolors='white', linewidths=3, 
                  label=f'Minimum: €{min_price:.2f}')
        ax.scatter([dates[max_idx]], [max_price], s=250, color=COLORS['positive'], 
                  zorder=5, edgecolors='white', linewidths=3, 
                  label=f'Maximum: €{max_price:.2f}')
        
        # Add average line
        ax.axhline(y=avg_price, color=COLORS['neutral'], linestyle='--', 
                  linewidth=2.5, alpha=0.8, label=f'Average: €{avg_price:.2f}')
        
        # Professional annotations for min/max
        ax.annotate(f'€{min_price:.2f}', 
                   xy=(dates[min_idx], min_price),
                   xytext=(15, 25), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.8', facecolor=COLORS['negative'], 
                            edgecolor='white', linewidth=2, alpha=0.9),
                   arrowprops=dict(arrowstyle='->', lw=2, color=COLORS['negative']),
                   fontsize=11, fontweight='bold', color='white', zorder=6)
        
        ax.annotate(f'€{max_price:.2f}', 
                   xy=(dates[max_idx], max_price),
                   xytext=(15, -30), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.8', facecolor=COLORS['positive'], 
                            edgecolor='white', linewidth=2, alpha=0.9),
                   arrowprops=dict(arrowstyle='->', lw=2, color=COLORS['positive']),
                   fontsize=11, fontweight='bold', color='white', zorder=6)
        
        # Styling
        ax.set_title('EUA 2 Futures Historical Price Trend', 
                    fontsize=20, fontweight='bold', pad=25, color=COLORS['primary'])
        ax.set_xlabel('Date', fontsize=14, fontweight='medium', color=COLORS['text'])
        ax.set_ylabel('Price (€)', fontsize=14, fontweight='medium', color=COLORS['text'])
        ax.grid(True, alpha=0.4, color=COLORS['grid'], linestyle='-', linewidth=0.8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(COLORS['grid'])
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.tick_params(colors=COLORS['text'], labelsize=11)
        
        # Format x-axis with clearer dates
        # Use AutoDateLocator for better spacing
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=12))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=11)
        
        # Tighten y-axis range with small padding (5% of range)
        price_range = max_price - min_price
        padding = price_range * 0.05
        ax.set_ylim(min_price - padding, max_price + padding)
        
        # Professional legend
        legend = ax.legend(loc='upper left', frameon=True, fancybox=True, 
                          shadow=True, fontsize=11, framealpha=0.95, ncol=1)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_edgecolor(COLORS['grid'])
        legend.get_frame().set_linewidth(1.5)
        
        # Add summary box
        summary_text = f'Summary\n'
        summary_text += f'━━━━━━━━━━━━━━━━━━━━\n'
        summary_text += f'Period: {dates[0].strftime("%Y-%m-%d")} to {dates[-1].strftime("%Y-%m-%d")}\n'
        summary_text += f'Range: €{max_price - min_price:.2f}\n'
        summary_text += f'Records: {len(self.data)}'
        
        ax.text(0.98, 0.02, summary_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='bottom', horizontalalignment='right',
               family='monospace',
               bbox=dict(boxstyle='round,pad=1', facecolor='white', 
                        edgecolor=COLORS['primary'], linewidth=2, alpha=0.95))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"✓ Visualization saved to: {output_file}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        return output_file


def main():
    """Main function to run the visualizer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize EUA 2 Futures price data')
    parser.add_argument('--csv', '-c', default='eua2_futures_data.csv',
                       help='Path to CSV file (default: eua2_futures_data.csv)')
    parser.add_argument('--output', '-o', default=None,
                       help='Output file path (default: auto-generated)')
    parser.add_argument('--no-show', action='store_true',
                       help='Do not display plot (only save to file)')
    
    args = parser.parse_args()
    
    try:
        visualizer = EUA2DataVisualizer(csv_file=args.csv)
        print(f"Loading data from {args.csv}...")
        data = visualizer.load_data()
        
        if not data:
            print("No data found in CSV file.")
            return 1
        
        print(f"Loaded {len(data)} data points")
        print(f"Date range: {data[0]['date'].strftime('%Y-%m-%d')} to {data[-1]['date'].strftime('%Y-%m-%d')}")
        print(f"Price range: €{min(d['price'] for d in data):.2f} - €{max(d['price'] for d in data):.2f}")
        
        output_file = visualizer.create_visualization(
            output_file=args.output,
            show_plot=not args.no_show
        )
        
        print(f"\n✓ Visualization complete!")
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

