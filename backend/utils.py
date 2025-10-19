import pandas as pd #type: ignore

CATEGORY_RULES = {
    "Shopping": ["amazon", "flipkart", "myntra", "shopping", "grocery", "supermarket", "mall"],
    "Transport": ["uber", "ola", "metro", "bus", "train", "taxi"],
    "Entertainment": ["netflix", "prime", "spotify", "movie", "cinema", "tickets"],
    "Food": ["restaurant", "cafe", "dominos", "burger", "pizza"],
    "Housing": ["rent", "flat", "apartment", "house"],
    "Income": ["salary", "bonus", "deposit", "payroll"]
}

ADVICE_TEMPLATES = {
    "Shopping": "You spent {pct:.1f}% of your income on shopping. {tip}",
    "Food": "Food costs are {pct:.1f}% of your income. {tip}",
    "Housing": "Housing/rent takes {pct:.1f}% of income. {tip}",
    "Transport": "Transport spending is {pct:.1f}% of income. {tip}",
    "Entertainment": "Entertainment is {pct:.1f}% of income. {tip}",
    "Income": "Your income is {amount}. Keep track of savings and budget.",
    "Others": "Other expenses total {pct:.1f}% of income. {tip}"
}

USER_BUDGET = {
    "Shopping": 5000,
    "Food": 3000,
    "Transport": 2000,
    "Entertainment": 1000,
    "Housing": 15000
}

def categorize_transaction(description):
    desc = str(description).lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(k in desc for k in keywords):
            return category
    return "Others"

def generate_financial_advice(df):
    df["Category"] = df["Description"].apply(categorize_transaction)
    category_totals = df.groupby("Category")["Amount"].sum().to_dict()
    income = category_totals.get("Income", 0)
    advice_lines = []

    if income == 0:
        advice_lines.append("No income data found. Track your salary for accurate advice.")
    else:
        for category, total in category_totals.items():
            if category == "Income":
                advice_lines.append(f"Your total income is {total}. Keep a portion for savings!")
                continue
            pct = (total/income)*100
            if pct > 20:
                tip = "Consider reducing spending in this category."
            elif pct > 10:
                tip = "Good control, but watch for overspending."
            else:
                tip = "Excellent management in this area."
            template = ADVICE_TEMPLATES.get(category, ADVICE_TEMPLATES["Others"])
            advice_lines.append(template.format(pct=pct, tip=tip, amount=total))

        # Savings advice
        total_expenses = sum([v for k, v in category_totals.items() if k != "Income"])
        savings_pct = ((income - total_expenses)/income)*100 if income else 0
        if savings_pct < 10:
            advice_lines.append("Your savings are low. Try to reduce discretionary spending.")
        elif savings_pct < 30:
            advice_lines.append("Savings are moderate. Good job, but you can save more!")
        else:
            advice_lines.append("Excellent! You are saving a healthy portion of your income.")

    return df, "\n".join(advice_lines), category_totals

def budget_summary(category_totals):
    USER_BUDGET = {
        "Food": 5000,
        "Rent": 10000,
        "Entertainment": 3000,
        "Transport": 2000,
        "Shopping": 4000,
        "Health": 2500,
        "Bills": 3500,
        "Savings": 5000
    }

    summary = {}
    for cat, spent in category_totals.items():
        budget = USER_BUDGET.get(cat, None)
        if budget:
            pct = (spent / budget) * 100
            if pct > 100:
                status = "Over budget!"
            elif pct > 80:
                status = "Near budget limit"
            else:
                status = "Within budget"
            summary[cat] = {
                "spent": round(spent, 2),
                "budget": budget,
                "pct": round(pct, 2),
                "status": status
            }
        else:
            summary[cat] = {
                "spent": round(spent, 2),
                "budget": "N/A",
                "pct": None,
                "status": "No budget set"
            }
    return summary


def monthly_summary(df):
    income = df[df["Category"]=="Income"]["Amount"].sum()
    expenses = df[df["Type"]=="Expense"]["Amount"].sum()
    savings = income - expenses
    savings_pct = (savings / income * 100) if income else 0
    return {"income": income, "expenses": expenses, "savings": savings, "savings_pct": savings_pct}
def top_expenses(df, top_n=5):
    # Filter only expenses
    expenses_df = df[df["Type"] == "Expense"].copy()
    # Keep original order, no sorting
    top_df = expenses_df.head(top_n)
    # Return as list of dicts
    top_list = top_df[["Date", "Description", "Amount", "Category"]].to_dict(orient="records")
    
    # Category-wise % of total expenses
    category_totals = expenses_df.groupby("Category")["Amount"].sum()
    total_expenses = expenses_df["Amount"].sum()
    category_pct = (category_totals / total_expenses * 100).round(1).to_dict()

    return top_list, category_pct

