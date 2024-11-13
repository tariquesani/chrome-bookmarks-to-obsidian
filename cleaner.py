import os
import json
import shutil

# Define paths
CHROME_BOOKMARKS_PATH = r"C:\Users\ADMIN\AppData\Local\Google\Chrome\User Data\Profile 1\Bookmarks"  # Adjust as needed
EXPORT_FOLDER = "./Bookmarks"  # Folder where Markdown files are stored
SCREENSHOT_FOLDER = "./screenshots"  # Folder for bookmark screenshots
TRASH_FOLDER = "./trash"  # Folder to move obsolete files

# Function to load URLs from Chrome bookmarks JSON file
def load_current_bookmark_urls():
    with open(CHROME_BOOKMARKS_PATH, "r", encoding="utf-8") as file:
        bookmarks_data = json.load(file)
        urls = set()
        def parse_tree(tree):
            for item in tree:
                if item["type"] == "url":
                    urls.add(item["url"])
                elif item["type"] == "folder":
                    parse_tree(item["children"])
        parse_tree(bookmarks_data["roots"]["bookmark_bar"]["children"])
        return urls

# Function to extract URL from a Markdown file
def extract_url_from_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("url: "):
                start = line.find('"') + 1
                end = line.find('"', start)
                if start > 0 and end > 0:
                    return line[start:end]
    return None

# Function to move a file to the trash folder
def move_to_trash(file_path):
    os.makedirs(TRASH_FOLDER, exist_ok=True)
    try:
        shutil.move(file_path, TRASH_FOLDER)
        print(f"Moved to trash: {file_path}")
    except Exception as e:
        print(f"Error moving file {file_path} to trash: {e}")

# Function to clean up obsolete Markdown and screenshot files
def clean_obsolete_files():
    # Load the current bookmark URLs
    current_urls = load_current_bookmark_urls()
    print(f"Loaded {len(current_urls)} URLs from bookmarks")

    # Track the number of moved files
    moved_files_count = 0

    # Check each Markdown file
    for root, _, files in os.walk(EXPORT_FOLDER):
        for filename in files:
            if filename.endswith(".md"):
                file_path = os.path.join(root, filename)
                file_url = extract_url_from_markdown(file_path)
                
                # Check if the URL is still in the current bookmarks
                if file_url and file_url not in current_urls:
                    # Move the Markdown file to trash
                    move_to_trash(file_path)
                    moved_files_count += 1

                    # Check and move the corresponding screenshot file
                    screenshot_path = os.path.join(SCREENSHOT_FOLDER, f"{filename[:-3]}.png")
                    if os.path.isfile(screenshot_path):
                        move_to_trash(screenshot_path)
                        moved_files_count += 1

    print(f"Cleanup complete. Moved {moved_files_count} obsolete files to trash.")

# Run the cleanup
if __name__ == "__main__":
    clean_obsolete_files()
