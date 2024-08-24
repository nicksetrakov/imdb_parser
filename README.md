# IMDb Top 250 Cast Parser

This project contains two parsers for extracting cast information from IMDb's Top 250 movies. One parser uses Selenium, while the other uses Playwright.

## Requirements

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/nicksetrakov/imdb_parser.git
   cd imdb-parser
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # For Linux/Mac
   venv\Scripts\activate  # For Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Selenium Parser

To run the Selenium-based parser:
```python
python imdb_parser_selenium.py
```

### Playwright Parser

To run the Playwright-based parser:
```python
python imdb_parser_playwright.py
```
## Results

Parsers save the results to a CSV file `imdb_top250_cast.csv` or `imdb_top250_cast_async.csv` in the project's root directory.

## Logging

Execution logs are saved to the `imdb_parser.log` file.

## Notes

- The Selenium Parser requires ChromeDriver to be installed and compatible with your Chrome version.
- The Playwright Parser automatically downloads the necessary browsers on first run.

## Performance

You can compare the performance of both parsers by checking the execution time logged at the end of each run.