import json

def validate_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Total records: {len(data)}")
        
        errors = []
        for i, item in enumerate(data):
            if 'id' not in item:
                errors.append(f"Record {i}: Missing 'id'")
            if 'text' not in item:
                errors.append(f"Record {i}: Missing 'text'")
            if 'simplified' not in item or not item['simplified']:
                errors.append(f"Record {i}: Missing or empty 'simplified'")
            
            # Check for sequential IDs
            if 'id' in item and item['id'] != i + 1:
                errors.append(f"Record {i}: ID mismatch (Expected {i+1}, got {item['id']})")
                
        if not errors:
            print("Validation successful: No errors found.")
        else:
            print(f"Validation failed with {len(errors)} errors.")
            for error in errors[:10]:
                print(error)
            if len(errors) > 10:
                print("...")
                
    except Exception as e:
        print(f"Error reading JSON: {e}")

validate_json(r'c:\JU Intern\output\simplified_new10k.json')
