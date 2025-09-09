# 👕 ShirtMart — LLM-based SQL Querying System

This project demonstrates how to use **Large Language Models (LLMs)** to translate **natural language queries** into **SQL commands** for retrieving insights from a retail database (*ShirtMart*).  

It includes a **Streamlit-based chat UI**, an **LLM engine** for SQL generation, integration with **Google Gemini API**, and **few-shot retail SQL examples**.

---

## 🚀 Features

- **Natural Language → SQL**: Ask retail-style questions in plain English.  
- **Streamlit Chat UI**: Conversational interface for interacting with the system.  
- **LLM Integration**: Gemini model backend (via `google.generativeai`).  
- **Few-Shot Prompting**: Retail-focused SQL examples (`few_shots_retail.py`).  
- **Database Connectivity**: Powered by LangChain’s `SQLDatabase` utility.  

---

## 📂 Project Structure

```
ShirtMart-LLM-based-SQL-Querying-System/
│
├── app.py               # Streamlit app: chat interface for ShirtMart
├── engine.py            # Core engine: handles LLM → SQL → DB logic
├── few_shots_retail.py  # Few-shot retail SQL examples
├── gemini_llm.py        # Gemini LLM wrapper for LangChain
├── .gitignore
└── README.md            # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/Shashi-39/ShirtMart-LLM-based-SQL-Querying-System.git
cd ShirtMart-LLM-based-SQL-Querying-System
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:

```
GOOGLE_API_KEY=your_gemini_api_key_here
DB_CONNECTION_STRING=sqlite:///shirtmart.db   # or your DB URI
```

---

## ▶️ Usage

### Run the Streamlit app
```bash
streamlit run app.py
```
Then open the local URL in your browser.  

---

### Example Query

**Input**:  
```
How many Nike White size L are in stock?
```

**Generated SQL**:  
```sql
SELECT SUM(`stock_quantity`)
FROM `t_shirts`
WHERE `brand` = 'Nike' AND `color` = 'White' AND `size` = 'L';
```

---

## 🗄️ Example Database Schema

The system expects a retail-style table like this:

```sql
CREATE TABLE t_shirts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    color TEXT,
    size TEXT,
    price DECIMAL(10,2),
    stock_quantity INTEGER
);
```

Populate it with some sample data:

```sql
INSERT INTO t_shirts (brand, color, size, price, stock_quantity) VALUES
('Nike', 'White', 'L', 999.00, 50),
('Nike', 'Black', 'M', 899.00, 30),
('Adidas', 'Blue', 'S', 799.00, 20);
```

---

## 🛠️ Requirements

- Python 3.9+  
- Streamlit  
- LangChain + LangChain Community Utilities  
- Google Generative AI (`google-generativeai`)  
- python-dotenv  

---

## 📌 Roadmap

- [ ] Expand few-shot examples  
- [ ] Add support for multiple LLM backends (OpenAI, Anthropic, etc.)  
- [ ] Improve SQL validation and error handling  
- [ ] Deploy demo online (e.g., Streamlit Cloud)  

---

## 🤝 Contributing

Pull requests and feature suggestions are welcome!  
Steps:
1. Fork the repo  
2. Create a new branch (`feature/xyz`)  
3. Commit changes and push  
4. Open a PR  

---

 

## 🙏 Acknowledgements

- [LangChain](https://www.langchain.com/) for database utilities and prompts  
- [Google Generative AI](https://ai.google.dev/) for Gemini model integration  
- [Streamlit](https://streamlit.io/) for the interactive chat UI
