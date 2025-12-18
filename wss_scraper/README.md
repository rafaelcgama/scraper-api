# Scraper Design & Architecture

This document describes the architecture, data flow, and key design decisions behind the WallStreetSurvivor transaction scraper.

---

## Overall Architecture

The scraper follows a **two-phase architecture** optimized for performance and reliability:

1. **Browser-based authentication (SeleniumBase)**
2. **HTTP-based data retrieval (`requests.Session`)**

A real browser is used **only once** to handle authentication and anti-bot protections.  
After authentication, all data retrieval is performed using a persistent HTTP session.

### Component Responsibilities

| Component | Responsibility |
|--------|----------------|
| `login.py` | Authenticate using SeleniumBase and extract cookies and user-agent |
| `fetch.py` | Reuse an authenticated HTTP session to retrieve paginated transaction data |
| `parse.py` | Parse HTML fragments into structured Python dictionaries |
| `scrape.py` | Orchestrate the workflow and persist results |
| `settings.py` | Centralize configuration and defaults |

This separation ensures each component has a **single, well-defined responsibility**.

---

## Data Flow

The end-to-end data flow is as follows:

1. **Authentication**
    - A real browser session logs in to WallStreetSurvivor.
    - Authentication cookies and the browser’s user-agent are extracted.
    - The browser is closed immediately after login.

2. **Session Reuse**
    - A `requests.Session` is created using the extracted cookies and user-agent.
    - This session represents an authenticated user and is reused for all requests.

3. **Transaction Retrieval**
    - The scraper calls the transaction history endpoint with pagination parameters.
    - Each response returns JSON containing an HTML fragment with transaction rows.
    - The same HTTP session is reused across all pages.

4. **Parsing**
    - HTML fragments are parsed using `lxml`.
    - Each table row is converted into a structured dictionary.
    - Parsed rows are accumulated in memory.

5. **Persistence**
    - Parsed records are converted into a Pandas DataFrame.
    - The final dataset is written to disk as a Parquet file.

This approach minimizes browser usage while maintaining correctness and speed.

---

## Trade-offs and Assumptions

### Browser Usage

**Trade-off:**  
Browser automation is slower than pure HTTP requests.

**Reason:**  
WallStreetSurvivor blocks programmatic HTTP login attempts via anti-bot protections (e.g., Cloudflare).  
A real browser is therefore required for authentication.

To limit the performance impact, SeleniumBase is used only once for login, after which all data retrieval is performed via fast HTTP requests.

---

### Session Reuse Strategy

**Trade-off:**  
The scraper reuses the authenticated session only within a single run and does not persist login state across executions.

**Reason:**  
This scraper is designed as an on-demand batch process that runs infrequently.  
Re-authenticating once per run keeps the implementation simple and predictable, while still avoiding repeated browser usage during data retrieval.

Within a run, authentication cookies and the user-agent are reused for all HTTP requests, ensuring efficient pagination without additional browser interaction.  
Persisting login state across runs would be a straightforward optimization if needed but was intentionally omitted to reduce complexity.

---

### Session Handling

**Assumption:**  
Authenticated session cookies remain valid for the duration of the scrape.

**Reason:**  
The scraper is designed to run as a short-lived batch job.  
If session expiration occurs, the correct recovery strategy would be to re-authenticate.

---

### Dynamic Header Extraction

**Trade-off**:
An additional HTTP request is made to retrieve table headers.

**Reason**:
Transaction rows are loaded asynchronously and do not include column names.
Fetching headers dynamically from the page ensures the scraper adapts to column additions, renames, or reordering without hardcoding a schema, improving maintainability while adding negligible overhead.

---

### Parsing Strategy

**Trade-off:**  
HTML fragments are parsed using pure `lxml` instead of BeautifulSoup + `lxml` or browser-based DOM extraction.

**Reason:**  
The transaction endpoint returns HTML embedded in a JSON payload rather than a structured API response.  
Using `lxml` with XPath provides faster, deterministic parsing with fewer dependencies, which is well suited for a stable table structure and a performance-focused scraper.

---

### Logging and Retries

**Design Choice:**  
Minimal logging and targeted retries are implemented.

**Reason:**
- Logging focuses on key lifecycle events (login, page fetch, completion).
- Retries are applied only to network calls where transient failures are expected.
- This keeps the solution robust without introducing unnecessary complexity for a take-home exercise.

---

## Summary

The scraper is intentionally designed to:
- Authenticate reliably
- Minimize browser usage
- Reuse sessions efficiently
- Parse data deterministically
- Persist results in an analytics-friendly format

The solution balances **performance, simplicity, and maintainability**, making it suitable for both technical evaluation and practical use.