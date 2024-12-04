import os
import sys
import json
import re
import argparse
import requests
import yaml
from datetime import datetime, timedelta, timezone
import pytz
from PIL import Image
from io import BytesIO

# Define a set of invalid characters for Windows filenames and folder names
INVALID_CHARS = r'[<>:"/\\|?*]'
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1", "COM2", "LPT2", "COM3", "LPT3", "COM4", "LPT4", "COM5", "LPT5", "COM6", "LPT6", "COM7", "LPT7", "COM8", "LPT8", "COM9", "LPT9"}

URL_PREVIEW_API = "https://api.microlink.io"  # Free API to get URL preview

# Function to fetch URL preview from microlink API
def fetch_url_preview(url, title=None, screenshots_dir="screenshots"):
    try:
        params = {
            'url': url,
            'screenshot': True
        }

        # Send the request with the parameters
        response = requests.get(URL_PREVIEW_API, params)
        data = response.json()

        # Check if the API call was successful
        if data.get("status") != "success": 
            if data.get("code") == 'ERATE':
                reset_time_utc = response.headers.get("X-Rate-Limit-Reset")
                if reset_time_utc:
                    # Convert the reset time to a datetime object in UTC
                    reset_time = datetime.fromtimestamp(int(reset_time_utc), timezone.utc)

                    # Convert UTC reset time to local time
                    local_timezone = pytz.timezone("Asia/Kolkata")  # Replace with user's local timezone if known
                    reset_time_local = reset_time.astimezone(local_timezone)

                    # Calculate wait time in seconds
                    current_time = datetime.now(timezone.utc)
                    wait_time = (reset_time - current_time).total_seconds()

                    # Display a message to the user with local time
                    print(f"Microlink API rate limit reached. Please retry after {int(wait_time)} seconds, at {reset_time_local.strftime('%Y-%m-%d %H:%M:%S')} local time.")
                sys.exit()
            elif data.get("code") == 'EINVALURL':
                print(f"API call was not successful. Continuing to next bookmark. Code: {data['code']}.")
                return {
                    "description": None,
                    "image_url": None,
                    "screenshot_url": None,
                    "screenshot_name": None
                    }
            

        # Extract data from the API response
        preview_data = data.get("data", {})
        description = preview_data.get("description",None)
        image_url = preview_data.get("image", {}).get("url") if preview_data.get("image") else None
        screenshot_url = preview_data.get("screenshot", {}).get("url", None) or None

        # Save the screenshot locally if a screenshot URL is provided
        if screenshot_url:
            screenshot_name = save_screenshot_locally(screenshot_url, title, screenshots_dir)

        return {
            "description": description,
            "image_url": image_url,
            "screenshot_url": screenshot_url,
            "screenshot_name": screenshot_name if screenshot_url else None
        }

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        sys.exit()

def save_screenshot_locally(screenshot_url, title, screenshots_dir="screenshots"):
    """
    Download the screenshot from the given URL and save it locally to the specified screenshots directory
    with a filename derived from the URL. Return the path to the saved screenshot or None if
    the download failed.
    """
    try:
        # Create the screenshots directory if it doesn't exist
        create_dir(screenshots_dir)

        # The filename for the screenshot is same as the title (and same as the markdown file name)
        filepath = os.path.join(screenshots_dir, f"{title}.png")

        # Download and save the screenshot image
        response = requests.get(screenshot_url)
        image = Image.open(BytesIO(response.content))

        # Resize the image to fit within an 800-pixel width
        image.thumbnail((800, image.height), Image.LANCZOS)

        # Save the resized image
        image.save(filepath, format="PNG")

        print(f"Screenshot saved to {filepath}")
        return title

    except requests.RequestException as e:
        print(f"Failed to download screenshot: {e}")
        return None
    
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
def create_markdown_file(path, title, url, date_added, screenshots_dir="screenshots"):
    filename = os.path.join(path, f"{title}.md")
    if os.path.exists(filename):
        return
    with open(filename, "w", encoding="utf-8") as md_file:
        md_file.write("---\n")
        md_file.write(f"title: \"{title}\"\n")
        md_file.write(f"url: \"{url}\"\n")
        md_file.write(f"date: \"{date_added}\"\n")
        md_file.write(f"tags:\n  - Bookmark\n")
        md_file.write("---\n\n")
        md_file.write(f"# {title}\n\n")
        md_file.write(f"[{url}]({url})\n\n")
        preview = fetch_url_preview(url, title, screenshots_dir)
        if preview['description']:
            md_file.write(f"{preview['description']}\n\n")
        if preview['screenshot_name']:
            md_file.write(f"![[{preview['screenshot_name']}.png]]\n\n")
        daily_note_link = generate_daily_note_link(date_added)
        md_file.write(f"Date Added: [{date_added}]({daily_note_link})")
        print(f"Markdown file created: {filename}")

# Function to convert Chrome's timestamp format to a readable datetime string
def convert_chrome_timestamp(timestamp):
    # Convert microseconds to seconds and adjust by subtracting the Unix epoch offset (11644473600 seconds)
    return datetime(1601, 1, 1) + timedelta(microseconds=int(timestamp))

# Recursive function to process bookmarks and folders
def process_bookmarks(bookmarks, parent_path, screenshots_dir="screenshots"):
    for item in bookmarks:
        if item['type'] == 'folder':
            folder_name = sanitize_name(item['name'])
            folder_path = os.path.join(parent_path, folder_name)
            create_dir(folder_path)
            process_bookmarks(item['children'], folder_path, screenshots_dir)
        elif item['type'] == 'url':
            bookmark_name = sanitize_name(item['name'])
            bookmark_url = item['url']
            date_added = convert_chrome_timestamp(item.get('date_added', 0)).strftime('%Y-%m-%d %H:%M:%S')
            create_markdown_file(parent_path, bookmark_name, bookmark_url, date_added, screenshots_dir)

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
    parser.add_argument('-s', '--screenshots', type=str, help='Output directory for screenshots')
    args = parser.parse_args()

    # Load configuration from YAML file
    config = load_config(args.config) if os.path.exists(args.config) else {}

    # Get the JSON file, output directory, and screenshots directory from arguments or config file
    json_file = args.json or config.get('json_file')
    output_dir = args.output or config.get('output_dir')
    screenshots_dir = args.screenshots or config.get('screenshots_dir', 'screenshots')
    
    if not json_file or not output_dir:
        print("Error: JSON file and output directory must be provided either as arguments or in the config.yaml file.")
        return

    # Load bookmark data from JSON file
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Get the bookmarks from the "bookmark_bar"
    bookmarks = data['roots']['bookmark_bar']['children']
    
    # Process bookmarks
    process_bookmarks(bookmarks, output_dir, screenshots_dir)
    
if __name__ == "__main__":
    main()