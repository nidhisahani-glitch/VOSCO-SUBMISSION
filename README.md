# Natural Language to SQL (LM Studio) - NLP-QUERY-HUB

A simple **Streamlit** web app that lets you upload a CSV file and ask questions in plain English. The app converts your request into a SQL query automatically and shows results. Everything runs locally—no database setup required.

---

## Features

- **CSV Upload & Preview**  
  Drag and drop CSV files (up to 200MB) and preview data with shape information.  

- **Natural Language Queries**  
  Type requests in plain English and get SQL generated automatically using a local AI model (**Qwen2.5-1.5B-Instruct**).  

- **Safe SQL Generation**  
  Only single `SELECT` queries are allowed. Built-in checks prevent SQL injection or multi-statements.  

- **Execution on CSV**  
  Runs SQL queries directly on uploaded CSVs using **DuckDB**—no external database needed.  

- **Results Display**  
  Shows results as an interactive table.  

- **Query History**  
  Logs all queries (success/failure) with timestamps. Export history as a CSV file.  

- **Offline / Local-First**  
  Works entirely offline once LM Studio is set up.  

---

## Requirements

- Python 3.8+  
- LM Studio installed locally with **Qwen2.5-1.5B-Instruct** model loaded  

**Dependencies:**  
```text
streamlit
pandas
requests
duckdb
````

Install via:

```bash
pip install -r requirements.txt
```

---

## Setup

1. **Get the App**

```bash
git clone <your-repo>  # Or just save the .py file
cd <project-dir>
pip install -r requirements.txt
```

2. **Start LM Studio**

   * Install LM Studio locally
   * Load the **qwen2.5-1.5b-instruct** model
   * Start the API server (default: `http://localhost:1234/v1`)

3. **Run the App**

```bash
streamlit run app.py
```

* Opens in browser at `http://localhost:8501`

---

## Usage

1. **Upload CSV**
   Drag your CSV file into the uploader. Preview the data and schema.

2. **Enter a Query**
   Type a natural language request, e.g.,
   `"List all employees in the sales department"`

3. **Generate & Execute SQL**
   Click the button. The app will:

   * Ask the AI to generate SQL based on your CSV schema
   * Ensure it’s safe and only a `SELECT`
   * Execute the query on your CSV and show results

4. **Download Query History**
   Export all logged queries as `queries_history_YYYYMMDD_HHMMSS.csv`

**Example Workflow:**

* CSV: `employees.csv` with columns `employee_name, department_name, salary`
* Query: `"Show all employees in sales"`
* Generated SQL: `SELECT employee_name FROM data WHERE department_name = 'sales'`
* Results: Filtered table
* History CSV logs query, SQL, status, and timestamp

---

## Configuration

Edit `app.py` to customize:

* **API_BASE:** LM Studio endpoint (e.g., change IP/port)
* **LM_CHAT_MODEL:** Model name
* **MAX_TOKENS / TEMPERATURE:** Control AI response length and randomness

---

## Troubleshooting

* **LM Studio Errors:** Ensure the server is running and model is loaded. Test API with `curl http://your-ip:1234/v1/models`
* **SQL Safety Fail:** Only `SELECT` statements allowed; regenerate if needed
* **DuckDB Issues:** Ensure CSV is well-formed; large files may need sampling
* **No Results:** Column names in schema must match exactly (case-sensitive)
* 
