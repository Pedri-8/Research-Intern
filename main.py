"""
main.py - Dataset Generation & Summarization Pipeline

Orchestrates the full workflow:
  1. Determine how many paragraphs to generate.
  2. Stream purely randomized web data until the count is met.
  3. Summarize every paragraph into simple, clear language.
  4. Save both the raw dataset and summarized dataset to JSON & CSV.

Usage:
  python main.py                        # uses defaults from config.py
  python main.py --count 2500           # override paragraph count
  python main.py --backend sumy         # use lightweight summarizer
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime
from typing import List

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from tqdm import tqdm

import config
from scrapers import scrape_random_web
from summarizer import summarize


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a simple randomized web dataset and summarize it."
    )
    parser.add_argument(
        "--count", type=int, default=None,
        help=f"Total paragraphs to generate (default: random between "
             f"{config.MIN_PARAGRAPHS}-{config.MAX_PARAGRAPHS})"
    )
    parser.add_argument(
        "--backend", type=str, default=None,
        choices=["transformers", "sumy"],
        help=f"Summarizer backend (default: {config.SUMMARIZER_BACKEND})"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help=f"Output directory (default: {config.OUTPUT_DIR})"
    )
    return parser.parse_args()


def determine_paragraph_count(override: int = None) -> int:
    """Decide how many paragraphs to generate."""
    if override:
        return override
    if config.RANDOMIZE_COUNT:
        return random.randint(config.MIN_PARAGRAPHS, config.MAX_PARAGRAPHS)
    return config.TARGET_PARAGRAPHS


def run_summarization(texts: List[str]) -> List[dict]:
    """
    Summarize all paragraphs and return enriched records with summaries.
    """
    print(f"\n[SUM] Summarizing {len(texts)} paragraphs "
          f"(backend: {config.SUMMARIZER_BACKEND})...")
    
    batch_size = config.BATCH_SIZE
    summaries = []
    
    for i in tqdm(range(0, len(texts), batch_size),
                  desc="Summarizing", unit="batch"):
        batch = texts[i:i + batch_size]
        batch_summaries = summarize(batch)
        summaries.extend(batch_summaries)
    
    # Merge summaries back into paragraph records
    enriched = []
    for para, summary in zip(texts, summaries):
        enriched.append({
            "id": len(enriched) + 1,
            "source": "Web Scrape",
            "original_text": para,
            "original_word_count": len(para.split()),
            "summary": summary,
            "summary_word_count": len(summary.split()),
        })
    
    return enriched


def save_dataset(data: List[dict], filename: str, output_dir: str):
    """Save dataset to JSON and/or CSV based on config."""
    os.makedirs(output_dir, exist_ok=True)
    
    if config.SAVE_JSON:
        json_path = os.path.join(output_dir, f"{filename}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"   [SAVE] JSON: {json_path} ({len(data)} records)")
    
    if config.SAVE_CSV:
        csv_path = os.path.join(output_dir, f"{filename}.csv")
        if data:
            keys = data[0].keys()
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
            print(f"   [SAVE] CSV:  {csv_path} ({len(data)} records)")


def print_stats(data: List[dict]):
    """Print a summary of the generated dataset."""
    print("\n" + "=" * 65)
    print("  DATASET STATISTICS")
    print("=" * 65)
    print(f"  Total paragraphs: {len(data)}")
    
    # Word count stats
    orig_counts = [item["original_word_count"] for item in data]
    summ_counts = [item["summary_word_count"] for item in data]
    
    print(f"\n  Original Text:")
    print(f"    Avg words: {sum(orig_counts)/len(orig_counts):.1f}")
    print(f"    Min words: {min(orig_counts)}")
    print(f"    Max words: {max(orig_counts)}")
    
    print(f"\n  Summaries:")
    print(f"    Avg words: {sum(summ_counts)/len(summ_counts):.1f}")
    print(f"    Min words: {min(summ_counts)}")
    print(f"    Max words: {max(summ_counts)}")
    
    compression = (1 - sum(summ_counts) / sum(orig_counts)) * 100
    print(f"\n  Compression ratio: {compression:.1f}%")
    print("=" * 65)


def main():
    args = parse_args()
    
    # Apply overrides
    if args.backend:
        config.SUMMARIZER_BACKEND = args.backend
    if args.seed is not None:
        config.RANDOM_SEED = args.seed
    
    output_dir = args.output_dir or config.OUTPUT_DIR
    
    if config.RANDOM_SEED is not None:
        random.seed(config.RANDOM_SEED)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 65)
    print("  SIMPLIFIED WEB SCRAPING & SUMMARIZATION PIPELINE")
    print("=" * 65)
    print(f"  Timestamp:  {timestamp}")
    print(f"  Backend:    {config.SUMMARIZER_BACKEND}")
    print(f"  Output dir: {output_dir}")
    
    total = determine_paragraph_count(args.count)
    print(f"  Target:     {total} continuous paragraphs")
    
    # Collect purely random paragraphs
    start_time = time.time()
    paragraphs_dict = scrape_random_web(total)
    
    # Extract plain text string array for the summarizer
    texts = [p["text"] for p in paragraphs_dict]
    
    collect_time = time.time() - start_time
    print(f"\n[OK] Collected {len(texts)} pure web paragraphs in {collect_time:.1f}s")
    
    # Step 4: Save raw dataset
    raw_dataset = [
        {
            "id": i + 1,
            "source": paragraphs_dict[i]["source"],
            "text": text,
            "word_count": len(text.split()),
        }
        for i, text in enumerate(texts)
    ]
    
    print(f"\n[FILE] Saving raw dataset...")
    save_dataset(raw_dataset, f"{config.DATASET_FILENAME}_{timestamp}", output_dir)
    
    # Step 5: Summarize
    sum_start = time.time()
    enriched = run_summarization(texts)
    sum_time = time.time() - sum_start
    print(f"\n[OK] Summarization completed in {sum_time:.1f}s")
    
    # Step 6: Save summarized dataset
    print(f"\n[FILE] Saving summarized dataset...")
    save_dataset(enriched, f"{config.SUMMARY_FILENAME}_{timestamp}", output_dir)
    
    # Step 7: Print statistics
    print_stats(enriched)
    
    total_time = time.time() - start_time
    print(f"\n  Total pipeline time: {total_time:.1f}s")
    print(f"  Done! Check '{output_dir}/' for your files.\n")


if __name__ == "__main__":
    main()
