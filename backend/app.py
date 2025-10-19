from flask import Flask, request, jsonify, send_from_directory #type: ignore
import pandas as pd #type: ignore
import os
from utils import categorize_transaction, generate_financial_advice, budget_summary, monthly_summary, top_expenses
from flask_cors import CORS #type: ignore

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data"))
os.makedirs(DATA_DIR, exist_ok=True)

SAMPLE_FILE = os.path.join(DATA_DIR, "sample_transactions.csv")
UPLOAD_FILE = os.path.join(DATA_DIR, "uploaded_transactions.csv")

@app.route("/")
def home():
    return send_from_directory("../frontend", "index.html")

@app.route("/upload", methods=["POST"])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    try:
        df = pd.read_csv(file)
        # Categorize immediately
        df["Category"] = df["Description"].apply(categorize_transaction)
        df.to_csv(UPLOAD_FILE, index=False)
        return jsonify({
            "message": "File uploaded successfully",
            "transactions": df.to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"error": "Upload failed: " + str(e)}), 500


def convert_to_python(obj):
    if isinstance(obj, dict):
        return {k: convert_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_python(i) for i in obj]
    elif hasattr(obj, "item"):  # numpy numbers
        return obj.item()
    else:
        return obj
@app.route("/recommend", methods=["GET"])
def recommend():
    try:
        csv_path = UPLOAD_FILE if os.path.exists(UPLOAD_FILE) else SAMPLE_FILE
        df = pd.read_csv(csv_path)
        df, advice_text, category_totals = generate_financial_advice(df)
        budget_info = budget_summary(category_totals)
        monthly_info = monthly_summary(df)

        # 🔹 Top 5 expenses
        top_expenses = df[df['Type'] == "Expense"].sort_values(by="Amount", ascending=False).head(5)
        top_expenses_list = top_expenses.to_dict(orient="records")

        # 🔹 Category Percentages
        total_expense = sum(category_totals.get(cat, 0) for cat in category_totals if cat != "Income")
        category_pct = {
            cat: round((amt / total_expense) * 100, 1)
            for cat, amt in category_totals.items() if cat != "Income"
        }

        # ✅ Monthly Trends (auto-generated)
        # Summarize by Month-Year
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Month"] = df["Date"].dt.strftime("%B %Y")
        monthly_trends = {}
        for month, group in df.groupby("Month"):
            income = group.loc[group["Type"] == "Income", "Amount"].sum()
            expenses = group.loc[group["Type"] == "Expense", "Amount"].sum()
            savings = income - expenses
            monthly_trends[month] = {
                "income": round(float(income), 2),
                "expenses": round(float(expenses), 2),
                "savings": round(float(savings), 2)
            }

        # ✅ Financial Goals (simple auto estimation)
        # You can later make this user-defined from dashboard
        total_income = df.loc[df["Type"] == "Income", "Amount"].sum()
        total_expense = df.loc[df["Type"] == "Expense", "Amount"].sum()
        current_savings = total_income - total_expense
        goals_status = {
            "Emergency Fund": {"current": round(current_savings * 0.3, 2), "target": 10000},
            "Vacation Fund": {"current": round(current_savings * 0.2, 2), "target": 5000},
            "Investment Goal": {"current": round(current_savings * 0.5, 2), "target": 20000}
        }

        # 🔹 Convert NumPy types to native Python types
        def convert_to_python(obj):
            if isinstance(obj, dict):
                return {k: convert_to_python(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_python(i) for i in obj]
            elif hasattr(obj, "item"):
                return obj.item()
            else:
                return obj

        category_totals = convert_to_python(category_totals)
        budget_info = convert_to_python(budget_info)
        monthly_info = convert_to_python(monthly_info)
        top_expenses_list = convert_to_python(top_expenses_list)
        category_pct = convert_to_python(category_pct)
        monthly_trends = convert_to_python(monthly_trends)
        goals_status = convert_to_python(goals_status)

        # ✅ Return all sections including new ones
        return jsonify({
            "advice": advice_text,
            "category_totals": category_totals,
            "budget_info": budget_info,
            "monthly_summary": monthly_info,
            "top_expenses": top_expenses_list,
            "category_pct": category_pct,
            "monthly_trends": monthly_trends,
            "goals_status": goals_status
        })

    except Exception as e:
        return jsonify({
            "advice": "Error generating advice: " + str(e),
            "category_totals": {},
            "budget_info": {},
            "monthly_summary": {},
            "top_expenses": [],
            "category_pct": {},
            "monthly_trends": {},
            "goals_status": {}
        }), 500

@app.route("/insights", methods=["GET"])
def insights():
    try:
        csv_path = UPLOAD_FILE if os.path.exists(UPLOAD_FILE) else SAMPLE_FILE
        df = pd.read_csv(csv_path)
        df["Category"] = df["Description"].apply(categorize_transaction)
        top_list, category_pct = top_expenses(df)
        return jsonify({
            "top_expenses": top_list,
            "category_pct": category_pct
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
