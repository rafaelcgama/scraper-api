# WallStreetSurvivor Scraper

Python-based scraper that authenticates into **Wall Street Survivor**, retrieves a user’s transaction history, transforms the data into a DataFrame, and saves it as a **Parquet** file.

The scraper is designed to be:
- **Fast** (browser used only for authentication)
- **Simple** (clear separation of concerns)
- **Runnable on demand** (CLI-style execution)

---

## Requirements

- Python **3.10+**
- Google Chrome (or Chromium)
- ChromeDriver (handled automatically by SeleniumBase)

---

## Environment Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuring Credentials

This project uses a `.env` file to store login credentials securely.

In the project root directory, create a file named **.env**

Add your Wall Street Survivor credentials:

```env
WSS_USERNAME=your_email@example.com
WSS_PASSWORD=your_password
```

## Running the Scraper

Once the environment is set up and credentials are configured, you can run the scraper.

### 1. Ensure prerequisites

- Virtual environment is activated  
- Dependencies are installed  
- **.env** file exists with valid credentials  

### 2. Run the scraper

From the project root directory:

```bash
python -m wss_scraper.scrape
```

Optional flags:

- Run headless (no visible browser)
```bash
python -m wss_scraper.scrape --headless
```

- Specify a custom output file path.  
  If not provided, the scraper uses the default path defined in the code.
```bash
python -m wss_scraper.scrape --out my_transactions.parquet
```

### 3. Testing the scraper

Run all tests
```bash
python -m unittest -v
```

Run a specific test module
```bash
python -m unittest -v wss_scraper.tests.test_login
```

Test coverage is measured using coverage.py.

Run tests with coverage:
```bash
coverage run -m unittest
```

View coverage report in the terminal:
```bash
coverage report -m
```

Optional (HTML report)
```bash
coverage html
open htmlcov/index.html     # macOS
# start htmlcov\index.html  # Windows
```

### 4. Output

The scraper will:
- Authenticate using a real browser
- Reuse the authenticated session for HTTP requests
- Retrieve the full transaction history
- Transform the data into a DataFrame
- Save the result as a Parquet file

If the script completes successfully, the Parquet file will be created automatically.

## Notes
- Browser automation is used only for authentication.
- All transaction data is fetched via HTTP for performance.
- The scraper is intended to be run as a short-lived batch process.