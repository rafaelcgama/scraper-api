# Scraper Design & Architecture

This document describes the architecture, data flow, and key design decisions behind the WallStreetSurvivor transaction
scraper.

---

## Overall Architecture

The scraper follows a **two-phase architecture** optimized for performance and reliability:

1. **Browser-based authentication (SeleniumBase)**
2. **HTTP-based data retrieval (`requests.Session`)**

A real browser is used **only once** to handle authentication and anti-bot protections.  
After authentication, all data retrieval is performed using a persistent HTTP session.

---

### Component Responsibilities

| Component     | Responsibility                                                             |
|---------------|----------------------------------------------------------------------------|
| `login.py`    | Authenticate using SeleniumBase and extract cookies and user-agent         |
| `fetch.py`    | Handle authenticated GET requests with generic retry/backoff logic           |
| `parse.py`    | Parse HTML fragments with improved resilience (warns on missing cells)        |
| `scrape.py`   | Orchestrate workflow with modernized `datetime` range logic                   |
| `login.py`    | Authenticate with clarified click strategies (Native vs JS)                   |
| `settings.py` | Centralize scraper-specific configuration                                     |

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
    - This session represents an authenticated user and is reused for all subsequent requests.

3. **Transaction Retrieval**
    - The scraper calls the transaction history endpoint using pagination parameters.
    - Each response returns JSON containing an HTML fragment with transaction rows.
    - The same HTTP session is reused across all pages.

4. **Parsing**
    - HTML fragments are parsed using `lxml`.
    - Each table row is converted into a structured dictionary.
    - Parsed rows are accumulated in memory.

5. **Persistence**
    - Parsed records are converted into a Pandas DataFrame.
    - The final dataset is written to disk as a Parquet file.

This approach minimizes browser usage while maintaining correctness and performance.

---

## Trade-offs and Assumptions

### Browser Usage

**Decision:**  
Use browser automation for authentication.

**Trade-off:**  
Browser automation is slower than pure HTTP requests.

**Reason:**  
WallStreetSurvivor blocks programmatic HTTP login attempts via anti-bot protections (e.g., Cloudflare).  
A real browser is therefore required for authentication.

To limit the performance impact, SeleniumBase is used only once for login, after which all data retrieval is performed
via fast HTTP requests.

---

### Session Reuse Strategy

**Decision:**  
Reuse the authenticated session only within a single scraper run.

**Trade-off:**  
Login state is not persisted across executions, requiring re-authentication on each run.

**Reason:**  
The scraper is designed as an on-demand batch process that runs infrequently.  
Re-authenticating once per run keeps the implementation simple and predictable, while still avoiding repeated browser
usage during data retrieval.

Within a run, authentication cookies and the user-agent are reused for all HTTP requests, ensuring efficient pagination
without additional browser interaction.

---

### Session Handling

**Assumption:**  
Authenticated session cookies remain valid for the duration of the scrape.

**Reason:**  
The scraper is intended to run as a short-lived batch job.  
If session expiration occurs mid-run, the correct recovery strategy is to re-authenticate and restart the process.

---

### Dynamic Header Extraction

**Decision:**  
Fetch table headers dynamically from the transaction history page.

**Trade-off:**  
An additional HTTP request is required before retrieving transaction data.

**Reason:**  
Transaction rows are loaded asynchronously and do not include column names.  
Fetching headers dynamically ensures the scraper adapts to column additions, renames, or reordering without hardcoding a
schema, improving maintainability at negligible cost.

---

### Parsing Strategy

**Decision:**  
Parse HTML fragments using `lxml` and XPath, but with a "Soft Failure" policy for missing data.

**Trade-off:**  
The scraper may occasionally skip a row if expected data is missing, but it will continue to completion.

**Reason:**  
Web UI elements frequently change or have minor inconsistencies. Previously, a single empty cell would crash the entire scrape. Now, the parser logs a warning and skips the problematic row, ensuring the rest of the dataset is preserved. This matches the resilient nature of modern data engineering.

---

### Network Reliability

**Decision:**  
Centralize all HTTP GET requests through a shared `_get_with_retry` helper.

**Trade-off:**  
Slightly more abstraction in the `fetch.py` layer.

**Reason:**  
Network connections are inherently unstable. By centralizing the retry logic with exponential backoff (retrying 3 times with increasing delays), the scraper can successfully bypass transient network blips and temporary server 500 errors without failing the entire job.

---

### Logging and Retries

**Decision:**  
Implement minimal logging and targeted retries.

**Trade-off:**  
The scraper provides limited observability compared to verbose logging approaches.

**Reason:**  
Logging is intentionally limited to key lifecycle events (login, page fetch, completion), and retries are applied only
to network calls where transient failures are expected.  
This keeps the solution robust while avoiding unnecessary complexity for a take-home exercise.

---

## Summary

The scraper is intentionally designed to:

- Authenticate reliably
- Minimize browser usage
- Reuse sessions efficiently
- Parse data deterministically
- Persist results in an analytics-friendly format

The solution balances **performance, simplicity, and maintainability**, making it suitable for both technical evaluation
and practical use.