# Clearspend

**Clearspend** is a **Python**, **Streamlit**, **Pandas**, and **Plotly**-based financial dashboard that lets you upload and analyze your bank statements. Gain insights into your expenses, track recurring payments, set budgets and export visual reports—all from a simple web interface.

## ⚙️ Built With

- **Python** – Core language for backend logic  
- **Streamlit** – Web framework for building interactive dashboards  
- **Pandas** – Data processing and analysis  
- **Plotly** – Interactive visualizations  

## 📦 Features

- 📁 **Upload Bank Statements**  
  Upload your bank CSV file for analysis.

- 🔍 **Categorize Transactions**  
  Automatically categorize and organize debits and credits into separate tabs.

- 📂 **Expense Summary**  
  Display total spending per category.

- 📊 **Interactive Visualizations**  
  Use Plotly to explore your spending through dynamic graphs and charts.

- 🔁 **Recurring Payments**  
  Detect and display repeating transactions like rent or groceries.

- 💰 **Budgets**  
  Define monthly budgets and identify when limits are reached.

- 🧾 **Export Reports**  
  Download your data insights as **CSV** and **PDF** files.

## 📄 CSV Upload Format

Your bank statement should be a CSV with the following structure:

| Date       | Details        | Debit  | Credit | Balance |
|------------|----------------|--------|--------|---------|
| 10-Dec-24  | Grocery Store  | 20.00  |        |         |
| 10-Dec-24  | Salary         |        |2000.00 |         |

- `date`: Transaction date (`DD-MMM-YY`)  
- `details`: Transaction description  
- `debit`: Expense amount (optional)  
- `credit`: Income amount (optional)
- `balance`: Balance amount (optional)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/clearspend.git
cd clearspend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run main.py
```

Then open your browser and go to:
http://localhost:8501