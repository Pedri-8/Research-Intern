import json
import re

def analyze_dataset(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
    # If it starts with { and ends with } but has no [ ], it might be multiple objects
    if not content.startswith('['):
        # Try to make it a valid JSON array if it's just { ... }, { ... }
        content = '[' + content + ']'
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Initial attempt failed: {e}. Trying to parse objects manually.")
        # Fallback: find all { ... } patterns (simplistic but might work for this specific file)
        # Better: split by '},\n{'
        data = []
        # This is a bit risky for complex JSON but let's try a split
        # The file content shown earlier had:
        # }
        # {
        # ...
        parts = re.split(r'}\s*,\s*\n\s*{', content[1:-1])
        for p in parts:
            try:
                # Add back the braces
                if not p.startswith('{'): p = '{' + p
                if not p.endswith('}'): p = p + '}'
                data.append(json.loads(p))
            except:
                continue

    issues = []
    conjunctions = [r'\band\b', r'\bbut\b', r'\bbecause\b', r'\bso\b', r'\band also\b']
    
    for entry in data:
        entry_issues = []
        simplified = entry.get('simplified', '')
        if not simplified: continue
        
        sentences = re.split(r'[.!?]+', simplified)
        sentences = [s.strip() for s in sentences if s.strip()]

        for i, sentence in enumerate(sentences):
            words = sentence.split()
            
            # Rule: One idea per sentence
            if len(words) > 18: 
                entry_issues.append(f"Long sentence ({len(words)} words): '{sentence[:50]}...'")
            
            # Rule: Avoid conjunctions joining long ideas
            for conj in conjunctions:
                if re.search(conj, sentence, re.IGNORECASE):
                    # Check length after conjunction
                    parts = re.split(conj, sentence, flags=re.IGNORECASE)
                    if len(parts) > 1 and len(parts[1].split()) > 5:
                        entry_issues.append(f"May be joining long ideas with '{conj.strip('\\b')}': '{sentence[:50]}...'")

            # Rule: Natural flow with 'that', 'who', 'which'
            # (Audit: Check if sentences are too 'choppy')
            if len(words) < 5 and i < len(sentences) - 1:
                # Very short sentences might be fine, but check for missed connections
                pass

        if entry_issues:
            issues.append({
                "id": entry.get('id'),
                "issues": list(set(entry_issues)),
                "original_text": entry.get('text', '')[:100],
                "simplified_text": simplified
            })
            
    return issues

if __name__ == "__main__":
    report = analyze_dataset('c:/JU Intern/rectified_1.json')
    print(f"Total problematic entries identified: {len(report)}")
    
    with open('c:/JU Intern/dataset_audit_log.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("Audit log saved to c:/JU Intern/dataset_audit_log.json")
