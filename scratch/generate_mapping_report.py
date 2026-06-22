import json
from collections import defaultdict

def generate_issue_report(audit_log_path, output_path):
    with open(audit_log_path, 'r', encoding='utf-8') as f:
        log = json.load(f)
    
    report = defaultdict(list)
    
    for entry in log:
        eid = entry.get('id')
        for issue in entry.get('issues', []):
            # Clean up issue description for grouping
            if "joining long ideas with 'and'" in issue:
                key = "Compound sentences joined by 'and'"
            elif "joining long ideas with 'so'" in issue:
                key = "Improper use of 'so' for joining ideas"
            elif "joining long ideas with 'ut'" in issue or "joining long ideas with 'but'" in issue:
                key = "Compound sentences joined by 'but'"
            elif "joining long ideas with 'ecause'" in issue or "joining long ideas with 'because'" in issue:
                key = "Improper use of 'because' as a joiner"
            elif "Hard word detected" in issue:
                key = "Complex vocabulary / Hard words"
            elif "Long sentence" in issue:
                key = "Overly long sentences (>15 words)"
            else:
                key = "Other structural issues"
            
            report[key].append(eid)

    # Sort report keys and remove duplicates from ID lists
    sorted_report = {}
    for key in sorted(report.keys()):
        unique_ids = sorted(list(set(report[key])))
        sorted_report[key] = unique_ids

    # Create the text report
    lines = ["# Dataset Issue Mapping Report\n"]
    lines.append("This report lists the IDs of dataset entries that exhibited specific issues. These were rectified in the final version.\n")
    
    for issue, ids in sorted_report.items():
        lines.append(f"## {issue}")
        lines.append(f"**Total Count:** {len(ids)}")
        # If there are a lot of IDs, show first 100 and indicate others are in the file
        display_ids = [str(i) for i in ids]
        if len(display_ids) > 100:
            lines.append(", ".join(display_ids[:100]) + f", ... (and {len(display_ids)-100} more)")
        else:
            lines.append(", ".join(display_ids))
        lines.append("\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    return sorted_report

if __name__ == "__main__":
    generate_issue_report('c:/JU Intern/dataset_audit_log.json', 'c:/JU Intern/issue_mapping_report.md')
    print("Report generated at c:/JU Intern/issue_mapping_report.md")
