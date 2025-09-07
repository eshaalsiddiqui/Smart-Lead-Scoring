"""
Lead Data Simulator for Smart Lead Scoring CRM
Generates realistic customer/lead data with demographics, interaction history, 
email engagement, and site visits.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import List, Dict
import json

class LeadDataSimulator:
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Define realistic data distributions
        self.industries = [
            'SaaS', 'E-commerce', 'Healthcare', 'Finance', 'Education', 
            'Manufacturing', 'Retail', 'Technology', 'Consulting', 'Real Estate'
        ]
        
        self.company_sizes = ['1-10', '11-50', '51-200', '201-1000', '1001-5000', '5000+']
        
        self.regions = ['NA', 'EU', 'APAC', 'LATAM', 'MEA']
        
        self.touchpoints = [
            'demo_request', 'email_open', 'webinar', 'ad_click', 'content_download',
            'pricing_page', 'contact_form', 'trial_signup', 'case_study_view', 'product_tour'
        ]
        
        self.job_titles = [
            'CEO', 'CTO', 'VP Sales', 'Marketing Director', 'Operations Manager',
            'Sales Manager', 'Product Manager', 'Business Analyst', 'IT Director', 'CFO'
        ]
        
        # Revenue potential by industry (base multipliers)
        self.industry_revenue_multipliers = {
            'SaaS': 1.5, 'Technology': 1.3, 'Finance': 1.2, 'Healthcare': 1.1,
            'E-commerce': 1.0, 'Manufacturing': 0.9, 'Retail': 0.8, 'Education': 0.7,
            'Consulting': 0.9, 'Real Estate': 0.8
        }
        
        # Company size revenue multipliers
        self.size_revenue_multipliers = {
            '1-10': 0.3, '11-50': 0.6, '51-200': 1.0, '201-1000': 1.5, 
            '1001-5000': 2.0, '5000+': 3.0
        }

    def generate_lead_data(self, num_leads: int = 1000, start_date: datetime = None) -> pd.DataFrame:
        """Generate comprehensive lead data with realistic patterns"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        
        leads = []
        
        for i in range(num_leads):
            # Basic demographics
            industry = np.random.choice(self.industries, p=[0.25, 0.15, 0.12, 0.10, 0.08, 0.08, 0.07, 0.05, 0.05, 0.05])
            company_size = np.random.choice(self.company_sizes, p=[0.20, 0.25, 0.20, 0.15, 0.10, 0.10])
            region = np.random.choice(self.regions, p=[0.35, 0.25, 0.20, 0.12, 0.08])
            
            # Interaction history (last 30 days)
            days_since_last_touch = np.random.randint(1, 31)
            last_touch = np.random.choice(self.touchpoints)
            
            # Engagement metrics (correlated with conversion likelihood)
            base_engagement = np.random.beta(2, 5)  # Skewed towards lower engagement
            
            # Page views (7 days) - correlated with engagement
            page_views_7d = max(0, int(np.random.poisson(3 + base_engagement * 10)))
            
            # Email engagement (30 days)
            emails_sent = np.random.randint(1, 15)
            email_open_rate = base_engagement + np.random.normal(0, 0.1)
            emails_opened_30d = max(0, int(emails_sent * max(0, min(1, email_open_rate))))
            
            # Call activity
            calls_last_30d = max(0, int(np.random.poisson(1 + base_engagement * 3)))
            
            # Deal size estimation (correlated with company size and industry)
            base_deal_size = np.random.lognormal(7, 1)  # Log-normal distribution
            industry_mult = self.industry_revenue_multipliers[industry]
            size_mult = self.size_revenue_multipliers[company_size]
            deal_size_estimate = int(base_deal_size * industry_mult * size_mult)
            
            # Conversion probability (based on engagement patterns)
            conversion_prob = self._calculate_conversion_probability(
                page_views_7d, emails_opened_30d, calls_last_30d, 
                industry, company_size, region, last_touch
            )
            
            # Additional features for richer data
            lead_score = int(conversion_prob * 100)
            days_in_pipeline = np.random.randint(1, 180)
            source_channel = np.random.choice(['organic', 'paid', 'referral', 'direct', 'social'], 
                                            p=[0.30, 0.25, 0.20, 0.15, 0.10])
            
            # Contact information
            job_title = np.random.choice(self.job_titles)
            decision_maker = np.random.choice([True, False], p=[0.3, 0.7])
            
            # Time-based features
            created_date = start_date + timedelta(days=np.random.randint(0, 365))
            last_activity = created_date + timedelta(days=days_since_last_touch)
            
            lead = {
                'lead_id': f"LEAD_{i+1:06d}",
                'company_name': f"{industry} Company {i+1}",
                'contact_name': f"Contact {i+1}",
                'email': f"contact{i+1}@company{i+1}.com",
                'job_title': job_title,
                'industry': industry,
                'company_size': company_size,
                'region': region,
                'source_channel': source_channel,
                'decision_maker': decision_maker,
                'created_date': created_date.strftime('%Y-%m-%d'),
                'last_activity': last_activity.strftime('%Y-%m-%d'),
                'last_touch': last_touch,
                'page_views_7d': page_views_7d,
                'emails_opened_30d': emails_opened_30d,
                'calls_last_30d': calls_last_30d,
                'days_in_pipeline': days_in_pipeline,
                'deal_size_estimate': deal_size_estimate,
                'lead_score': lead_score,
                'conversion_probability': conversion_prob,
                'converted': int(np.random.random() < conversion_prob)
            }
            
            leads.append(lead)
        
        return pd.DataFrame(leads)
    
    def _calculate_conversion_probability(self, page_views, emails_opened, calls, 
                                        industry, company_size, region, last_touch):
        """Calculate realistic conversion probability based on lead characteristics"""
        
        # Base conversion rate
        base_prob = 0.05
        
        # Page views impact (diminishing returns)
        page_impact = min(0.3, page_views * 0.02)
        
        # Email engagement impact
        email_impact = min(0.2, emails_opened * 0.01)
        
        # Call impact (high value)
        call_impact = min(0.4, calls * 0.1)
        
        # Industry impact
        industry_impact = {
            'SaaS': 0.1, 'Technology': 0.08, 'Finance': 0.06, 'Healthcare': 0.04,
            'E-commerce': 0.02, 'Manufacturing': 0.01, 'Retail': 0.0, 'Education': -0.01,
            'Consulting': 0.02, 'Real Estate': 0.01
        }.get(industry, 0)
        
        # Company size impact
        size_impact = {
            '1-10': -0.05, '11-50': 0.0, '51-200': 0.03, '201-1000': 0.06,
            '1001-5000': 0.08, '5000+': 0.05
        }.get(company_size, 0)
        
        # Region impact
        region_impact = {
            'NA': 0.05, 'EU': 0.03, 'APAC': 0.02, 'LATAM': 0.0, 'MEA': 0.01
        }.get(region, 0)
        
        # Last touch impact
        touch_impact = {
            'demo_request': 0.15, 'trial_signup': 0.12, 'pricing_page': 0.08,
            'contact_form': 0.06, 'webinar': 0.04, 'content_download': 0.03,
            'product_tour': 0.02, 'case_study_view': 0.01, 'email_open': 0.01,
            'ad_click': 0.0
        }.get(last_touch, 0)
        
        # Calculate final probability
        total_prob = (base_prob + page_impact + email_impact + call_impact + 
                     industry_impact + size_impact + region_impact + touch_impact)
        
        # Add some noise
        noise = np.random.normal(0, 0.02)
        final_prob = max(0.01, min(0.95, total_prob + noise))
        
        return round(final_prob, 3)

    def generate_daily_batch(self, date: datetime, num_leads: int = 50) -> pd.DataFrame:
        """Generate daily batch of new leads for ETL pipeline"""
        return self.generate_lead_data(num_leads, date)

    def save_to_csv(self, df: pd.DataFrame, filepath: str):
        """Save generated data to CSV"""
        df.to_csv(filepath, index=False)
        print(f"Generated {len(df)} leads and saved to {filepath}")

if __name__ == "__main__":
    # Generate sample data
    simulator = LeadDataSimulator()
    
    # Generate 1000 leads for training
    leads_df = simulator.generate_lead_data(1000)
    simulator.save_to_csv(leads_df, "data/generated_leads.csv")
    
    # Generate daily batch for ETL testing
    today = datetime.now()
    daily_batch = simulator.generate_daily_batch(today, 25)
    simulator.save_to_csv(daily_batch, f"data/daily_leads_{today.strftime('%Y%m%d')}.csv")
    
    print(f"Generated {len(leads_df)} training leads and {len(daily_batch)} daily leads")
    print(f"Conversion rate: {leads_df['converted'].mean():.2%}")
    print(f"Average deal size: ${leads_df['deal_size_estimate'].mean():,.0f}")
