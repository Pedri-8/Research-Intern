"""
scrapers.py – Web data scraper

Simply pulls random web data and formats them into strict paragraph lengths.
"""

import re
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import config


def _trim_to_word_range(text: str,
                        min_w: int = config.MIN_WORDS_PER_PARA,
                        max_w: int = config.MAX_WORDS_PER_PARA) -> Optional[str]:
    """Return text trimmed to [min_w, max_w] words, or None if too short."""
    words = text.split()
    if len(words) < min_w:
        return None
    trimmed = " ".join(words[:max_w])
    # Make sure it ends with proper punctuation
    if not trimmed.endswith(('.', '!', '?', '"', "'")):
        trimmed = trimmed.rsplit(' ', 1)[0]  # drop partial last word
        trimmed = trimmed.rstrip(',;:-') + '.'
    # Re-check min length after trimming
    if len(trimmed.split()) < min_w:
        return None
    return trimmed


def _clean_text(text: str) -> str:
    """Remove citations, brackets, extra whitespace from scraped text."""
    text = re.sub(r'\[.*?\]', '', text)           # remove [1], [citation needed]
    text = re.sub(r'\{.*?\}', '', text)            # remove stray markup
    text = re.sub(r'\(.*?listen.*?\)', '', text)   # remove audio links
    text = re.sub(r'\s+', ' ', text).strip()       # collapse whitespace
    return text


def scrape_random_web(count: int) -> List[dict]:
    """
    Scrape continuously from Random Web APIs (Wikipedia) until we have 
    collecting enough text chunks that meet the precise word bounds.
    """
    results = []
    buffer = ""
    
    print(f"\n🌐 Initiating pure web scrape until {count} paragraphs collected...")
    
    while len(results) < count:
        try:
            # We use Wikipedia's "Random Page" API as our boundless generic text source
            url = "https://en.wikipedia.org/api/rest_v1/page/random/html"
            headers = {"User-Agent": config.WIKIPEDIA_USER_AGENT}
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, "lxml")
            
            # Read paragraphs and stitch them into the buffer
            for p_tag in soup.find_all('p'):
                text = _clean_text(p_tag.get_text())
                if not text:
                    continue
                
                buffer = (buffer + " " + text).strip()
                
                # If we have accumulated enough words for a paragraph
                if len(buffer.split()) >= config.MIN_WORDS_PER_PARA:
                    trimmed = _trim_to_word_range(buffer)
                    if trimmed:
                        results.append({
                            "text": trimmed,
                            "source": "Web Scrape",
                        })
                        if len(results) % 100 == 0:
                            print(f"  -> Collected {len(results)} paragraphs")
                        if len(results) >= count:
                            break
                    # Reset buffer to start accumulating the next chunk
                    buffer = ""
                    
        except Exception:
            # Drop errors (timeouts, connection drops) and keep pulling new pages
            continue

    return results
