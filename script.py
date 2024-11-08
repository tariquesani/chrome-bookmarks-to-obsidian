import os
import json
import re
import argparse
import requests
import yaml
from datetime import datetime, timedelta

# Define a set of invalid characters for Windows filenames and folder names
INVALID_CHARS = r'[<>:"/\\|?*]'
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1", "COM2", "LPT2", "COM3", "LPT3", "COM4", "LPT4", "COM5", "LPT5", "COM6", "LPT6", "COM7", "LPT7", "COM8", "LPT8", "COM9", "LPT9"}

URL_PREVIEW_API = "https://api.microlink.io/?url="  # Free API to get URL preview

# Function to fetch URL preview from microlink API
def fetch_url_preview(url):
    try:
        response = requests.get(URL_PREVIEW_API + url)
        if response.status_code == 200:
            data = response.json().get("data", {})
            if data.get("description"):
                description = data.get("description")
            else:
                description = None
            if data.get("image"):
                image_url = data.get("image").get("url")
            else:
                image_url = None
            return description, image_url
    except requests.RequestException:
        return None, None
    return None, None

# Function to sanitize folder and file names
def sanitize_name(name, max_length=128):
    # Remove invalid characters
    name = re.sub(INVALID_CHARS, '', name)
    # Truncate to the max length
    name = name[:max_length].strip()
    # Handle reserved names
    if name.upper() in RESERVED_NAMES:
        name = f"{name}_reserved"
    return name

# Function to generate daily note link based on watched date
def generate_daily_note_link(date_added):
    date_obj = datetime.strptime(date_added, '%Y-%m-%d %H:%M:%S')
    year = date_obj.strftime('%Y')
    month_num = date_obj.strftime('%m')
    month_name = date_obj.strftime('%B')
    day_date = date_obj.strftime('%Y-%m-%d')
    day_name = date_obj.strftime('%A')
    return f"/DailyNotes/{year}/{month_num}-{month_name}/{day_date}-{day_name}.md"



# Function to create directories if they do not exist
def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Function to create markdown files for bookmarks with metadata as frontmatter
def create_markdown_file(path, title, url, date_added):
    filename = os.path.join(path, f"{title}.md")
    with open(filename, "w", encoding="utf-8") as md_file:
        md_file.write("---\n")
        md_file.write(f"title: \"{title}\"\n")
        md_file.write(f"url: \"{url}\"\n")
        md_file.write(f"date: \"{date_added}\"\n")
        md_file.write(f"tags:\n  - Bookmark\n")
        md_file.write("---\n\n")
        md_file.write(f"# {title}\n\n")
        md_file.write(f"[{url}]({url})\n\n")
        description, image_url = fetch_url_preview(url)
        if description:
            md_file.write(f"{description}\n\n")
        if image_url:
            md_file.write(f"![{title}]({image_url})\n\n")
        daily_note_link = generate_daily_note_link(date_added)
        md_file.write(f"Date Added: [{date_added}]({daily_note_link})")

# Function to convert Chrome's timestamp format to a readable datetime string
def convert_chrome_timestamp(timestamp):
    # Convert microseconds to seconds and adjust by subtracting the Unix epoch offset (11644473600 seconds)
    return datetime(1601, 1, 1) + timedelta(microseconds=int(timestamp))

# Recursive function to process bookmarks and folders
def process_bookmarks(bookmarks, parent_path):
    for item in bookmarks:
        if item['type'] == 'folder':
            folder_name = sanitize_name(item['name'])
            folder_path = os.path.join(parent_path, folder_name)
            create_dir(folder_path)
            process_bookmarks(item['children'], folder_path)
        elif item['type'] == 'url':
            bookmark_name = sanitize_name(item['name'])
            bookmark_url = item['url']
            date_added = convert_chrome_timestamp(item.get('date_added', 0)).strftime('%Y-%m-%d %H:%M:%S')
            create_markdown_file(parent_path, bookmark_name, bookmark_url, date_added)

# Function to load configuration from YAML file
def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)
    


# Main function
def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Convert Chrome bookmarks to ObsidianMD markdown files.')
    parser.add_argument('-c', '--config', type=str, default='config.yaml', help='Path to the config.yaml file')
    parser.add_argument('-j', '--json', type=str, help='Path to the bookmarks JSON file')
    parser.add_argument('-o', '--output', type=str, help='Output directory for markdown files')
    args = parser.parse_args()

    # Load configuration from YAML file
    config = load_config(args.config) if os.path.exists(args.config) else {}

    # Get the JSON file and output directory from arguments or config file
    json_file = args.json or config.get('json_file')
    output_dir = args.output or config.get('output_dir')
    

    if not json_file or not output_dir:
        print("Error: JSON file and output directory must be provided either as arguments or in the config.yaml file.")
        return

    # Load bookmark data from JSON file
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Get the bookmarks from the "bookmark_bar"
    bookmarks = data['roots']['bookmark_bar']['children']
    
    # Process bookmarks
    process_bookmarks(bookmarks, output_dir)

if __name__ == "__main__":
    main()
