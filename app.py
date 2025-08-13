# app.py
# Streamlit chat for the LLM → SQL pipeline.

import streamlit as st
from engine import ask_retail

st.set_page_config(page_title="Shirt Mart — Cashier Chat (LLM)", page_icon="👕", layout="centered")
st.title(" Shirt Mart — Cashier Chat (LLM)")

# --- Chat session state ---
if "chat_active" not in st.session_state:
    st.session_state.chat_active = False
if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns(2)
with col1:
    if st.button(" Start Chat", use_container_width=True):
        st.session_state.chat_active = True
with col2:
    if st.button(" Stop Chat", use_container_width=True):
        st.session_state.chat_active = False

st.caption("Ask things like: *how many nike white large tees are available?*")

# --- Display history ---
for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

# --- Input box (disabled when stopped) ---
prompt = st.chat_input("Type your question…", disabled=not st.session_state.chat_active)

if prompt and st.session_state.chat_active:
    # show user msg
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # run pipeline
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            res = ask_retail(prompt)

        # show SQL + result
        st.code(res["sql"], language="sql")
        if res.get("answer") is not None:
            st.success(f"Answer: {res['answer']}")
        elif res.get("note"):
            st.info(res["note"])
        else:
            st.write("Rows:", res["rows"])

        # save assistant message summary (just the answer or rows)
        if res.get("answer") is not None:
            summary = f"**Answer:** {res['answer']}\n\n```sql\n{res['sql']}\n```"
        elif res.get("note"):
            summary = f"{res['note']}\n\n```sql\n{res['sql']}\n```"
        else:
            summary = f"Rows: {res['rows']}\n\n```sql\n{res['sql']}\n```"
        st.session_state.messages.append(("assistant", summary))
