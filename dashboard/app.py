from shiny import App, ui, render, reactive, req
import pickle
import json
import pandas as pd
import numpy as np

# ===============================================
# Load Model Artifacts
# ===============================================

# Define the class BEFORE loading pickle
class CreditLimitRecommender:
    """Credit limit recommendation system"""
    def __init__(self, model, scaler, segment_profiles, feature_names, thresholds):
        self.model = model
        self.scaler = scaler
        self.profiles = segment_profiles
        self.feature_names = feature_names
        self.thresholds = thresholds
    
    def _validate_input(self, customer_data):
        """Validate input"""
        # Check all required features present
        missing = [f for f in self.feature_names if f not in customer_data]
        if missing:
            raise ValueError(f"Missing required features: {missing}")
        
        # Check for None/empty values
        none_fields = [f for f in self.feature_names if customer_data[f] is None]
        if none_fields:
            raise ValueError(f"Please provide values for: {', '.join(none_fields)}")
        
        # Check transaction counts are integers
        int_fields = ['CASH_ADVANCE_TRX', 'PURCHASES_TRX', 'TENURE']
        non_int = [f for f in int_fields if not float(customer_data[f]).is_integer()]
        if non_int:
            raise ValueError(f"Transaction counts must be whole numbers: {', '.join(non_int)}")

        # Check for negative values (all financial metrics and counts must be >= 0)
        non_negative_fields = [
            'BALANCE', 'PURCHASES', 'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES',
            'CASH_ADVANCE', 'CASH_ADVANCE_TRX', 'PURCHASES_TRX',
            'PAYMENTS', 'MINIMUM_PAYMENTS', 'TENURE'
        ]
        for field in non_negative_fields:
            if customer_data[field] < 0:
                raise ValueError(f"{field} cannot be negative")
        
        # Check percentage/frequency fields are in [0, 1]
        # Note: CASH_ADVANCE_FREQUENCY excluded (can exceed 1.0 in data, max=1.5)
        pct_fields = [
            'BALANCE_FREQUENCY', 'PURCHASES_FREQUENCY',
            'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
            'PRC_FULL_PAYMENT'
        ]
        for field in pct_fields:
            if not 0 <= customer_data[field] <= 1:
                raise ValueError(f"{field} must be between 0 and 1")
        
        if customer_data['CASH_ADVANCE_FREQUENCY'] < 0:
            raise ValueError("CASH_ADVANCE_FREQUENCY cannot be negative")
    
    def _compute_individual_risk_score(self, customer_data):
        """Compute risk score"""
        score = 0
        cash_adv = customer_data['CASH_ADVANCE']
        full_pay = customer_data['PRC_FULL_PAYMENT']
        purchases = customer_data['PURCHASES']
        payments = customer_data['PAYMENTS']
        
        cash_adv_90th = self.thresholds['cash_adv_90th']
        cash_adv_75th = self.thresholds['cash_adv_75th']
        full_pay_mean = self.thresholds['full_pay_mean']
        
        if cash_adv > cash_adv_90th:
            score += 3
        elif cash_adv > cash_adv_75th:
            score += 2
        
        if full_pay < full_pay_mean:
            score += 1
        
        if payments < purchases:
            score += 1
        
        return min(score / 5, 1.0)
    
    def predict(self, customer_data):
        """Predict segment and recommend limit"""
        self._validate_input(customer_data)
        
        features_df = pd.DataFrame([[customer_data[f] for f in self.feature_names]], 
                                   columns=self.feature_names)
        features_scaled = self.scaler.transform(features_df)
        cluster_id = int(self.model.predict(features_scaled)[0])
        
        profile = self.profiles[cluster_id]
        risk_level = profile['risk_level']
        
        p25 = profile['credit_limit_25th']
        p50 = profile['credit_limit_median']
        p75 = profile['credit_limit_75th']
        
        if risk_level == 'Low Risk':
            low, high = p50, p75
        elif risk_level == 'Medium Risk':
            low, high = p25, p50
        else:
            low, high = p25, p25
        
        individual_risk = self._compute_individual_risk_score(customer_data)
        
        if high == low:
            recommended_limit = low
        else:
            recommended_limit = low + (1 - individual_risk) * (high - low)
        
        return {
            'cluster_id': cluster_id,
            'segment_name': profile['segment_name'],
            'risk_level': risk_level,
            'recommended_limit': int(recommended_limit),
            'individual_risk_score': round(individual_risk, 3),
            'segment_stats': {
                'p25': int(p25),
                'median': int(p50),
                'p75': int(p75),
                'size': int(profile['size']),
                'size_pct': round(profile['size_pct'], 1)
            }
        }


