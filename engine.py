# llm_core.py
# Minimal, importable core: LLM → SQL → DB → answer
# Uses: gemini_llm.GeminiLLM and few_shots_retail.FEWSHOTS from your project.

import os
import re
import ast
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Union, Optional

from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from gemini_llm import GeminiLLM
from few_shots_retail import FEW_SHOTS

# ---------- Env & DB ----------
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")   # e.g., mysql+pymysql://user:pass@localhost/Shirt_mart
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not DB_URL:
    raise RuntimeError("DATABASE_URL is not set")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set")

db = SQLDatabase.from_uri(DB_URL, sample_rows_in_table_info=3)
llm = GeminiLLM()

# ---------- Few-shots block ----------
EXAMPLES = "\n\n".join([f"Q: {e['q']}\nSQL: {e['sql']}" for e in FEW_SHOTS])

# ---------- Retail prompt ----------
RETAIL_PROMPT = PromptTemplate(
    input_variables=["question", "schema", "examples"],
    template=("""
You help a store cashier. Convert the question into ONE MySQL SELECT for this database.

Rules:
- Output ONLY the SQL on a single line. No prose, no labels, no code fences.
- Each (brand, color, size) row is a SKU.
- If they ask "how many / available / in stock", use SUM(`stock_quantity`) (not COUNT(*)).
- To use discounts, JOIN `t_shirts` t with `discounts` d ON t.`t_shirt_id`=d.`t_shirt_id`.
- Use exact enums and backticks on identifiers.
- Aggregates (SUM/COUNT/AVG/MIN/MAX): do NOT use LIMIT.
- SELECT only (no INSERT/UPDATE/DELETE/ALTER/DROP/TRUNCATE).

Examples:
{examples}

Schema:
{schema}

Question: {question}
""").strip()
)

# ---------- Helpers from notebook ----------

ENUMS = {
    "brand": {"Van Huesen", "Levi", "Nike", "Adidas"},
    "color": {"Red", "Blue", "Black", "White"},
    "size":  {"XS", "S", "M", "L", "XL"},
}

def normalize_retail(q: str) -> str:
    """Normalize casual cashier phrasing to match your enum spellings."""
    t = q.strip()

    # sizes
    t = re.sub(r"(?i)\bextra large\b|\bx large\b|\bxl\b", "XL", t)
    t = re.sub(r"(?i)\bextra small\b|\bx small\b|\bxs\b", "XS", t)
    t = re.sub(r"(?i)\blarge\b", "L", t)
    t = re.sub(r"(?i)\bmedium\b", "M", t)
    t = re.sub(r"(?i)\bsmall\b", "S", t)

    # brand spelling (your ENUM uses "Van Huesen")
    t = re.sub(r"(?i)\bvan heusen\b", "Van Huesen", t)

    # normalize product slang
    t = re.sub(r"(?i)\btee(s)?\b", "t-shirt", t)
    t = re.sub(r"(?i)\btshirt(s)?\b", "t-shirt", t)

    # case-correct brand & color names to enum case
    for b in ENUMS["brand"]:
        t = re.sub(rf"(?i)\b{re.escape(b)}\b", b, t)
    for c in ENUMS["color"]:
        t = re.sub(rf"(?i)\b{re.escape(c)}\b", c, t)

    return t

def _clean_sql(text: str) -> str:
    """Strip code fences; keep first SELECT; collapse whitespace; block non-SELECT; strip LIMIT for aggregates."""
    text = re.sub(r"^```(?:sql)?\s*|\s*```$", "", text.strip(), flags=re.I | re.M)
    m = re.search(r"select\s.+", text, flags=re.I | re.S)
    sql = m.group(0) if m else text
    sql = " ".join(sql.split())
    sql = re.sub(r";+\s*$", "", sql)

    # block non-SELECT
    if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE)\b", sql, flags=re.I):
        raise ValueError(f"Non-SELECT generated: {sql}")

    # strip LIMIT on aggregates
    low = sql.lower()
    if any(fn in low for fn in ("sum(", "count(", "avg(", "min(", "max(")) and " limit " in low:
        sql = re.sub(r"\s+limit\s+\d+\s*$", "", sql, flags=re.I)
    return sql

