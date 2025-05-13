import streamlit as st
import pandas as pd
import json
import os

from utils import (
    save_categories,
    load_transactions,
    add_keyword_to_category,
    statement_summary,
    show_recurring_transactions,
    download_csv,
    generate_pdf_report,
    setup_budget,
    visualize_expenses
)

st.set_page_config(page_title="ClearSpend", layout="wide")

category_file = "categories.json"

# Load categories from the session or file
if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": [],
        "Groceries": ["tesco", "lidl", "aldi", "dealz", "supervalu", "eurogiant", "mr price"],
        "Electricity": ["sseairtricity", "electric ireland"],
        "Transportation": ["uber", "rail", "bus", "leap card"],
        "Dining": ["sano"],     
        "Entertainment": ["netflix", "spotify"],
        "Shopping": ["amazon"],
        "India Home": ["wise"],
        "Phone Bill": ["gomo"]
    }

if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)


def main():
    # Title and Description
    st.markdown(
    """
    <div style="text-align: center; padding: 30px 0 20px 0;">
        <h1 style="font-size: 3em; margin-bottom: 0;">ClearSpend</h1>
        <p style="font-size: 1.2em; color: #666; margin-top: 0;">Your Finances, Clearly Visualized.</p>
        <p style="font-size: 1em; color: #888; max-width: 600px; margin: auto;">
            Effortlessly analyze your bank statements, categorize your expenses, and uncover smart insights to better manage your money — all in one clean, visual dashboard.
        </p>
    </div>
    """,
    unsafe_allow_html=True
    )

    # Upload file
    upload_file = st.file_uploader("Upload your account statement (CSV)", type=["csv"])

    if upload_file is not None:
        # Dataframe
        df = load_transactions(upload_file)
        if df is not None:
            # Convert 'Debit' and 'Credit' columns to numeric
            df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')
            df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce')

            debits_df = df[df['Debit'].notna() & (df['Debit'] != 0)].copy()
            credits_df = df[df['Credit'].notna() & (df['Credit'] != 0)].copy()

            st.session_state.debits_df = debits_df.copy()
            st.session_state.credits_df = credits_df.copy()

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
            # Expenses / Debits Tab
            with tab1:
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()  # Save new category to the JSON file
                        st.rerun()
                        st.success(f"Category '{new_category}' added successfully!")

                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[["Date", "Details", "Debit", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Debit": st.column_config.NumberColumn("Amount", format="%.2f EUR"),
                        "Category": st.column_config.SelectboxColumn(
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )                
                # Save Changes button
                save_button = st.button("Save Changes", type="primary")

                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.debits_df.at[idx, "Category"]:
                            continue
                        details = row["Details"]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)

                # Category wise expenses
                st.subheader("Expense Summary by Category")
                category_totals = st.session_state.debits_df.groupby("Category")["Debit"].sum().reset_index()
                category_totals = category_totals.sort_values(by="Debit", ascending=False)
                st.dataframe(
                    category_totals,
                    column_config={
                        "Debit": st.column_config.NumberColumn("Amount", format="%.2f EUR")
                    }, 
                    use_container_width=True,
                    hide_index=True
                )

                # Visualize expenses
                st.subheader("Visualize Your Spending")
                st.write("Explore your spending patterns with these visualizations.")
                visualize_expenses(st.session_state.debits_df)
                
                # Budgeting
                setup_budget(df)
    
                # Recurring expense        
                show_recurring_transactions(df)
                
            # Payments / Credits Tab
            with tab2:
                st.subheader("Payments Summary")
                total_payments = credits_df["Credit"].sum()
                st.metric("Total Payments", f'{total_payments:,.2f} EUR')
                st.dataframe(
                    credits_df[["Date", "Details", "Credit", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Credit": st.column_config.NumberColumn("Amount", format="%.2f EUR")
                    }, 
                    use_container_width=True,
                    hide_index=True
                )

            # Statement Summary
            st.subheader("Monthly Transaction Details")
            statement_summary(df)
                                 
            # PDF and CSV report download buttons
            st.markdown("<h4 style='text-align: center;'>Download Financial Report</h2>", unsafe_allow_html=True)
            col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])
            with col2:               
                download_csv(df)  # CSV report
            with col4:
                pdf_path = generate_pdf_report(df) 
                st.download_button(
                        label="Download PDF", 
                        data=open(pdf_path, "rb").read(), 
                        file_name="account_statement.pdf", 
                        mime="application/pdf"
                )  # PDF report
                os.remove(pdf_path)  # Clean up the temporary file

if __name__ == "__main__":
    main()