# Advanced Deep Learning Downloader

A utility script to download lecture slides, materials, and research papers from the University of Texas "Advances in Deep Learning" course.

[https://ut.philkr.net/advances_in_deeplearning/](https://ut.philkr.net/advances_in_deeplearning/)

## Overview

This tool automatically downloads and organizes:

- Lecture slides (PDF format)
- Additional lecture materials (ZIP format, when available)
- Research papers referenced in the course (PDF format)

All files are downloaded with consistent naming conventions and organized into appropriate directories.

## Requirements

- Python 3.6+
- Required packages:
  - requests
  - beautifulsoup4
  - tqdm

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/utmsai-adv-deep-learning-downloader.git
   cd utmsai-adv-deep-learning-downloader
   ```

2. Install required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Run the script with default settings:

```bash
python download_adl.py
```

This will:
- Download all lecture slides to `./adl-slides/`
- Download all research papers to `./adl-papers/`

### Advanced Options

The script supports several command-line arguments:

```bash
python download_adl.py [--slides-dir DIR] [--papers-dir DIR] [--skip-slides] [--skip-papers]
```

Options:

- `--slides-dir DIR`: Specify custom directory for lecture slides (default: `adl-slides`)
- `--papers-dir DIR`: Specify custom directory for research papers (default: `adl-papers`)
- `--skip-slides`: Skip downloading lecture slides
- `--skip-papers`: Skip downloading research papers

### Examples

Download only the lecture slides:
```bash
python download_adl.py --skip-papers
```

Download only the research papers:
```bash
python download_adl.py --skip-slides
```

Use custom directories:
```bash
python download_adl.py --slides-dir my_slides --papers-dir my_papers
```

## Features

- **Automatic organization**: Files are named consistently with numbering
- **Skip existing files**: Already downloaded files are skipped
- **Progress bars**: Visual feedback during downloads
- **Polite downloading**: Includes delays to avoid overwhelming the server

## Notes

- The script connects to `https://ut.philkr.net/advances_in_deeplearning/`
- Downloaded files are sanitized to ensure valid filenames
- The script attempts to maintain the course's original organization structure

## License

This project is available under the MIT License.
