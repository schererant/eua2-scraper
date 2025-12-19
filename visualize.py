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
        Create comprehensive professional visualization of the data
        
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
        
        # Create figure with professional styling
        fig = plt.figure(figsize=(18, 11), facecolor='white')
        fig.patch.set_facecolor('white')
        gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.25, 
                             left=0.08, right=0.95, top=0.93, bottom=0.08)
        
        dates = [d['date'] for d in self.data]
        prices = [d['price'] for d in self.data]
        
        # Calculate statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        min_date = dates[prices.index(min_price)]
        max_date = dates[prices.index(max_price)]
        price_range = max_price - min_price
        
        # 1. Main price chart with gradient fill
        ax1 = fig.add_subplot(gs[0:2, :])
        ax1.set_facecolor(COLORS['background'])
        
        # Create gradient fill
        for i in range(len(dates) - 1):
            ax1.fill_between([dates[i], dates[i+1]], 
                           [prices[i], prices[i+1]], 
                           alpha=0.4, 
                           color=COLORS['accent'])
        
        # Main price line with gradient effect
        line = ax1.plot(dates, prices, linewidth=3, color=COLORS['primary'], 
                       label='EUA 2 Futures Price', zorder=3)
        
        # Add smooth gradient fill under curve
        ax1.fill_between(dates, prices, alpha=0.2, color=COLORS['primary'])
        
        # Highlight min and max points
        ax1.scatter([min_date], [min_price], s=200, color=COLORS['negative'], 
                   zorder=5, edgecolors='white', linewidths=2, label='Minimum')
        ax1.scatter([max_date], [max_price], s=200, color=COLORS['positive'], 
                   zorder=5, edgecolors='white', linewidths=2, label='Maximum')
        
        # Add average line
        ax1.axhline(y=avg_price, color=COLORS['neutral'], linestyle='--', 
                   linewidth=2, alpha=0.7, label=f'Average: €{avg_price:.2f}')
        
        # Styling
        ax1.set_title('EUA 2 Futures Historical Price Trend', 
                     fontsize=18, fontweight='bold', pad=25, color=COLORS['text'])
        ax1.set_xlabel('Date', fontsize=13, fontweight='medium', color=COLORS['text'])
        ax1.set_ylabel('Price (€)', fontsize=13, fontweight='medium', color=COLORS['text'])
        ax1.grid(True, alpha=0.4, color=COLORS['grid'], linestyle='-', linewidth=0.8)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color(COLORS['grid'])
        ax1.spines['bottom'].set_color(COLORS['grid'])
        ax1.tick_params(colors=COLORS['text'], labelsize=10)
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
        
        # Professional legend
        legend = ax1.legend(loc='upper left', frameon=True, fancybox=True, 
                           shadow=True, fontsize=10, framealpha=0.95)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_edgecolor(COLORS['grid'])
        
        # Statistics box with modern design
        stats_text = f'Statistics\n'
        stats_text += f'━━━━━━━━━━━━━━━━━━━━\n'
        stats_text += f'Min: €{min_price:.2f}\n'
        stats_text += f'   {min_date.strftime("%Y-%m-%d")}\n\n'
        stats_text += f'Max: €{max_price:.2f}\n'
        stats_text += f'   {max_date.strftime("%Y-%m-%d")}\n\n'
        stats_text += f'Average: €{avg_price:.2f}\n'
        stats_text += f'Range: €{price_range:.2f}\n'
        stats_text += f'Records: {len(self.data)}'
        
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
                fontsize=10, verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round,pad=1', facecolor='white', 
                         edgecolor=COLORS['primary'], linewidth=2, alpha=0.95))
        
        # 2. Price distribution histogram with gradient
        ax2 = fig.add_subplot(gs[2, 0])
        ax2.set_facecolor(COLORS['background'])
        
        n, bins, patches = ax2.hist(prices, bins=25, color=COLORS['secondary'], 
                                    edgecolor='white', linewidth=1.5, alpha=0.8)
        
        # Add gradient to histogram bars
        for i, patch in enumerate(patches):
            patch.set_facecolor(plt.cm.Blues(0.3 + 0.7 * i / len(patches)))
        
        ax2.axvline(avg_price, color=COLORS['negative'], linestyle='--', 
                   linewidth=2.5, label=f'Mean: €{avg_price:.2f}', zorder=3)
        
        ax2.set_title('Price Distribution', fontsize=14, fontweight='bold', 
                     pad=15, color=COLORS['text'])
        ax2.set_xlabel('Price (€)', fontsize=11, fontweight='medium', color=COLORS['text'])
        ax2.set_ylabel('Frequency', fontsize=11, fontweight='medium', color=COLORS['text'])
        ax2.grid(True, alpha=0.3, color=COLORS['grid'], axis='y')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color(COLORS['grid'])
        ax2.spines['bottom'].set_color(COLORS['grid'])
        ax2.tick_params(colors=COLORS['text'], labelsize=9)
        ax2.legend(loc='upper right', fontsize=9, framealpha=0.9)
        
        # 3. Monthly average prices with modern bar chart
        ax3 = fig.add_subplot(gs[2, 1])
        ax3.set_facecolor(COLORS['background'])
        
        monthly_avg = self._calculate_monthly_averages()
        if monthly_avg:
            months = [m['month'] for m in monthly_avg]
            month_prices = [m['avg_price'] for m in monthly_avg]
            
            # Create gradient bars
            bars = ax3.bar(range(len(months)), month_prices, 
                          color=COLORS['accent'], edgecolor='white', 
                          linewidth=1.5, alpha=0.85)
            
            # Add gradient effect to bars
            for i, bar in enumerate(bars):
                bar.set_facecolor(plt.cm.viridis(0.2 + 0.6 * i / len(bars)))
            
            ax3.set_title('Monthly Average Prices', fontsize=14, fontweight='bold', 
                         pad=15, color=COLORS['text'])
            ax3.set_xlabel('Month', fontsize=11, fontweight='medium', color=COLORS['text'])
            ax3.set_ylabel('Average Price (€)', fontsize=11, fontweight='medium', color=COLORS['text'])
            ax3.set_xticks(range(len(months)))
            ax3.set_xticklabels([m.strftime('%b %Y') for m in months], 
                               rotation=45, ha='right', fontsize=8)
            ax3.grid(True, alpha=0.3, color=COLORS['grid'], axis='y')
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.spines['left'].set_color(COLORS['grid'])
            ax3.spines['bottom'].set_color(COLORS['grid'])
            ax3.tick_params(colors=COLORS['text'], labelsize=9)
        
        # Professional main title
        fig.suptitle('EUA 2 Futures - Comprehensive Price Analysis', 
                    fontsize=22, fontweight='bold', y=0.98, color=COLORS['primary'])
        
        # Save with high quality
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"✓ Visualization saved to: {output_file}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        return output_file
    
    def _calculate_monthly_averages(self) -> List[Dict]:
        """Calculate monthly average prices"""
        monthly_data = {}
        
        for item in self.data:
            month_key = item['date'].replace(day=1)
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(item['price'])
        
        monthly_avg = []
        for month in sorted(monthly_data.keys()):
            avg_price = sum(monthly_data[month]) / len(monthly_data[month])
            monthly_avg.append({
                'month': month,
                'avg_price': avg_price,
                'count': len(monthly_data[month])
            })
        
        return monthly_avg
    
    def create_simple_chart(self, output_file: Optional[str] = None, 
                           show_plot: bool = True) -> str:
        """
        Create a beautiful simple line chart
        
        Args:
            output_file: Optional path to save the plot. Default: eua2_futures_simple.png
            show_plot: Whether to display the plot interactively
            
        Returns:
            Path to saved visualization file
        """
        if not self.data:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Set default output file (overwrites existing)
        if output_file is None:
            output_file = "eua2_futures_simple.png"
        
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
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=10)
        
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
        print(f"✓ Simple chart saved to: {output_file}")
        
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
    parser.add_argument('--simple', '-s', action='store_true',
                       help='Create simple chart instead of comprehensive visualization')
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
        
        if args.simple:
            output_file = visualizer.create_simple_chart(
                output_file=args.output,
                show_plot=not args.no_show
            )
        else:
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

