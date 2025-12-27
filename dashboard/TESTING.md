# Testing Guide

## Local Testing

### Start Server
```bash
cd dashboard
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
shiny run app.py
```

Browser opens at: http://127.0.0.1:8000

---

## Test Cases

### Test 1: Low-Activity Users
**Input Values** (mean of Cluster 0):
```
Financial Metrics:
  BALANCE: 1010
  PURCHASES: 280
  ONEOFF_PURCHASES: 220
  INSTALLMENTS_PURCHASES: 70
  CASH_ADVANCE: 560
  PAYMENTS: 970
  MINIMUM_PAYMENTS: 540

Transaction Patterns:
  BALANCE_FREQUENCY: 0.8
  PURCHASES_FREQUENCY: 0.2
  ONEOFF_PURCHASES_FREQUENCY: 0.1
  PURCHASES_INSTALLMENTS_FREQUENCY: 0.1
  CASH_ADVANCE_FREQUENCY: 0.1
  CASH_ADVANCE_TRX: 2
  PURCHASES_TRX: 3

Behavioral Indicators:
  PRC_FULL_PAYMENT: 0.08
  TENURE: 11
```

**Expected Output:**
- Segment: Low-Activity Users
- Risk Level: Low Risk
- Credit Limit: ~$3,000-4,000

---

### Test 2: General Users (Default Values)
**Input Values** (median of Cluster 1):
- Use default values (already loaded)

**Expected Output:**
- Segment: General Users
- Risk Level: Low Risk
- Credit Limit: ~$4,000-6,000

---

### Test 3: Cash-Advance Dependent
**Input Values** (mean of Cluster 2):
```
BALANCE: 4310
PURCHASES: 470
CASH_ADVANCE: 4390
PAYMENTS: 3390
MINIMUM_PAYMENTS: 2010
CASH_ADVANCE_FREQUENCY: 0.5
CASH_ADVANCE_TRX: 14
PURCHASES_TRX: 7
PRC_FULL_PAYMENT: 0.04
TENURE: 11
```

**Expected Output:**
- Segment: Cash-Advance Dependent
- Risk Level: High Risk
- Credit Limit: ~$4,000 (fixed at p25)

---

### Test 4: Premium Spenders
**Input Values** (mean of Cluster 3):
```
BALANCE: 4120
PURCHASES: 9930
ONEOFF_PURCHASES: 6670
INSTALLMENTS_PURCHASES: 3270
CASH_ADVANCE: 700
PAYMENTS: 9150
MINIMUM_PAYMENTS: 2560
PURCHASES_FREQUENCY: 0.9
PURCHASES_TRX: 105
PRC_FULL_PAYMENT: 0.3
TENURE: 12
```

**Expected Output:**
- Segment: Premium Spenders
- Risk Level: Medium Risk
- Credit Limit: ~$8,000-10,000

---

## Validation Tests

### Test 5: Missing Value
1. Clear BALANCE field (delete value)
2. Click "Get Recommendation"
3. **Expected:** Error message "Please provide values for: BALANCE"

### Test 6: Invalid Value
1. Enter PURCHASES = -500
2. Click "Get Recommendation"
3. **Expected:** Error message "PURCHASES cannot be negative"

### Test 7: Float Transaction Count
1. Enter PURCHASES_TRX = 4.5
2. Click "Get Recommendation"
3. **Expected:** Error message "Transaction counts must be whole numbers"

---

## UI Tests

### Test 8: Reset Button
1. Change multiple values
2. Click "Reset to Defaults"
3. **Expected:** All values revert to General Users medians

### Test 9: Accordion Navigation
1. Click each accordion section
2. **Expected:** Sections expand/collapse smoothly, no scrolling needed

### Test 10: Reactive Updates
1. Start with default values (General Users)
2. Click "Get Recommendation" once
3. Change CASH_ADVANCE from 0 to **15000**
4. **Expected:** 
   - Output updates immediately (no button click needed)
   - Segment changes: General Users → Cash-Advance Dependent
   - Risk changes: Low Risk → High Risk
   - Limit changes: ~$5,600 → 4,000

**Note:** Value of 15000 is needed (not just 5000) because K-Means considers all 16 features, not just cash advance. A single feature change must be extreme enough to shift overall cluster assignment in 16-dimensional scaled feature space.
