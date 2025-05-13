import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import math
from fpdf import FPDF
import tempfile

category_file = "categories.json"

# Save categories to a JSON file
def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)

# Categorize transactions based on keywords
def categorize_transaction(df):
    # By default, all transactions are categorized as "Uncategorized"
    df["Category"] = "Uncategorized"
    # Set Credit category to "Income / Receivables"
    df.loc[df['Credit'].notna() & (df['Credit'] != 0), 'Category'] = "Income / Receivables"
    # print(st.session_state.categories.items())
    # Setting categories based on keywords
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue       
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if any(keyword in details for keyword in lowered_keywords):
                df.at[idx, "Category"] = category    
    return df

# Loading transactions from a CSV file
def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        # Ensure proper conversion of numeric columns
        df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')
        df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce')
        df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce')
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
        return categorize_transaction(df)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# Save categories to session state
def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False

# Display Account Summary
def statement_summary(df):
    # Calculating total expense, total credit, net savings, top category
    # Ensure Debit, Credit is numeric in case of string values
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce')

    total_expense = df['Debit'].sum()
    total_credit = df['Credit'].sum()
    net_savings = total_credit - total_expense
    
    # Filter rows with actual debit values
    debit_rows = df[df['Debit'].notna() & (df['Debit'] != 0)]
    top_category = debit_rows.groupby('Category')['Debit'].sum().idxmax()
    top_category_amount = debit_rows[debit_rows['Category'] == top_category]['Debit'].sum()

    # Calculating number of days without any transaction
    df['Date'] = pd.to_datetime(df['Date'])
    spent_dates = df[df['Debit'].notna() & (df['Debit'] != 0)]['Date'].dt.date.unique()
    all_dates = pd.date_range(df['Date'].min(), df['Date'].max()).date
    no_spend_days = set(all_dates) - set(spent_dates)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Credit", f'{total_credit:,.2f} EUR')
    col2.metric("Total Expense", f'{total_expense:,.2f} EUR')    
    col3.metric("Net Savings", f'{net_savings:,.2f} EUR')

    col4, col5, col6 = st.columns(3)
    col4.metric("Top Spending Category", f'{top_category} ({top_category_amount:,.2f} EUR)')
    col6.metric("No-Spend Days", f'{len(no_spend_days)} / {len(all_dates)} days')

# Visualizations (Pie, Bar, Line, Scatter)
def plot_pie_chart(df):
    color_sequence = px.colors.qualitative.Dark24
    fig_pie = px.pie(
        df, 
        values='Amount', 
        names='Category', 
        title='Pie Chart',
        color_discrete_sequence=color_sequence
    )
    return fig_pie

def plot_bar_chart(df):
    color_sequence = px.colors.qualitative.Dark24 
    fig_bar = px.bar(
        df, 
        x='Category', 
        y='Amount', 
        title="Bar Chart",
        color_discrete_sequence=color_sequence
    )
    return fig_bar

def plot_line_chart(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')
    daily_expense = df[df['Debit'].notna() & (df['Debit'] != 0)].groupby(df['Date'].dt.date)['Debit'].sum().reset_index()
    daily_expense.columns = ['Date', 'Total Expenses']

    fig_line = px.line(
        daily_expense, 
        x='Date', 
        y='Total Expenses', 
        title='Daily Expense Trend'
    )
    return fig_line

def plot_scatter_chart(df):
    color_sequence = px.colors.qualitative.Dark24
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.rename(columns={"Debit": "Amount"})
    fig_scatter = px.scatter(
        df, 
        x='Date', 
        y='Amount', 
        color='Category', 
        title='Scatter Plot of Transactions',
        color_discrete_sequence=color_sequence
    )
    return fig_scatter

# Visualize Expenses
def visualize_expenses(df):
    category_totals = df.groupby("Category")["Debit"].sum().reset_index()
    category_totals = category_totals.sort_values(by="Debit", ascending=False)
    category_totals = category_totals.rename(columns={"Debit": "Amount"})

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    with col1:
        fig_pie = plot_pie_chart(category_totals)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        fig_bar = plot_bar_chart(category_totals)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col3:
        fig_line = plot_line_chart(df)
        st.plotly_chart(fig_line, use_container_width=True)
    with col4:
        fig_scatter = plot_scatter_chart(df)
        st.plotly_chart(fig_scatter, use_container_width=True)

# Budgeting
def setup_budget(df):
    st.sidebar.header("Set Budget per Category")
    budget = {}
    for cat in df['Category'].unique():
        if cat != "Income / Receivables" and cat != "Uncategorized":
            budget[cat] = st.sidebar.number_input(f"Budget for {cat}", value=1000)
                    
    st.subheader("Budget Comparison")
                
    for cat in df['Category'].unique():
        if cat != "Income / Receivables" and cat != "Uncategorized":
            spent = df[(df['Category'] == cat) & (df['Debit'].notna()) & (df['Debit'] != 0)]['Debit'].sum()

            limit = budget.get(cat, 0)
            percent = (spent / limit) * 100 if limit else 0
            percent = min(math.floor(percent), 100)

            st.write(f"**{cat}**: {spent:.2f} EUR of {limit} EUR")
            st.progress(min(math.floor(percent), 100), text=f"{percent}% spent")

            if spent > limit:
                st.error(f"Over Budget by {spent - limit:.2f} EUR")
            elif spent == limit:
                st.warning("Budget exactly met.")
            else:
                st.success(f"Remaining: {limit - spent:.2f} EUR")

# Recurring Payments
def show_recurring_transactions(df):
    st.subheader("Recurring Payments")
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')

    recurring = df[df['Debit'].notna() & (df['Debit'] != 0)].groupby('Details')['Debit'].agg(['count']).reset_index()
    recurring = recurring[recurring['count'] >= 3]
    recurring.rename(columns={'count': 'Occurrences'}, inplace=True)
    if not recurring.empty:
        st.dataframe(recurring.sort_values(by='Occurrences', ascending=False, ignore_index=True), use_container_width=False)
    else:
        st.info("No recurring payments detected.")

# Download CSV
def download_csv(df):
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "account_statement.csv", "text/csv")

