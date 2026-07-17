import json
import re

def sequential_number_ids(file_path):
    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Try to make it a valid JSON array if it isn't one
    is_array = content.startswith('[') and content.endswith(']')
    if not is_array:
        print("File is not wrapped in brackets. Adding them...")
        # If there's a trailing comma, remove it before wrapping
        if content.endswith(','):
            content = content[:-1]
        content = '[' + content + ']'
    
    try:
        data = json.loads(content)
        print("Successfully loaded JSON data.")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print("Attempting to parse manually using regex...")
        # Fallback: find all JSON-like objects
        # We can split by regex that matches the boundary between objects
        # e.g., },\s*\n\s*{
        data = []
        # Let's clean up content a bit
        cleaned_content = content
        if cleaned_content.startswith('['):
            cleaned_content = cleaned_content[1:]
        if cleaned_content.endswith(']'):
            cleaned_content = cleaned_content[:-1]
        
        parts = re.split(r'\}\s*,\s*\n\s*\{', cleaned_content)
        for i, p in enumerate(parts):
            # Reconstruct the JSON object string
            obj_str = p.strip()
            if not obj_str.startswith('{'):
                obj_str = '{' + obj_str
            if not obj_str.endswith('}'):
                obj_str = obj_str + '}'
            
            try:
                obj = json.loads(obj_str)
                data.append(obj)
            except Exception as ex:
                print(f"Failed to parse object {i}: {ex}")
                # Print a snippet for debugging
                print(f"Snippet: {obj_str[:200]}...")
    
    print(f"Loaded {len(data)} records.")
    
    # Update IDs sequentially
    for index, record in enumerate(data):
        record['id'] = index + 1
        
    # Write back as nice formatted JSON array
    print(f"Writing corrected data back to {file_path}...")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print("Done! Verified IDs sequentially.")

if __name__ == "__main__":
    sequential_number_ids('c:/JU Intern/simplified_1.json')
