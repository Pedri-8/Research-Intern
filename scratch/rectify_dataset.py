import json
import re

def rectify_simplified_text(text):
    """
    Applies strict simplification rules to rectify common errors:
    1. Splits sentences joined by 'and', 'but', 'because', 'so' if they are long.
    2. Ensures one idea per sentence.
    3. Prefers 'This was because' or 'This means' over starters like 'So' or 'Because'.
    """
    # 1. Handle "and" joining long clauses
    # Heuristic: if 'and' is followed by a verb-like structure or > 4 words
    text = re.sub(r'(\w+),?\s+and\s+(\w+)', lambda m: f"{m.group(1)}. {m.group(2)}" if len(m.group(0).split()) > 10 else m.group(0), text)
    
    # 2. Handle "but"
    text = re.sub(r',\s+but\s+', '. But ', text)
    
    # 3. Handle "because"
    # "A because B" -> "A. This was because B."
    text = re.sub(r'(\w+)\s+because\s+(\w+)', r'\1. This was because \2', text)
    
    # 4. Handle "so"
    # "A, so B." -> "A. This means B." or "A. So B."
    text = re.sub(r',\s+so\s+', '. This means ', text)
    
    # 5. Clean up "So," at the start of sentences
    text = re.sub(r'\bSo,\s+', 'This means ', text)
    
    # 6. Clean up "But " at start if it joins a long idea
    # (Optional, but often better to just state the point)
    
    # 7. Split sentences longer than 15 words if they have and/or/but/which
    sentences = re.split(r'([.!?])\s*', text)
    new_sentences = []
    
    i = 0
    while i < len(sentences):
        s = sentences[i]
        punct = sentences[i+1] if i+1 < len(sentences) else ""
        i += 2
        
        words = s.split()
        if len(words) > 15:
            # Try to split on common conjunctions
            sub_parts = re.split(r'\s+(and|which|who|where|but)\s+', s, flags=re.IGNORECASE)
            if len(sub_parts) > 1:
                # Reconstruct with periods
                refined = ""
                for j, part in enumerate(sub_parts):
                    if j % 2 == 0:
                        refined += part
                    else:
                        refined += ". " + part.capitalize() + " "
                new_sentences.append(refined.strip())
            else:
                new_sentences.append(s)
        else:
            new_sentences.append(s)
        
        if punct and new_sentences:
             new_sentences[-1] += punct

    final_text = " ".join(new_sentences)
    # Clean up double periods or spaces
    final_text = re.sub(r'\.\s*\.', '.', final_text)
    final_text = re.sub(r'\s+', ' ', final_text).strip()
    
    return final_text

def process_dataset(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Normalize to array
    if not content.startswith('['):
        content = '[' + content + ']'
    
    try:
        data = json.loads(content)
    except:
        # Fallback manual parse if needed
        data = []
        parts = re.split(r'}\s*,\s*\n\s*{', content[1:-1])
        for p in parts:
            try:
                if not p.startswith('{'): p = '{' + p
                if not p.endswith('}'): p = p + '}'
                data.append(json.loads(p))
            except: continue

    rectified_count = 0
    for entry in data:
        original_sim = entry.get('simplified', '')
        new_sim = rectify_simplified_text(original_sim)
        if new_sim != original_sim:
            entry['simplified'] = new_sim
            rectified_count += 1
            entry['rectified'] = True
        else:
            entry['rectified'] = False

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    return rectified_count, len(data)

if __name__ == "__main__":
    count, total = process_dataset('c:/JU Intern/simplified_1.json', 'c:/JU Intern/rectified_1.json')
    print(f"Rectified {count} out of {total} entries.")
    print("Saved to c:/JU Intern/rectified_1.json")
