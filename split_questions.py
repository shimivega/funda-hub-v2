import json
import os
from pathlib import Path

def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def save_grade_questions(grade, questions, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Sanitize grade name for filename
    safe_grade = "".join(c if c.isalnum() else "_" for c in grade)
    output_path = os.path.join(output_dir, f"{safe_grade}_questions.json")
    
    # Save the questions for this grade
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    # Check file size
    size_mb = get_file_size_mb(output_path)
    print(f"Saved {len(questions)} questions for {grade} to {output_path} ({size_mb:.2f} MB)")

def main():
    # Configuration
    input_files = [
        "static/data/practice_zone_questions.json",
        "static/data/practice_zone_questions (2).json"
    ]
    output_dir = "static/data/split_by_grade"
    
    # Initialize data structures
    grade_questions = {}
    
    # Process each input file
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            continue
            
        print(f"Processing {file_path}...")
        data = load_json_file(file_path)
        
        # Group questions by grade
        for item in data:
            grade = item.get('grade', 'Unknown')
            if grade not in grade_questions:
                grade_questions[grade] = []
            grade_questions[grade].append(item)
    
    # Save questions by grade
    for grade, questions in grade_questions.items():
        save_grade_questions(grade, questions, output_dir)
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()
