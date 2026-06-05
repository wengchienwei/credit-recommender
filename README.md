# Credit Limit Recommendation System

**[→ Live Demo](https://huggingface.co/spaces/wengchienwei/credit-recommender)** | **[View Analysis](clustering_analysis.ipynb)**

> Machine learning system for automated credit limit recommendations using customer segmentation and behavioral risk scoring.

---

## Overview

This project implements an end-to-end credit decisioning pipeline that segments credit card customers into 4 distinct behavioral groups and recommends personalized credit limits based on segment-level risk profiles and individual behavioral patterns.

**Key Features:**
- K-Means clustering identifies 4 customer segments with distinct spending patterns
- Individual risk scoring using 3 behavioral factors (cash advance, payment, debt)
- Segment-specific credit bands with risk-adjusted recommendations
- Interactive dashboard for real-time what-if analysis
- Automated validation with test coverage

---

## Tech Stack

**Machine Learning:** scikit-learn, pandas, numpy  
**Visualization:** matplotlib, seaborn  
**Dashboard:** Shiny for Python  
**Deployment:** Hugging Face Spaces  
**Development:** Python 3.12, Jupyter Notebook

---

## Quick Start

<details>
<summary><b>Setup and Execution — Click to expand</b></summary>

### 1. Clone Repository
```bash
git clone https://github.com/wengchienwei/credit-recommender.git
cd credit-recommender
```

### 2. Install Dependencies
```bash
cd dashboard
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 3. Run Dashboard
```bash
shiny run app.py
```
Dashboard opens at `http://127.0.0.1:8000`

</details>

---

## Model Performance

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Algorithm** | K-Means (k=4) | Unsupervised clustering |
| **Silhouette Score** | 0.213 | Good cluster separation |
| **Davies-Bouldin Index** | 1.496 | Well-defined clusters |

**Feature Set:** 16 behavioral and financial metrics including purchases, cash advances, payment patterns, transaction frequencies, and account tenure.

---

## Customer Segments

| Segment | Size | Risk | Recommended Range | Characteristics |
|---------|------|------|-------------------|-----------------|
| **Low-Activity Users** | 44.7% | Low | $3,000-4,000 | Minimal transactions, conservative spending |
| **General Users** | 38.5% | Low | $4,000-6,000 | Moderate activity, balanced behavior |
| **Cash-Advance Dependent** | 14.1% | High | $4,000 (capped) | Heavy cash advance usage, low payments |
| **Premium Spenders** | 2.7% | Medium | $8,000-10,000 | High purchase volume, frequent transactions |

---

## Recommendation Logic

**Credit Limit Bands:**
- **Low Risk:** Median → 75th percentile (encouraging growth)
- **Medium Risk:** 25th → 50th percentile (balanced approach)
- **High Risk:** Fixed at 25th percentile (conservative)

**Individual Risk Modulation:** 3-factor behavioral score (0-1 scale) adjusts final limit within assigned band based on cash advance dependency, payment discipline, and debt accumulation.

---

## Project Structure
```
├── clustering_analysis.ipynb    # Complete analysis pipeline
├── dashboard/
│   ├── app.py                   # Shiny dashboard application
│   ├── requirements.txt         # Python dependencies
│   ├── TESTING.md              # Test procedures
│   ├── kmeans_model.pkl        # Trained clustering model
│   ├── scaler.pkl              # Feature scaler
│   ├── segment_profiles.json   # Segment statistics
│   ├── feature_names.json      # Feature list
│   └── risk_thresholds.json    # Risk scoring thresholds
└── README.md
```

---

## Results & Insights

**Business Impact:**
- 83% of customers are low-risk (Low-Activity + General Users)
- 14% require restrictive credit management (Cash-Advance Dependent)
- 2.7% represent high-value opportunity (Premium Spenders)

**Operational Value:**
- Automated, consistent credit decisions eliminate subjective bias
- Real-time what-if analysis enables scenario testing
- Scalable to thousands of applications daily
- Individual risk scoring complements segment-level assessment
- Optimizes revenue opportunity with default risk

---

## Testing

Test suite covers:
- Segment classification (all 4 clusters with mean values)
- Input validation (missing values, negative amounts, type checking)
- Reactive UI updates and reset functionality
- Risk scoring accuracy and credit band logic

See [`dashboard/TESTING.md`](dashboard/TESTING.md) for complete test procedures.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

*Data source: Confidential credit card customer dataset. Model uses aggregated statistics only. Original data not included per data privacy agreements.*

---

*Academic Project | Marketing Analytics (Fall 2025)*  
*Instructor: Prof. Raoul V. Kübler (ESSEC Business School)*
	