# Check remaining space in PDF
def check_remaining_space(pdf, chart_height):
    remaining_space = pdf.h - pdf.get_y()
    if remaining_space < chart_height:
        pdf.add_page()

# Generate PDF report
def generate_pdf_report(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Account Summary from ClearSpend", ln=True, align='C')
    pdf.ln(10)

    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce')

    total_expense = df['Debit'].sum()
    total_income = df['Credit'].sum()
    net_savings = total_income - total_expense
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(200, 10, "Account Summary", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Total Transactions: {len(df)}", ln=True)
    pdf.cell(200, 10, f"Total Credit: {total_income:,.2f} EUR", ln=True)
    pdf.cell(200, 10, f"Total Expense: {total_expense:,.2f} EUR", ln=True)
    pdf.cell(200, 10, f"Net Savings: {net_savings:,.2f} EUR", ln=True)
    pdf.ln(5)

    category_totals = df[df['Debit'].notna() & (df['Debit'] != 0)].groupby("Category")["Debit"].sum().reset_index()
    category_totals = category_totals.sort_values(by="Debit", ascending=False)
    category_totals = category_totals.rename(columns={"Debit": "Amount"})

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Expense by Category", ln=True)
    pdf.set_font("Arial", size=12)
    for _, row in category_totals.iterrows():
        cat = row['Category']
        amt = row['Amount']
        pdf.cell(200, 10, f"{cat}: {amt:,.2f} EUR", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(200, 10, "Visual Representation of Expenses", ln=True)

    pie_fig = plot_pie_chart(category_totals)  
    pie_path = os.path.join(tempfile.gettempdir(), "pie_chart.png")
    pie_fig.write_image(pie_path, format="png")

    bar_fig = plot_bar_chart(category_totals)
    bar_path = os.path.join(tempfile.gettempdir(), "bar_chart.png")
    bar_fig.write_image(bar_path, format="png")

    line_fig = plot_line_chart(df)
    line_path = os.path.join(tempfile.gettempdir(), "line_chart.png")
    line_fig.write_image(line_path, format="png")

    scatter_fig = plot_scatter_chart(df)
    scatter_path = os.path.join(tempfile.gettempdir(), "scatter_chart.png")
    scatter_fig.write_image(scatter_path, format="png")

    chart_width = 150
    chart_height = 100

    check_remaining_space(pdf, chart_height)
    pdf.image(pie_path, x=10, y=pdf.get_y() + 5, w=chart_width, h=chart_height)
    pdf.ln(chart_height + 10)

    check_remaining_space(pdf, chart_height)
    pdf.image(bar_path, x=10, y=pdf.get_y() + 5, w=chart_width, h=chart_height)
    pdf.ln(chart_height + 10)

    check_remaining_space(pdf, chart_height)
    pdf.image(line_path, x=10, y=pdf.get_y() + 5, w=chart_width, h=chart_height)
    pdf.ln(chart_height + 10)

    check_remaining_space(pdf, chart_height)
    pdf.image(scatter_path, x=10, y=pdf.get_y() + 5, w=chart_width, h=chart_height)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        # Cleanup temporary chart images
        os.remove(pie_path)
        os.remove(bar_path)
        os.remove(line_path)
        os.remove(scatter_path)
        return tmp.name