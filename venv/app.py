import streamlit as st
import pandas as pd
import io
import json
import re
import requests
import duckdb
from datetime import datetime

# CONFIGURATIONS
API_BASE = "http://192.168.137.1:1234/v1"
API_CHAT = f"{API_BASE}/chat/completions"
LM_CHAT_MODEL = "qwen2.5-1.5b-instruct"

# SQL SAFETY
DENY_PATTERN = re.compile(
    r";|--|\b(insert|update|delete|drop|truncate|alter|create|grant|revoke|replace|exec|call|copy|vacuum)\b",
    flags=re.IGNORECASE,
)
# LLM STUDIO
def call_lmstudio_chat(prompt: str, max_tokens: int = 256, temperature: float = 0.0, timeout: int = 60):
    payload = {
        "model": LM_CHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(temperature),
        "max_tokens": int(max_tokens)
    }
    r = requests.post(API_CHAT, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    # safe access depending on LM Studio response format
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        # fallback: try older schema
        return data["choices"][0]["text"]

# SQL CLEANING
def clean_sql_from_model(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    # remove triple-backticks and language tags
    t = re.sub(r"^```(?:sql)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t, flags=re.IGNORECASE).strip()
    # Strip trailing semicolon (harmless for single stmt)
    t = t.rstrip(';').strip()
    # find first SELECT ... occurrence
    m = re.search(r"(select\b.*)", t, flags=re.IGNORECASE | re.DOTALL)
    candidate = m.group(1).strip() if m else t
    # collapse newlines
    candidate = " ".join(line.strip() for line in candidate.splitlines() if line.strip())
    return candidate

def is_sql_safe(sql_text: str) -> bool:
    if not sql_text:
        return False
    s = sql_text.strip()
    # Strip trailing semicolon for check
    s = s.rstrip(';').strip()
    # must begin with a single SELECT
    if not s.lower().startswith("select"):
        return False
    # disallow dangerous keywords
    if DENY_PATTERN.search(s):
        return False
    # disallow semicolons to prevent multiple statements (after strip)
    if ";" in s:
        return False
    return True

# CSV & SCHEMA
def load_csv(uploaded_file):
    """Load uploaded CSV to pandas DF"""
    df = pd.read_csv(uploaded_file)
    return df

def get_schema_hint(df):
    """Generate schema string for prompt: data(col1 type, col2 type, ...)"""
    types = df.dtypes.astype(str).to_dict()
    cols = ', '.join([f"{col} ({types[col]})" for col in df.columns])
    return f"data({cols})"

# SQL EXCUETIONS
def execute_sql_on_df(df, sql_text):
    """Execute SQL on DF using DuckDB (in-memory)"""
    try:
        con = duckdb.connect()
        con.register('data', df)
        result_df = con.execute(sql_text).df()
        con.close()
        return result_df, None
    except Exception as e:
        return None, str(e)

# HISTORY
if 'history' not in st.session_state:
    st.session_state.history = []

# STREAMLIT UI
st.set_page_config(page_title="QUERY-HUB", layout="wide")
st.title(" NLP-QUERY-HUB")

# Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = load_csv(uploaded_file)
    st.subheader("Data Preview")
    st.dataframe(df.head(10), use_container_width=True)
    st.info(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    
    schema_hint = get_schema_hint(df)
    
    st.subheader("Type your Query in your Language")
    user_input = st.text_area("Type your request....", height=100)
    
    if st.button("Get your SQL Query"):
        if not user_input.strip():
            st.warning("Please enter a query.")
        else:
            user_q = user_input.strip()
            st.write("**User request:**", user_q)
            
            # Create prompt (adapted from original, added no semicolon)
            prompt = f"""You are an SQL writer for a single table named 'data' in PostgreSQL/DuckDB. Convert the user's request into ONE valid SELECT SQL statement only. Use only this table. Return only the SELECT statement (no explanation, no trailing semicolon).

Schema: {schema_hint}

User request: {user_q!r}
SQL:
"""
            
            # Call LM Studio
            try:
                lm_out = call_lmstudio_chat(prompt, max_tokens=256, temperature=0.0)
                sql_candidate = clean_sql_from_model(lm_out)
                st.subheader("Generated SQL")
                st.code(sql_candidate, language="sql")
            except Exception as e:
                st.error(f"LM Studio error: {str(e)}")
                st.stop()
            
            # Safety check (from original)
            if not is_sql_safe(sql_candidate):
                st.error("Generated SQL failed safety checks.")
                st.stop()
            
            # Execute (adapted logic)
            st.info("Executing SQL on your data...")
            result_df, err = execute_sql_on_df(df, sql_candidate)
            if err:
                st.error(f"SQL execution error: {err}")
            else:
                st.success("Query executed successfully.")
                st.subheader("Results")
                st.dataframe(result_df, use_container_width=True)
            
            # Log to history (simplified from original)
            log_entry = {
                'id': len(st.session_state.history) + 1,
                'user_query': user_q,
                'generated_sql': sql_candidate,
                'executed': err is None,
                'error_text': err,
                'created_at': datetime.now().isoformat()
            }
            st.session_state.history.append(log_entry)
            st.success("Query logged to history.")

    # Download History CSV Button
    st.subheader("Query History Download")
    if st.button("Download Your all Queries History as CSV"):
        if st.session_state.history:
            history_df = pd.DataFrame(st.session_state.history)
            csv_buffer = io.StringIO()
            history_df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")
            st.download_button(
                label="Download History CSV",
                data=csv_bytes,
                file_name=f"queries_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No queries in history yet.")

else:
    st.info("👆 Please upload a CSV file to start querying.")

st.markdown("---")