# Load basic pickles and JSONs
with open('kmeans_model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

with open('segment_profiles.json', 'r') as f:
    segment_profiles = json.load(f)
    # Convert string keys to int
    segment_profiles = {int(k): v for k, v in segment_profiles.items()}

with open('feature_names.json', 'r') as f:
    feature_names = json.load(f)

with open('risk_thresholds.json', 'r') as f:
    thresholds = json.load(f)

# Create recommender instance (avoids pickle class issues)
recommender = CreditLimitRecommender(
    model=model,
    scaler=scaler,
    segment_profiles=segment_profiles,
    feature_names=feature_names,
    thresholds=thresholds
)

# ===============================================
# UI Layout
# ===============================================

app_ui = ui.page_fluid(
    # Centered title with styling
    ui.div(
        {"class": "text-center py-3 mb-4 bg-light border-bottom"},
        ui.h2("Credit Limit Recommendation System", class_="mb-0")
    ),

    ui.layout_sidebar(
        # Sidebar
        ui.sidebar(
            ui.h4("Customer Information"),
            ui.p("Default values represent median General Users segment (38.5% of customers). Modify values to test different customer profiles.", class_="text-muted small mb-3"),
            
            ui.accordion(
                ui.accordion_panel(
                    "Financial Metrics (7 fields)",
                    ui.input_numeric("BALANCE", "Balance ($):", value=400, min=0, step=100),
                    ui.input_numeric("PURCHASES", "Purchases ($):", value=1000, min=0, step=50),
                    ui.input_numeric("ONEOFF_PURCHASES", "One-off Purchases ($):", value=230, min=0, step=50),
                    ui.input_numeric("INSTALLMENTS_PURCHASES", "Installment Purchases ($):", value=500, min=0, step=50),
                    ui.input_numeric("CASH_ADVANCE", "Cash Advance ($):", value=0, min=0, step=50),
                    ui.input_numeric("PAYMENTS", "Payments ($):", value=1000, min=0, step=50),
                    ui.input_numeric("MINIMUM_PAYMENTS", "Minimum Payments ($):", value=200, min=0, step=50),
                ),
                
                ui.accordion_panel(
                    "Transaction Patterns (7 fields)",
                    ui.input_slider("BALANCE_FREQUENCY", "Balance Frequency:", min=0, max=1, value=1, step=0.01),
                    ui.input_slider("PURCHASES_FREQUENCY", "Purchase Frequency:", min=0, max=1, value=1, step=0.01),
                    ui.input_slider("ONEOFF_PURCHASES_FREQUENCY", "One-off Purchase Frequency:", min=0, max=1, value=0.2, step=0.01),
                    ui.input_slider("PURCHASES_INSTALLMENTS_FREQUENCY", "Installment Frequency:", min=0, max=1, value=0.8, step=0.01),
                    ui.input_numeric("CASH_ADVANCE_FREQUENCY", "Cash Advance Frequency:", value=0, min=0, max=2, step=0.01),
                    ui.input_numeric("CASH_ADVANCE_TRX", "Cash Advance Transactions:", value=0, min=0, step=1),
                    ui.input_numeric("PURCHASES_TRX", "Purchase Transactions:", value=18, min=0, step=1),
                ),
                
                ui.accordion_panel(
                    "Behavioral Indicators (2 fields)",
                    ui.input_slider("PRC_FULL_PAYMENT", "Full Payment Percentage:", min=0, max=1, value=0.08, step=0.01),
                    ui.input_numeric("TENURE", "Tenure (months):", value=12, min=0, max=12, step=1),
                ),
                
                id="input_accordion",
                open=["Financial Metrics (7 fields)"]
            ),
            
            ui.hr(),

            ui.input_action_button("predict", "Get Recommendation", class_="btn-primary btn-lg w-100"),
            ui.input_action_button("reset", "Reset to Defaults", class_="btn-outline-primary w-100 mt-2"),
            
            width=350
        ),
        
        # Main content
        ui.output_ui("results")
    )
)

# ===============================================
# Server Logic
# ===============================================

def server(input, output, session):
    
    @reactive.Calc
    def get_customer_data():
        """Collect all input values into customer data dict"""
        return {
            'BALANCE': input.BALANCE(),
            'BALANCE_FREQUENCY': input.BALANCE_FREQUENCY(),
            'PURCHASES': input.PURCHASES(),
            'ONEOFF_PURCHASES': input.ONEOFF_PURCHASES(),
            'INSTALLMENTS_PURCHASES': input.INSTALLMENTS_PURCHASES(),
            'CASH_ADVANCE': input.CASH_ADVANCE(),
            'PURCHASES_FREQUENCY': input.PURCHASES_FREQUENCY(),
            'ONEOFF_PURCHASES_FREQUENCY': input.ONEOFF_PURCHASES_FREQUENCY(),
            'PURCHASES_INSTALLMENTS_FREQUENCY': input.PURCHASES_INSTALLMENTS_FREQUENCY(),
            'CASH_ADVANCE_FREQUENCY': input.CASH_ADVANCE_FREQUENCY(),
            'CASH_ADVANCE_TRX': input.CASH_ADVANCE_TRX(),
            'PURCHASES_TRX': input.PURCHASES_TRX(),
            'PAYMENTS': input.PAYMENTS(),
            'MINIMUM_PAYMENTS': input.MINIMUM_PAYMENTS(),
            'PRC_FULL_PAYMENT': input.PRC_FULL_PAYMENT(),
            'TENURE': input.TENURE()
        }
    
    @reactive.effect
    @reactive.event(input.reset)
    def _():
            """Reset all inputs to default values"""
            ui.update_numeric("BALANCE", value=400)
            ui.update_numeric("PURCHASES", value=1000)
            ui.update_numeric("ONEOFF_PURCHASES", value=230)
            ui.update_numeric("INSTALLMENTS_PURCHASES", value=500)
            ui.update_numeric("CASH_ADVANCE", value=0)
            ui.update_numeric("PAYMENTS", value=1000)
            ui.update_numeric("MINIMUM_PAYMENTS", value=200)
            ui.update_slider("BALANCE_FREQUENCY", value=1.0)
            ui.update_slider("PURCHASES_FREQUENCY", value=1.0)
            ui.update_slider("ONEOFF_PURCHASES_FREQUENCY", value=0.2)
            ui.update_slider("PURCHASES_INSTALLMENTS_FREQUENCY", value=0.8)
            ui.update_numeric("CASH_ADVANCE_FREQUENCY", value=0)
            ui.update_numeric("CASH_ADVANCE_TRX", value=0)
            ui.update_numeric("PURCHASES_TRX", value=18)
            ui.update_slider("PRC_FULL_PAYMENT", value=0.08)
            ui.update_numeric("TENURE", value=12)
        
    @output
    @render.ui
    def results():
        # Show instruction message before first click
        if input.predict() == 0:
            return ui.div(
                 {"class": "text-center p-5 mt-5"},
                ui.h4("Enter customer information and click 'Get Recommendation'", class_="text-muted"),
                ui.p("The system will predict the customer segment and recommend an appropriate credit limit.", class_="text-muted")
            )

        req(input.predict())  # Only proceed if button clicked at least once
        
        # Get customer data
        customer_data = get_customer_data()
        
        # Try prediction
        try:
            result = recommender.predict(customer_data)
            
            # Determine alert class based on risk
            risk_class = {
                'Low Risk': 'success',
                'Medium Risk': 'warning',
                'High Risk': 'danger'
            }.get(result['risk_level'], 'info')
            
            return ui.div(
                # Segment and Risk
                ui.h3(f"Segment: {result['segment_name']}", class_="mb-3"),
                ui.div(
                    {"class": f"alert alert-{risk_class}"},
                    ui.h5(f"Risk Level: {result['risk_level']}", class_="mb-0")
                ),
                
                ui.hr(),
                
                # Recommended Credit Limit
                ui.div(
                    {"class": "card bg-light mb-4"},
                    ui.div(
                        {"class": "card-body"},
                        ui.h4("Recommended Credit Limit", class_="card-title"),
                        ui.h2(f"${result['recommended_limit']:,}", class_="text-primary"),
                        ui.p(f"Individual Risk Score: {result['individual_risk_score']:.3f} (0=lowest, 1=highest)", class_="text-muted")
                    )
                ),
                
                # Segment Statistics
                ui.h5("Segment Credit Limit Distribution"),
                ui.div(
                    {"class": "card"},
                    ui.div(
                        {"class": "card-body"},
                        ui.tags.table(
                            {"class": "table table-sm"},
                            ui.tags.tbody(
                                ui.tags.tr(
                                    ui.tags.td("25th Percentile:"),
                                    ui.tags.td(f"${result['segment_stats']['p25']:,}", {"class": "text-end"})
                                ),
                                ui.tags.tr(
                                    ui.tags.td("Median (50th):"),
                                    ui.tags.td(f"${result['segment_stats']['median']:,}", {"class": "text-end fw-bold"})
                                ),
                                ui.tags.tr(
                                    ui.tags.td("75th Percentile:"),
                                    ui.tags.td(f"${result['segment_stats']['p75']:,}", {"class": "text-end"})
                                ),
                                ui.tags.tr(
                                    ui.tags.td("Segment Size:"),
                                    ui.tags.td(f"{result['segment_stats']['size']:,} customers ({result['segment_stats']['size_pct']:.1f}%)", {"class": "text-end"})
                                )
                            )
                        )
                    )
                ),
                
                ui.hr(),
                
                # Explanation
                ui.div(
                    {"class": "alert alert-info"},
                    ui.h6("How this recommendation was calculated:", class_="mb-2"),
                    ui.tags.ul(
                        ui.tags.li(f"Customer assigned to '{result['segment_name']}' segment"),
                        ui.tags.li(f"Segment risk level: {result['risk_level']}"),
                        ui.tags.li(f"Individual behavioral risk score: {result['individual_risk_score']:.3f}"),
                        ui.tags.li("Recommendation scaled within segment credit band based on individual risk")
                    )
                )
            )
            
        except ValueError as e:
            # Validation error
            return ui.div(
                {"class": "alert alert-danger"},
                ui.h5("Validation Error", class_="alert-heading"),
                ui.p(str(e)),
                ui.hr(),
                ui.p("Please check your input values and try again.", class_="mb-0")
            )
        except Exception as e:
            # Other errors
            return ui.div(
                {"class": "alert alert-danger"},
                ui.h5("Error", class_="alert-heading"),
                ui.p(f"An unexpected error occurred: {str(e)}")
            )

# ===============================================
# Create App
# ===============================================

app = App(app_ui, server)