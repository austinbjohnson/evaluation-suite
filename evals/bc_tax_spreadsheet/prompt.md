You are a tax calculation expert for Canadian sole proprietors. Your task is to create a working spreadsheet that calculates federal and BC provincial income taxes.

**Requirements:**
- Generate a CSV format spreadsheet (you can describe it as text showing the structure)
- Use FORMULAS, not hardcoded values
- Calculate both federal and BC provincial taxes
- Show your work with clear cell labels

**Tax Scenario:**
- Year: {{ year }}
- Business type: {{ business_type }} (Vancouver, BC)
- Total taxable income: ${{ income }}

**Federal Tax Brackets (2025):**
- $0 to $55,867: 14% (Note: reduced from 15% mid-year 2025)
- $55,867 to $111,733: 20.5%
- $111,733 to $173,205: 26%
- $173,205 to $246,752: 29%
- Over $246,752: 33%
- Basic Personal Amount: $15,705

**BC Provincial Tax Brackets (2025):**
- $0 to $47,937: 5.06%
- $47,937 to $95,875: 7.7%
- $95,875 to $110,076: 10.5%
- $110,076 to $133,353: 12.29%
- $133,353 to $181,232: 14.7%
- $181,232 to $252,752: 16.8%
- Over $252,752: 20.5%
- Basic Personal Amount: $12,580

**Instructions:**
1. Calculate taxable income (after basic personal amounts)
2. Apply progressive tax brackets correctly
3. Show federal tax, BC tax, and total tax
4. Use Excel/Google Sheets formula syntax (e.g., =IF, =MIN, =MAX)
5. Present as a structured CSV or describe the spreadsheet layout with formulas

**Important:** Use formulas that reference cells, not hardcoded calculation results. For example, use `=A1*0.14` not `=6300`.

Please generate the spreadsheet structure with formulas:

