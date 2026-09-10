import pandas as pd
import streamlit as st

try:
    from client import (
        APIClientError,
        check_backend_health,
        execute_question,
        get_backend_url,
        submit_clarification,
    )
except ImportError:
    from frontend.client import (
        APIClientError,
        check_backend_health,
        execute_question,
        get_backend_url,
        submit_clarification,
    )

st.set_page_config(
    page_title="Text-to-SQL Clarification Engineer",
    page_icon="🔍",
    layout="wide",
)

# --------------------------------------------------
# Session State Initialization
# --------------------------------------------------
if "question" not in st.session_state:
    st.session_state.question = ""
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None
if "backend_healthy" not in st.session_state:
    st.session_state.backend_healthy = check_backend_health()

# --------------------------------------------------
# Sidebar: Status & Examples
# --------------------------------------------------
with st.sidebar:
    st.markdown("### Text-to-SQL Clarification Engineer")
    st.caption(f"Backend: `{get_backend_url()}`")

    st.markdown("#### Backend Status")
    if st.session_state.backend_healthy:
        st.success("● Connected")
    else:
        st.error("● Unavailable")
        if st.button("Retry Connection"):
            st.session_state.backend_healthy = check_backend_health()
            st.rerun()

    st.markdown("---")
    st.markdown("#### Example Questions")

    example_questions = [
        "What is the total revenue?",
        "Show customers from India",
        "Show revenue by customer",
        "Show revenue by product",
        "Show revenue by category",
        "How many units were sold by product?",
        "Show top 3 customers by revenue",
        "Show top 5 products",
    ]

    for ex in example_questions:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.question = ex
            st.session_state.current_result = None
            st.session_state.pending_clarification = None
            st.rerun()

# --------------------------------------------------
# Main UI Layout
# --------------------------------------------------
st.title("Text-to-SQL Clarification Engineer")
st.markdown("Ask questions about your data in natural language.")

# Question input area
question_input = st.text_area(
    "Enter your question about the database:",
    value=st.session_state.question,
    placeholder="e.g. Show revenue by customer",
    height=100,
    key="main_question_area",
)

# Run Query Button
col_btn, _ = st.columns([1, 4])
with col_btn:
    run_clicked = st.button("Run Query", type="primary", use_container_width=True)

if run_clicked:
    st.session_state.question = question_input.strip()
    if not st.session_state.question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking and querying the database..."):
            try:
                result = execute_question(st.session_state.question)
                st.session_state.backend_healthy = True
                st.session_state.current_result = result
                if not result.get("resolved", True):
                    st.session_state.pending_clarification = result
                else:
                    st.session_state.pending_clarification = None
            except APIClientError as err:
                st.session_state.current_result = None
                st.session_state.pending_clarification = None
                st.error(f"Query Failed: {err.message}")

# --------------------------------------------------
# Display Result or Clarification
# --------------------------------------------------
if st.session_state.pending_clarification:
    clarification_data = st.session_state.pending_clarification
    analysis_id = clarification_data.get("analysis_id")
    clarification = clarification_data.get("clarification", {})
    clarification_q = clarification.get(
        "question",
        "Please provide more specific details to resolve your query.",
    )

    st.markdown("---")
    st.markdown("### Clarification Required")
    st.info(f"**I need one more detail:**\n\n{clarification_q}")

    col_ans, col_sub = st.columns([3, 1])
    with col_ans:
        ans_input = st.text_input(
            "Your answer:",
            placeholder="e.g. total revenue, units, or orders",
            key="clarification_answer_input",
        )
    with col_sub:
        st.write("")  # Vertical spacing
        st.write("")
        submit_ans_clicked = st.button(
            "Submit Clarification",
            key="submit_clarification_btn",
            use_container_width=True,
        )

    if submit_ans_clicked:
        if not ans_input.strip():
            st.warning("Please enter a clarification answer.")
        elif not analysis_id:
            st.error("Analysis ID missing. Please re-run your query.")
        else:
            with st.spinner("Applying clarification and executing query..."):
                try:
                    updated_result = submit_clarification(
                        analysis_id, ans_input.strip()
                    )
                    st.session_state.current_result = updated_result
                    if updated_result.get("resolved", True):
                        st.session_state.pending_clarification = None
                    else:
                        st.session_state.pending_clarification = updated_result
                    st.rerun()
                except APIClientError as err:
                    st.error(f"Clarification Failed: {err.message}")

elif st.session_state.current_result:
    res = st.session_state.current_result
    execution = res.get("execution")
    sql = res.get("sql")

    st.markdown("---")
    st.markdown("### Query Result")

    if execution:
        columns = execution.get("columns", [])
        rows = execution.get("rows", [])

        if not rows:
            st.info("No matching records found in the database.")
        else:
            # Check for single aggregate scalar result
            if len(rows) == 1 and len(columns) == 1:
                metric_name = columns[0].replace("_", " ").title()
                val = rows[0][0]
                st.metric(label=metric_name, value=str(val))

            # Render Table
            try:
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df, use_container_width=True)

                # Optional simple bar chart if 2 columns: 1 categorical, 1 numeric
                if len(columns) == 2 and len(rows) > 1:
                    cat_col, num_col = columns[0], columns[1]
                    numeric_series = pd.to_numeric(df[num_col], errors="coerce")
                    if not numeric_series.isna().all():
                        chart_df = df.copy()
                        chart_df[num_col] = numeric_series
                        valid_chart = chart_df.dropna(subset=[num_col])
                        if not valid_chart.empty:
                            st.bar_chart(valid_chart.set_index(cat_col)[[num_col]])
            except (ValueError, TypeError, KeyError):
                st.table(rows)

            if execution.get("answer"):
                with st.expander("Summary Text", expanded=False):
                    st.text(execution["answer"])

    if sql:
        st.markdown("#### Generated SQL")
        st.code(sql, language="sql")
