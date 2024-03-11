# YC Company Scraper

This Python script scrapes startup information from provided URLs of Y Combinator (YC) companies. It extracts details such as the company's name, tagline, abstract, year founded, number of jobs available, operational status, location, and team size from each URL and saves the data to a CSV file.

## Requirements

- Python 3
- BeautifulSoup4
- requests
- fire
- csv

## Installation

Ensure you have Python 3 installed on your system. You can then install the required Python libraries using pip:

```bash
pip install beautifulsoup4 requests fire
```

## Usage

The script can be executed from the command line, providing flexibility with input and output files, the number of retries for requests, and verbosity of the output.

### Basic Command

```bash
python main.py
```

This command runs the script using default settings, which are defined in the script. By default, it looks for `input.csv` for URLs to scrape, attempts up to 3 retries for each URL, and outputs the results to `output.csv` with verbose logging enabled.

### Custom Input and Output CSV Files

You can specify custom input and output CSV files using the `--input_csv`, `--output_csv`, `--max_retries` and `--verbose` arguments:

```bash
python main.py --input_csv sample_input.csv --output_csv my_output.csv
```

Verbose output is enabled by default. To run the script without verbose output, use the `--verbose` argument:

```bash
python main.py --verbose False
```

## Input CSV Format

The input CSV should contain URLs to scrape, one per line. For example:

```csv
https://example.com/company1
https://example.com/company2
```

## Output CSV Format

The output CSV will contain columns for each piece of information scraped, including the URL, with one company per row.

---
