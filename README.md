# Chrome Bookmarks to Obsidian Markdown Converter

## Pull requests welcomed

## Introduction

This Python script converts your Google Chrome bookmarks JSON file into Markdown files that can be used with ObsidianMD. Each bookmark is converted into a separate Markdown file, organized into folders that mirror the structure of your Chrome bookmarks. The script also adds metadata as frontmatter to each Markdown file, including the title, URL, and date added. Search the web to find where the Google Chrome stores the bookmarks JSON file for your os. Make a copy of the file to work upon rather than working on the original. Similarly the output folder should be outside the your vault, copy over once you are satisfied with the output.

## Features

- Converts Chrome bookmarks JSON file to Markdown files.
- Organizes Markdown files into folders reflecting your Chrome bookmarks structure.
- Adds metadata (title, URL, and date added) as frontmatter in each Markdown file.
- Allows configuration via command-line arguments or a `config.yaml` file.

## Requirements

- Python 3.6+
- `pyyaml` package

You can install the required Python package using pip:

```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Arguments
You can run the script with the following command-line arguments:

* --json (-j): Path to the Chrome bookmarks JSON file.
* --output (-o): Output directory where the Markdown files will be saved.
* --config (-c): Path to a config.yaml file that provides default values for the JSON file and output directory.

```bash
python script.py --json bookmarks.json --output Bookmarks

```
### Using config.yaml
Instead of passing the JSON file and output directory as arguments, you can specify them in a config.yaml file:
```yaml
json_file: "bookmarks.json"
output_dir: "ObsidianBookmarks"
```
### Example of markdown file produced

```markdown
---
title: "Some Bookmark Title"
url: "https://example.com"
date_added: "2023-08-29 12:34:56"
---

# Some Bookmark Title

[https://example.com](https://example.com)
```

## License
This project is free to use as you please