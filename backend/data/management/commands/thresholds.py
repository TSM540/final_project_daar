from django.core.management.base import BaseCommand
from data.models import Book
import os
import json
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
from matplotlib.ticker import FuncFormatter

fr_thresholds = list(range(0, 16, 5))  # 0, 5, 10, 15
en_thresholds = list(range(0, 31, 5))  # 0, 5, 10, 15, 20, 25, 30
output_dir='thresholds'
class Command(BaseCommand):
    help = 'Analyze keywords across multiple thresholds and plot token counts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--plot-only',
            action='store_true',
            help='Only generate plots from cached data',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='keyword_analysis',
            help='Output prefix for generated files',
        )
    
    def handle(self, *args, **options):
        dossier_occu = 'keywords'
        
        # Define thresholds to test
       
        
        # Store results here - use integers as keys consistently
        results = {
            'fr': {threshold: 0 for threshold in fr_thresholds},
            'en': {threshold: 0 for threshold in en_thresholds},
            'book_counts': {'fr': 0, 'en': 0},
            'keywords_per_book': {'fr': {}, 'en': {}}
        }
        
        if not options['plot_only']:
            # Get list of files first, then use tqdm to show progress
            files = os.listdir(dossier_occu)
            self.stdout.write(f"Processing {len(files)} keyword files...")
            
            # First pass: count books per language
            for nom_fichier in tqdm(files, desc="Counting books per language"):
                pk = int(nom_fichier.split('.')[0])
                book = Book.objects.get(pk=pk)
                book_language_code = book.languages.all()[0].code
                if book_language_code in ('fr', 'en'):
                    results['book_counts'][book_language_code] += 1
            
            # Second pass: analyze keywords across thresholds
            for nom_fichier in tqdm(files, desc="Analyzing keywords across thresholds"):
                chemin_fichier = os.path.join(dossier_occu, nom_fichier)
                pk = int(nom_fichier.split('.')[0])
                with open(chemin_fichier, 'r') as f:
                    keywords_book = json.load(f)
                book = Book.objects.get(pk=pk)
                book_language_code = book.languages.all()[0].code
                
                if book_language_code not in ('fr', 'en'):
                    continue
                
                # Count keywords that meet each threshold for this book
                book_id = book.pk
                
                # Initialize book data if it doesn't exist
                if book_id not in results['keywords_per_book'][book_language_code]:
                    results['keywords_per_book'][book_language_code][book_id] = {}
                
                # Get thresholds for this language
                thresholds = fr_thresholds if book_language_code == 'fr' else en_thresholds
                
                for threshold in thresholds:
                    valid_keywords_count = sum(1 for occ in keywords_book.values() if occ >= threshold)
                    results['keywords_per_book'][book_language_code][book_id][threshold] = valid_keywords_count
            
            # Compile total keyword counts for each threshold
            for lang in ['fr', 'en']:
                thresholds = fr_thresholds if lang == 'fr' else en_thresholds
                for threshold in thresholds:
                    total_keywords = sum(book_data.get(threshold, 0) for book_data in results['keywords_per_book'][lang].values())
                    results[lang][threshold] = total_keywords
            
            # Save results to a JSON file
           
            os.makedirs(output_dir, exist_ok=True)
            # output_file = f"{options['output']}_results.json"
            output_file = os.path.join(output_dir, f"{options['output']}_results.json")
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            self.stdout.write(f"Results saved to {output_file}")
        else:
            # Load results from JSON file
            input_file = f"{options['output']}_results.json"
            with open(input_file, 'r') as f:
                results = json.load(f)
                
                # Convert string keys back to integers if needed
                for lang in ['fr', 'en']:
                    results[lang] = {int(k): v for k, v in results[lang].items()}
                    for book_id in results['keywords_per_book'][lang]:
                        results['keywords_per_book'][lang][book_id] = {
                            int(k): v for k, v in results['keywords_per_book'][lang][book_id].items()
                        }
                        
            self.stdout.write(f"Loaded results from {input_file}")
        
        # Generate plots
        self._generate_plots(results, options['output'])
        
        # Display summary
        self._display_summary(results)
    
    def _generate_plots(self, results, output_prefix):
        # Calculate averages per book
        fr_avg = {}
        en_avg = {}
        
        for threshold in sorted(results['fr'].keys()):
            if results['book_counts']['fr'] > 0:
                fr_avg[threshold] = sum(book_data.get(threshold, 0) for book_data in results['keywords_per_book']['fr'].values()) / results['book_counts']['fr']
            else:
                fr_avg[threshold] = 0
                
        for threshold in sorted(results['en'].keys()):
            if results['book_counts']['en'] > 0:
                en_avg[threshold] = sum(book_data.get(threshold, 0) for book_data in results['keywords_per_book']['en'].values()) / results['book_counts']['en']
            else:
                en_avg[threshold] = 0
        
        # Calculate reduction percentages
        fr_base = results['fr'].get(0, 0)
        en_base = results['en'].get(0, 0)
        
        fr_pct = {t: 100 - (results['fr'][t] / fr_base * 100) if fr_base > 0 else 0 for t in results['fr']}
        en_pct = {t: 100 - (results['en'][t] / en_base * 100) if en_base > 0 else 0 for t in results['en']}
        
        # 1. Bar charts for total tokens by threshold (separate for each language)
        self._plot_bar_chart(
            results['fr'], 
            'French Keywords by Threshold', 
            'Threshold', 
            'Total Keywords',
            'blue',
            f"{output_prefix}_fr_total_bar.png",
            annotations=[f"{v:,} tokens" for v in results['fr'].values()]
        )
        
        self._plot_bar_chart(
            results['en'], 
            'English Keywords by Threshold', 
            'Threshold', 
            'Total Keywords',
            'red',
            f"{output_prefix}_en_total_bar.png",
            annotations=[f"{v:,} tokens" for v in results['en'].values()]
        )
        
        # 2. Bar charts for average tokens per book
        self._plot_bar_chart(
            fr_avg, 
            'French Keywords per Book by Threshold', 
            'Threshold', 
            'Average Keywords per Book',
            'blue',
            f"{output_prefix}_fr_avg_bar.png",
            annotations=[f"{v:.1f} tokens/book" for v in fr_avg.values()]
        )
        
        self._plot_bar_chart(
            en_avg, 
            'English Keywords per Book by Threshold', 
            'Threshold', 
            'Average Keywords per Book',
            'red',
            f"{output_prefix}_en_avg_bar.png",
            annotations=[f"{v:.1f} tokens/book" for v in en_avg.values()]
        )
        
        # 3. Bar charts for reduction percentage
        self._plot_bar_chart(
            {k: v for k, v in fr_pct.items() if k > 0},  # Skip threshold 0
            'French Keywords Reduction (vs Threshold 0)', 
            'Threshold', 
            'Reduction Percentage (%)',
            'blue',
            f"{output_prefix}_fr_reduction_bar.png",
            annotations=[f"{v:.1f}% reduction" for k, v in fr_pct.items() if k > 0]
        )
        
        self._plot_bar_chart(
            {k: v for k, v in en_pct.items() if k > 0},  # Skip threshold 0
            'English Keywords Reduction (vs Threshold 0)', 
            'Threshold', 
            'Reduction Percentage (%)',
            'red',
            f"{output_prefix}_en_reduction_bar.png",
            annotations=[f"{v:.1f}% reduction" for k, v in en_pct.items() if k > 0]
        )
        
        # 4. Boxplots (separate for each language)
        self._plot_boxplot(
            results, 'fr', fr_thresholds,
            'French Keywords Distribution by Threshold',
            'blue',
            f"{output_prefix}_fr_boxplot.png"
        )
        
        self._plot_boxplot(
            results, 'en', en_thresholds,
            'English Keywords Distribution by Threshold',
            'red',
            f"{output_prefix}_en_boxplot.png"
        )
        
        # 5. Combined line chart for easy comparison
        self._plot_combined_line_chart(
            results, fr_avg, en_avg, fr_thresholds, en_thresholds,
            f"{output_prefix}_combined_line.png"
        )
            
    def _plot_bar_chart(self, data, title, xlabel, ylabel, color, output_file, annotations=None):
        plt.figure(figsize=(10, 6))
        
        x = list(data.keys())
        y = list(data.values())
        
        bars = plt.bar(x, y, color=color, alpha=0.7, width=0.6)
        
        # Add labels to each bar
        if annotations:
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + (max(y) * 0.01),  # Small offset above the bar
                    annotations[i],
                    ha='center', va='bottom', rotation=0, fontsize=9
                )
        
        # Add threshold descriptions below the x-axis
        for i, threshold in enumerate(x):
            if threshold == 0:
                desc = "No filtering"
            else:
                desc = f"Min {threshold} occurrences"
                
            plt.text(
                i, 
                -max(y) * 0.05,  # Position below the x-axis
                desc,
                ha='center', va='top', rotation=0, fontsize=8
            )
        
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Add some space at the bottom for threshold descriptions
        plt.subplots_adjust(bottom=0.15)
        
        plt.savefig(os.path.join(output_dir, output_file))
        self.stdout.write(f"Saved plot to {output_file}")
        plt.close()
    
    def _plot_boxplot(self, results, lang, thresholds, title, color, output_file):
        plt.figure(figsize=(12, 6))
        
        data = []
        labels = []
        
        for threshold in thresholds:
            values = [book_data.get(threshold, 0) for book_data in results['keywords_per_book'][lang].values()]
            if values:
                data.append(values)
                
                # Calculate average for this threshold
                avg = sum(values) / len(values) if values else 0
                labels.append(f"Threshold {threshold}\n(avg: {avg:.1f})")
        
        box = plt.boxplot(data, labels=labels, patch_artist=True)
        
        # Color the boxes
        for patch in box['boxes']:
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        # Add average values as text annotations
        for i, d in enumerate(data):
            avg = sum(d) / len(d) if d else 0
            plt.text(
                i + 1, 
                max([max(d) for d in data if d]) * 0.9,  # Position at 90% of max height
                f"Average: {avg:.1f}\nBooks: {len(d)}",
                ha='center', va='top', fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
            )
        
        plt.title(title)
        plt.ylabel(f"Keywords per Book")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        plt.savefig(os.path.join(output_dir, output_file))
        self.stdout.write(f"Saved plot to {output_file}")
        plt.close()

    def _plot_combined_line_chart(self, results, fr_avg, en_avg, fr_thresholds, en_thresholds, output_file):
        plt.figure(figsize=(12, 8))
        
        # Create 2x2 subplot
        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Total keywords count (top left)
        axs[0, 0].plot(fr_thresholds, [results['fr'][t] for t in fr_thresholds], 'b-o', label='French')
        axs[0, 0].plot(en_thresholds, [results['en'][t] for t in en_thresholds], 'r-o', label='English')
        axs[0, 0].set_title('Total Keywords by Threshold')
        axs[0, 0].set_xlabel('Occurrence Threshold')
        axs[0, 0].set_ylabel('Number of Keywords')
        axs[0, 0].grid(True, linestyle='--', alpha=0.7)
        axs[0, 0].legend()
        
        # Format y-axis with commas for thousands
        axs[0, 0].get_yaxis().set_major_formatter(
            FuncFormatter(lambda x, p: format(int(x), ','))
        )
        
        # 2. Average keywords per book (top right)
        axs[0, 1].plot(fr_thresholds, [fr_avg[t] for t in fr_thresholds], 'b-o', label='French')
        axs[0, 1].plot(en_thresholds, [en_avg[t] for t in en_thresholds], 'r-o', label='English')
        axs[0, 1].set_title('Average Keywords per Book')
        axs[0, 1].set_xlabel('Occurrence Threshold')
        axs[0, 1].set_ylabel('Keywords per Book')
        axs[0, 1].grid(True, linestyle='--', alpha=0.7)
        axs[0, 1].legend()
        
        # 3. Percentage reduction (bottom left)
        fr_base = results['fr'].get(0, 0)
        en_base = results['en'].get(0, 0)
        
        fr_pct = [100 - (results['fr'][t] / fr_base * 100) if fr_base > 0 else 0 for t in fr_thresholds if t > 0]
        en_pct = [100 - (results['en'][t] / en_base * 100) if en_base > 0 else 0 for t in en_thresholds if t > 0]
        
        axs[1, 0].plot(fr_thresholds[1:], fr_pct, 'b-o', label='French')
        axs[1, 0].plot(en_thresholds[1:], en_pct, 'r-o', label='English')
        axs[1, 0].set_title('Percentage Reduction vs Baseline (Threshold 0)')
        axs[1, 0].set_xlabel('Occurrence Threshold')
        axs[1, 0].set_ylabel('Reduction Percentage (%)')
        axs[1, 0].grid(True, linestyle='--', alpha=0.7)
        axs[1, 0].legend()
        
        # 4. Total keywords with logarithmic scale (bottom right)
        axs[1, 1].plot(fr_thresholds, [results['fr'][t] for t in fr_thresholds], 'b-o', label='French')
        axs[1, 1].plot(en_thresholds, [results['en'][t] for t in en_thresholds], 'r-o', label='English')
        axs[1, 1].set_title('Total Keywords (Log Scale)')
        axs[1, 1].set_xlabel('Occurrence Threshold')
        axs[1, 1].set_ylabel('Number of Keywords')
        axs[1, 1].set_yscale('log')
        axs[1, 1].grid(True, linestyle='--', alpha=0.7)
        axs[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, output_file))
        self.stdout.write(f"Saved combined plot to {output_file}")
        plt.close()
    
    def _display_summary(self, results):
        fr_base = results['fr'].get(0, 0)
        en_base = results['en'].get(0, 0)
        
        # Calculate total stats for the final summary
        max_fr_threshold = max(results['fr'].keys())
        max_en_threshold = max(results['en'].keys())
        
        fr_final_count = results['fr'][max_fr_threshold]
        en_final_count = results['en'][max_en_threshold]
        
        fr_reduction = 100 - (fr_final_count / fr_base * 100) if fr_base > 0 else 0
        en_reduction = 100 - (en_final_count / en_base * 100) if en_base > 0 else 0
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("                 KEYWORD ANALYSIS SUMMARY                 ")
        self.stdout.write("="*60)
        
        self.stdout.write(f"\nDATASET STATISTICS:")
        self.stdout.write(f"  - Total French books: {results['book_counts']['fr']}")
        self.stdout.write(f"  - Total English books: {results['book_counts']['en']}")
        
        self.stdout.write(f"\nFRENCH KEYWORDS ANALYSIS:")
        self.stdout.write(f"  - Initial keyword count (threshold 0): {fr_base:,} tokens")
        self.stdout.write(f"  - Final keyword count (threshold {max_fr_threshold}): {fr_final_count:,} tokens")
        self.stdout.write(f"  - Total reduction: {fr_reduction:.2f}%")
        
        self.stdout.write(f"\nENGLISH KEYWORDS ANALYSIS:")
        self.stdout.write(f"  - Initial keyword count (threshold 0): {en_base:,} tokens")
        self.stdout.write(f"  - Final keyword count (threshold {max_en_threshold}): {en_final_count:,} tokens")
        self.stdout.write(f"  - Total reduction: {en_reduction:.2f}%")
        
        self.stdout.write(f"\nDETAILED THRESHOLD ANALYSIS:")
        
        # French detailed analysis
        self.stdout.write(f"\n  FRENCH KEYWORDS BY THRESHOLD:")
        for threshold in sorted(results['fr'].keys()):
            token_count = results['fr'][threshold]
            avg_per_book = token_count / results['book_counts']['fr'] if results['book_counts']['fr'] > 0 else 0
            pct_reduction = 100 - (token_count / fr_base * 100) if fr_base > 0 and threshold > 0 else 0
            
            self.stdout.write(f"  [Threshold {threshold}]: {token_count:,} tokens | {avg_per_book:.1f} tokens/book" + 
                         (f" | {pct_reduction:.2f}% reduction" if threshold > 0 else ""))
        
        # English detailed analysis
        self.stdout.write(f"\n  ENGLISH KEYWORDS BY THRESHOLD:")
        for threshold in sorted(results['en'].keys()):
            token_count = results['en'][threshold]
            avg_per_book = token_count / results['book_counts']['en'] if results['book_counts']['en'] > 0 else 0
            pct_reduction = 100 - (token_count / en_base * 100) if en_base > 0 and threshold > 0 else 0
            
            self.stdout.write(f"  [Threshold {threshold}]: {token_count:,} tokens | {avg_per_book:.1f} tokens/book" + 
                         (f" | {pct_reduction:.2f}% reduction" if threshold > 0 else ""))
        
        self.stdout.write("\n" + "="*60)
        
        # Recommendation based on the analysis
        fr_rec_threshold = self._find_optimal_threshold(results['fr'], fr_base)
        en_rec_threshold = self._find_optimal_threshold(results['en'], en_base)
        
        self.stdout.write("\nRECOMMENDATION:")
        self.stdout.write(f"  - Recommended French threshold: {fr_rec_threshold}")
        fr_rec_count = results['fr'][fr_rec_threshold]
        fr_rec_reduction = 100 - (fr_rec_count / fr_base * 100) if fr_base > 0 else 0
        self.stdout.write(f"    This reduces the keyword count from {fr_base:,} to {fr_rec_count:,} ({fr_rec_reduction:.2f}% reduction)")
        
        self.stdout.write(f"  - Recommended English threshold: {en_rec_threshold}")
        en_rec_count = results['en'][en_rec_threshold]
        en_rec_reduction = 100 - (en_rec_count / en_base * 100) if en_base > 0 else 0
        self.stdout.write(f"    This reduces the keyword count from {en_base:,} to {en_rec_count:,} ({en_rec_reduction:.2f}% reduction)")
        
        self.stdout.write("\n" + "="*60)
    
    def _find_optimal_threshold(self, threshold_data, base_count):
        """Find the threshold with the best tradeoff between reduction and retention."""
        if base_count == 0:
            return max(threshold_data.keys())
            
        # Calculate the rate of token reduction for each threshold
        # Looking for an "elbow point" where further increases in threshold don't yield as much benefit
        prev_count = base_count
        prev_threshold = 0
        best_score = 0
        best_threshold = 0
        
        for threshold in sorted(threshold_data.keys()):
            if threshold == 0:
                continue
                
            count = threshold_data[threshold]
            reduction = prev_count - count
            reduction_pct = (reduction / prev_count) * 100 if prev_count > 0 else 0
            
            # Score based on:
            # - Higher score for greater absolute reduction per threshold increase
            # - But also considering diminishing returns
            threshold_increase = threshold - prev_threshold
            score = reduction / (threshold_increase * 10) if threshold_increase > 0 else 0
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
                
            prev_count = count
            prev_threshold = threshold
            
        return best_threshold