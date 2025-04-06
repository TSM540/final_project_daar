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
output_dir = 'final_thresholds'  # Changed output directory

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
            output_file = os.path.join(output_dir, f"{options['output']}_results.json")
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            self.stdout.write(f"Results saved to {output_file}")
        else:
            # Load results from JSON file
            input_file = os.path.join(output_dir, f"{options['output']}_results.json")
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
        
        # Generate only the combined line chart
        self._plot_combined_line_chart(
            results, fr_avg, en_avg, fr_thresholds, en_thresholds,
            f"{output_prefix}_combined_line.png"
        )
    
    def _plot_combined_line_chart(self, results, fr_avg, en_avg, fr_thresholds, en_thresholds, output_file):
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
        
        # 2. Average keywords per book - ENGLISH ONLY (top right)
        axs[0, 1].plot(en_thresholds, [en_avg[t] for t in en_thresholds], 'r-o', label='English')
        axs[0, 1].set_title('Average Keywords per Book (English Only)')
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
        self.stdout.write(f"Saved combined plot to {os.path.join(output_dir, output_file)}")
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