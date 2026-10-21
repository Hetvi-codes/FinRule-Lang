TEMPLATES = [
    {
        "id": "saas-growth",
        "name": "SaaS MRR Growth & Churn Projection",
        "category": "SaaS & Subscription",
        "description": "Predicts how much money a subscription business makes over 24 months. Solves: How will customer signups, cancellations (churn), and monthly expenses affect our future profit?",
        "source_code": """// FinRule: SaaS Recurring Revenue & Churn Projection
model "SaaS Growth Engine" {
  starting_mrr = 75000
  monthly_growth = 0.055
  churn = 0.02
  cogs_rate = 0.22
  opex = 38000

  for month in 1 to 24 {
    mrr = starting_mrr * (1 + monthly_growth - churn) ^ month
    revenue = mrr
    cogs = revenue * cogs_rate
    gross_profit = revenue - cogs
    net_profit = gross_profit - opex

    output month, mrr, revenue, cogs, gross_profit, net_profit
  }
}

scenario "Aggressive Growth" {
  monthly_growth = 0.09
  churn = 0.015
  opex = 45000
}

scenario "Recession Stress Test" {
  monthly_growth = 0.02
  churn = 0.045
  opex = 32000
}
"""
    },
    {
        "id": "loan-amortization",
        "name": "Commercial Loan Amortization Schedule",
        "category": "Debt & Banking",
        "description": "Calculates monthly loan repayment (EMI) over 36 months. Solves: How much of each monthly payment goes to paying off the actual loan vs paying interest to the bank?",
        "source_code": """// FinRule: Commercial Term Loan Amortization Schedule
model "Commercial Debt Service" {
  loan_amount = 500000
  annual_rate = 0.075
  loan_term_months = 36
  monthly_rate = annual_rate / 12

  // Built-in PMT function calculates fixed monthly payment
  monthly_payment = PMT(monthly_rate, loan_term_months, loan_amount)
  balance = loan_amount

  for month in 1 to 36 {
    interest_payment = balance * monthly_rate
    principal_payment = monthly_payment - interest_payment
    balance = balance - principal_payment

    output month, monthly_payment, principal_payment, interest_payment, balance
  }
}

scenario "Refinanced Low Rate" {
  annual_rate = 0.055
}

scenario "High Rate Environment" {
  annual_rate = 0.105
}
"""
    },
    {
        "id": "startup-runway",
        "name": "Startup Cash Runway & Burn Rate Forecast",
        "category": "Startup Finance",
        "description": "Forecasts when a startup will run out of cash over 18 months. Solves: How many months of money do we have left as hiring and team costs grow each month?",
        "source_code": """// FinRule: Startup Runway & Cash Burn Forecast
model "Seed Runway Planner" {
  starting_cash = 1200000
  monthly_burn_base = 45000
  hiring_expansion_rate = 3500
  revenue_starting = 8000
  revenue_mom_growth = 0.08

  cash_balance = starting_cash
  current_revenue = revenue_starting

  for month in 1 to 18 {
    current_revenue = current_revenue * (1 + revenue_mom_growth)
    total_expenses = monthly_burn_base + (hiring_expansion_rate * month)
    net_burn = total_expenses - current_revenue
    cash_balance = cash_balance - net_burn
    runway_months_remaining = cash_balance / net_burn

    output month, current_revenue, total_expenses, net_burn, cash_balance, runway_months_remaining
  }
}

scenario "Conservative Lean Burn" {
  hiring_expansion_rate = 1500
  monthly_burn_base = 38000
}

scenario "Fast Growth Hiring" {
  hiring_expansion_rate = 6000
  revenue_mom_growth = 0.12
}
"""
    },
    {
        "id": "unit-economics",
        "name": "Unit Economics & Customer Lifetime Value (LTV / CAC)",
        "category": "Unit Economics",
        "description": "Evaluates whether you make a profit on each customer. Solves: Is the money we spend to get a customer (CAC) lower than the total money they will spend with us (LTV)?",
        "source_code": """// FinRule: Unit Economics & Cohort Payback Analysis
model "Unit Economics Model" {
  ad_spend = 25000
  new_customers = 250
  cac = ad_spend / new_customers
  arpu = 85
  gross_margin_rate = 0.78
  monthly_churn = 0.035

  customer_lifetime_months = 1 / monthly_churn
  ltv = arpu * gross_margin_rate * customer_lifetime_months
  ltv_cac_ratio = ltv / cac
  payback_period_months = cac / (arpu * gross_margin_rate)

  for cohort in 1 to 12 {
    cohort_revenue = new_customers * arpu * (1 - monthly_churn) ^ cohort
    cohort_margin = cohort_revenue * gross_margin_rate

    output cohort, cac, ltv, ltv_cac_ratio, cohort_revenue, cohort_margin
  }
}

scenario "Optimized Paid Ads" {
  new_customers = 340
  monthly_churn = 0.025
}
"""
    },
    {
        "id": "capex-depreciation",
        "name": "Capex & Asset Depreciation Schedule",
        "category": "Corporate Finance",
        "description": "Tracks how machines, computers, or assets lose value over 5 years. Solves: What is the equipment worth each month and how much tax do we save from depreciation?",
        "source_code": """// FinRule: Capital Expenditure & Depreciation Schedule
model "Data Center Hardware Capex" {
  asset_cost = 600000
  salvage_value = 60000
  useful_life_months = 60
  tax_rate = 0.25

  depreciable_base = asset_cost - salvage_value
  monthly_depreciation = depreciable_base / useful_life_months
  accumulated_depreciation = 0
  net_book_value = asset_cost

  for month in 1 to 60 {
    accumulated_depreciation = accumulated_depreciation + monthly_depreciation
    net_book_value = asset_cost - accumulated_depreciation
    tax_shield = monthly_depreciation * tax_rate

    output month, monthly_depreciation, accumulated_depreciation, net_book_value, tax_shield
  }
}

scenario "Accelerated 36-Month Useful Life" {
  useful_life_months = 36
  salvage_value = 30000
}
"""
    }
]
