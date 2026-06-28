"""
Configuration for dataset generation and summarization pipeline.
Adjust these values to control the output.
"""

# ─── Dataset Generation Settings ───────────────────────────────────────────────
MIN_PARAGRAPHS = 2000         # Minimum number of paragraphs to generate
MAX_PARAGRAPHS = 5000          # Maximum number of paragraphs to generate
TARGET_PARAGRAPHS = 5000       # Default target (used if not randomized)
RANDOMIZE_COUNT = False         # If True, picks a random count between MIN and MAX

MIN_WORDS_PER_PARA = 450      # Minimum words per paragraph
MAX_WORDS_PER_PARA = 650      # Maximum words per paragraph

# ─── Scraping Settings ─────────────────────────────────────────────────────────
WIKIPEDIA_USER_AGENT = "DatasetGenerator/2.0 (research-project)"

# ─── Summarization Settings ───────────────────────────────────────────────────
# Options: "transformers" (uses T5-small) or "sumy" (extractive, lightweight)
SUMMARIZER_BACKEND = "transformers"

# Transformer model for summarization (only used if backend = "transformers")
SUMMARIZER_MODEL = "t5-small"

# Target summary length (in words, approximate)
SUMMARY_MIN_WORDS = 120
SUMMARY_MAX_WORDS = 150

# ─── Output Settings ──────────────────────────────────────────────────────────
OUTPUT_DIR = "output"
SAVE_JSON = True
SAVE_CSV = True
DATASET_FILENAME = "dataset"            # will get .json / .csv appended
SUMMARY_FILENAME = "summarized_dataset"  # will get .json / .csv appended

# ─── Misc ─────────────────────────────────────────────────────────────────────
RANDOM_SEED = None   # Set to an integer for reproducibility; None = truly random
BATCH_SIZE = 16      # Batch size for transformer summarization
