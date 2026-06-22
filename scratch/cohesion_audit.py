import json
import re

def is_fragment(sentence):
    sentence = sentence.strip()
    if not sentence:
        return False
    
    # 1. Check for missing end punctuation
    if not sentence[-1] in ".!?\"'":
        return True
    
    # 2. Check for sentences ending in conjunctions or prepositions
    trailing_words = ['and', 'but', 'or', 'because', 'with', 'from', 'to', 'for', 'after', 'before']
    last_word = re.sub(r'[^\w\s]', '', sentence.split()[-1].lower()) if sentence.split() else ""
    if last_word in trailing_words:
        return True
    
    # 3. Check for typical fragment starters that often imply a missing main clause
    # (Simplified check: if the whole entry is just one "Before..." sentence)
    starters = ['Before', 'After', 'Because', 'While', 'Although', 'Since']
    for starter in starters:
        if sentence.startswith(starter) and ',' not in sentence and len(sentence.split()) < 10:
             # Very likely a dangling subordinate clause
             return True
             
    return False

def audit_cohesion(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cohesion_issues = []
    
    for entry in data:
        simplified = entry.get('simplified', '')
        original = entry.get('text', '')
        eid = entry.get('id')
        
        # Split into sentences roughly
        sentences = re.split(r'(?<=[.!?])\s+', simplified)
        
        issues = []
        
        # Check last sentence specifically for "cut-offs"
        if sentences:
            last_sent = sentences[-1].strip()
            if is_fragment(last_sent):
                issues.append(f"Possible fragment/cut-off at end: '{last_sent}'")
        
        # Check for extremely short simplifications (e.g. < 5 words) when original is long
        if len(simplified.split()) < 5 and len(original.split()) > 50:
            issues.append("Entry seems too short; major content might be missing.")
            
        # Check for repeated sentences (model artifact)
        if len(sentences) > 2:
            seen = set()
            for s in sentences:
                s_clean = s.lower().strip()
                if s_clean in seen and len(s_clean) > 10:
                    issues.append(f"Repeat sentence detected: '{s}'")
                seen.add(s_clean)

        if issues:
            cohesion_issues.append({
                "id": eid,
                "issues": issues,
                "simplified": simplified
            })
            
    return cohesion_issues

if __name__ == "__main__":
    # Check the rectified dataset
    issues = audit_cohesion('c:/JU Intern/rectified_1.json')
    
    output = {
        "total_cohesion_issues": len(issues),
        "issues": issues
    }
    
    with open('c:/JU Intern/cohesion_audit_log.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"Found {len(issues)} cohesion issues.")
    print("Log saved to c:/JU Intern/cohesion_audit_log.json")
