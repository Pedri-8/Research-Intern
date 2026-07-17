import json
import os

def merge_datasets(file_path1, file_path2, output_path):
    print(f"Reading first file: {file_path1}...")
    with open(file_path1, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    print(f"Loaded {len(data1)} records.")

    print(f"Reading second file: {file_path2}...")
    with open(file_path2, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    print(f"Loaded {len(data2)} records.")

    # Combine lists
    combined_data = data1 + data2
    print(f"Combined total records: {len(combined_data)}")

    # Re-index sequentially from 1 to N
    for index, record in enumerate(combined_data):
        record['id'] = index + 1

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Writing combined data to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)

    print("Success! Merged and re-indexed sequentially.")

if __name__ == "__main__":
    file1 = 'c:/JU Intern/simplified_1.json'
    file2 = 'c:/JU Intern/output/simplified_new10k.json'
    output = 'c:/JU Intern/output/combined_simplified_19830.json'
    merge_datasets(file1, file2, output)