def _fixup_sql(question: str, sql: str) -> str:
    """Auto-correct common mistakes (COUNT→SUM for stock; ensure JOIN for discount math)."""
    s = sql

    # Prefer SUM(stock_quantity) when asking how many/available/in stock
    if re.search(r"(?i)\b(how many|available|in stock)\b", question) and re.search(r"count\s*\(\s*\*\s*\)", s, re.I):
        s = re.sub(r"count\s*\(\s*\*\s*\)", "SUM(`stock_quantity`)", s, flags=re.I)

    # If referencing price/stock/discount from discounts-only query, promote to JOIN
    refs_price_or_stock = re.search(r"\b(price|stock_quantity)\b", s, re.I)
    refs_discount = re.search(r"\bpct_discount\b", s, re.I)
    from_only_discounts = re.search(r"from\s+`?discounts`?\b(?!.*join)", s, re.I)
    if (refs_price_or_stock or refs_discount) and from_only_discounts:
        s = re.sub(
            r"from\s+`?discounts`?\b",
            "FROM `t_shirts` t INNER JOIN `discounts` d ON t.`t_shirt_id`=d.`t_shirt_id`",
            s, flags=re.I
        )
        s = re.sub(r"\b`?price`?\b", "t.`price`", s)
        s = re.sub(r"\b`?stock_quantity`?\b", "t.`stock_quantity`", s)
        s = re.sub(r"\b`?pct_discount`?\b", "d.`pct_discount`", s)

        # if it was selecting only t_shirt_id, rewrite to meaningful top-1 by revenue
        if re.search(r"select\s+`?t_shirt_id`?\s+from", s, re.I):
            s = (
                "SELECT t.`brand`, t.`color`, t.`size`, "
                "t.`price`, t.`stock_quantity`, d.`pct_discount`, "
                "(t.`price` * t.`stock_quantity` * ((100-COALESCE(d.`pct_discount`,0))/100)) AS net_revenue "
                "FROM `t_shirts` t INNER JOIN `discounts` d ON t.`t_shirt_id`=d.`t_shirt_id` "
                "ORDER BY net_revenue DESC, t.`t_shirt_id` ASC LIMIT 1"
            )
    return s

def enforce_enum(sql: str) -> str:
    """Ensure any WHERE brand/color/size='...' values are inside allowed enums."""
    issues = []
    for col, allowed in ENUMS.items():
        for m in re.finditer(rf"`{col}`\s*=\s*'([^']+)'", sql, flags=re.I):
            val = m.group(1)
            if val not in allowed:
                issues.append((col, val))
    if issues:
        raise ValueError(f"Out-of-enum value(s): {issues}")
    return sql

def generate_sql(question: str) -> str:
    """Build prompt (few-shots + live schema + rules) → LLM → cleaned SQL."""
    schema = db.get_table_info()
    raw = LLMChain(llm=llm, prompt=RETAIL_PROMPT).run(
        {"question": question, "schema": schema, "examples": EXAMPLES}
    ).strip()
    sql = _clean_sql(raw)
    sql = _fixup_sql(question, sql)
    sql = enforce_enum(sql)
    return sql

def run_sql(sql: str) -> Union[str, List[Tuple], Tuple]:
    """Execute SQL and return rows (string or list of tuples depending on backend)."""
    return db.run(sql)

def _to_scalar(rows: Union[str, List[Tuple], Tuple]) -> Optional[Union[int, float]]:
    """Return a scalar if it's a 1x1 aggregate; otherwise None."""
    py = rows
    if isinstance(rows, str):
        try:
            py = ast.literal_eval(rows)
        except Exception:
            py = rows

    if isinstance(py, (list, tuple)) and py and isinstance(py[0], (list, tuple)) and len(py[0]) == 1:
        v = py[0][0]
        if isinstance(v, Decimal):
            return int(v) if v == v.to_integral_value() else float(v)
        if isinstance(v, (int, float)):
            return int(v) if float(v).is_integer() else float(v)
        m = re.search(r"[-+]?\d*\.?\d+", str(v))
        if m:
            return float(m.group()) if "." in m.group() else int(m.group())
    if isinstance(rows, str):
        m = re.search(r"[-+]?\d*\.?\d+", rows)
        if m:
            return float(m.group()) if "." in m.group() else int(m.group())
    return None

def _is_groupby(sql: str) -> bool:
    return " group by " in sql.lower()

def ask_retail(user_text: str) -> Dict[str, Any]:
    """End-to-end: normalize → generate SQL → run → parse → return dict."""
    normalized = normalize_retail(user_text)
    sql = generate_sql(normalized)
    rows = run_sql(sql)

    # Empty or no match
    if rows in ("", []) or (isinstance(rows, list) and len(rows) == 0):
        return {
            "question": user_text,
            "normalized": normalized,
            "sql": sql,
            "rows": [],
            "answer": None,
            "note": "No matching rows."
        }

    # GROUP BY / multi-col → return rows only
    if _is_groupby(sql):
        return {
            "question": user_text,
            "normalized": normalized,
            "sql": sql,
            "rows": rows,
            "answer": None
        }

    # scalar aggregate
    scalar = _to_scalar(rows)
    return {
        "question": user_text,
        "normalized": normalized,
        "sql": sql,
        "rows": rows,
        "answer": scalar
    }
