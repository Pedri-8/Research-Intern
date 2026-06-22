"""
summarizer.py – Paragraph summarization with simplified vocabulary.

Supports two backends:
  1. "transformers" – Uses T5-small (or configurable model) for abstractive
     summarization with simple language.
  2. "sumy" – Uses LSA-based extractive summarization (lightweight, no GPU).
"""

import re
from typing import List

import config


def _simplify_text(text: str) -> str:
    """
    Post-process summarized text to ensure simple vocabulary and structure.
    - Splits overly long sentences.
    - Removes parenthetical asides.
    - Cleans up punctuation artifacts.
    """
    # Remove parenthetical content
    text = re.sub(r'\(.*?\)', '', text)
    # Remove quotes within the text for clarity
    text = text.replace('"', '').replace("'s", " is").replace("'re", " are")
    text = text.replace("'ve", " have").replace("'ll", " will")
    text = text.replace("n't", " not")
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Ensure it ends with a period
    if text and not text.endswith(('.', '!', '?')):
        text += '.'
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Transformers Backend
# ──────────────────────────────────────────────────────────────────────────────

_transformer_model = None
_transformer_tokenizer = None
_transformer_device = None


def _load_transformer_model():
    """Lazy-load the transformer model and tokenizer manually."""
    global _transformer_model, _transformer_tokenizer, _transformer_device
    if _transformer_model is None:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        
        _transformer_device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        
        print(f"  Loading summarization model: {config.SUMMARIZER_MODEL} (Device: {str(_transformer_device).upper()}) ...")
        
        _transformer_tokenizer = AutoTokenizer.from_pretrained(config.SUMMARIZER_MODEL, legacy=False)
        _transformer_model = AutoModelForSeq2SeqLM.from_pretrained(config.SUMMARIZER_MODEL).to(_transformer_device)
        
        print("  Model loaded successfully.")
    return _transformer_model, _transformer_tokenizer, _transformer_device


def _summarize_transformers_batch(texts: List[str]) -> List[str]:
    """Summarize a batch of texts using manual model generation."""
    model, tokenizer, device = _load_transformer_model()
    
    # T5 requires a prefix
    model_name = config.SUMMARIZER_MODEL.lower()
    if "t5" in model_name:
        prefixed = [f"summarize: {t}" for t in texts]
    else:
        prefixed = texts
    
    # Tokenize in batch
    inputs = tokenizer(
        prefixed,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    ).to(device)
    
    # Generate summaries
    summary_ids = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=config.SUMMARY_MAX_WORDS * 2, # rough conversion for tokens
        min_length=config.SUMMARY_MIN_WORDS,
        do_sample=False,
    )
    
    # Decode and clean
    summaries = []
    for output_id in summary_ids:
        text_out = tokenizer.decode(output_id, skip_special_tokens=True)
        summaries.append(_simplify_text(text_out))
        
    return summaries


def summarize_transformers(paragraphs: List[str],
                           batch_size: int = config.BATCH_SIZE) -> List[str]:
    """Summarize a list of paragraphs using transformers, in batches."""
    results = []
    for i in range(0, len(paragraphs), batch_size):
        batch = paragraphs[i:i + batch_size]
        results.extend(_summarize_transformers_batch(batch))
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Sumy Backend (lightweight extractive summarization)
# ──────────────────────────────────────────────────────────────────────────────

def _summarize_sumy_single(text: str) -> str:
    """Summarize a single text using Sumy's LSA algorithm."""
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.nlp.stemmers import Stemmer
    from sumy.utils import get_stop_words
    
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    stemmer = Stemmer("english")
    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = get_stop_words("english")
    
    # Determine number of sentences for target word count
    sentences = list(parser.document.sentences)
    if len(sentences) <= 2:
        summary_count = 1
    else:
        summary_count = max(1, len(sentences) // 3)
    
    summary_sentences = summarizer(parser.document, summary_count)
    summary = " ".join(str(s) for s in summary_sentences)
    
    return _simplify_text(summary)


def summarize_sumy(paragraphs: List[str]) -> List[str]:
    """Summarize a list of paragraphs using Sumy."""
    return [_summarize_sumy_single(p) for p in paragraphs]


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def summarize(paragraphs: List[str]) -> List[str]:
    """
    Summarize paragraphs using the backend specified in config.
    Returns a list of simplified summaries, one per input paragraph.
    """
    backend = config.SUMMARIZER_BACKEND.lower()
    
    if backend == "transformers":
        return summarize_transformers(paragraphs)
    elif backend == "sumy":
        return summarize_sumy(paragraphs)
    else:
        raise ValueError(
            f"Unknown summarizer backend: '{backend}'. "
            f"Use 'transformers' or 'sumy'."
        )
