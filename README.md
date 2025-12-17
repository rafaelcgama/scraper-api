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
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
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
- `.env` file exists with valid credentials  

### 2. Run the scraper

From the project root directory:

```bash
python scrape.py
```

### 3. Output

The scraper will:
- Log in to Wall Street Survivor
- Retrieve the transaction history
- Transform the data into a DataFrame
- Save the result as a Parquet file in the project directory

If the script completes successfully, the Parquet file will be created automatically.