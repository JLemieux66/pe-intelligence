"""
Analyze the feasibility of building an ML model for revenue prediction
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Load the data
df = pd.read_csv('ml_features_combined_cleaned.csv')

print("=" * 80)
print("ML FEASIBILITY ANALYSIS FOR REVENUE PREDICTION")
print("=" * 80)

# 1. Dataset Overview
print("\n1. DATASET OVERVIEW")
print("-" * 80)
print(f"Total records: {len(df):,}")
print(f"Total features: {len(df.columns)}")
print(f"\nShape: {df.shape}")

# 2. Target Variable Analysis
print("\n2. TARGET VARIABLE ANALYSIS (revenue_usd_millions)")
print("-" * 80)
target = 'revenue_usd_millions'
print(f"Non-null values: {df[target].notna().sum():,} ({df[target].notna().sum()/len(df)*100:.1f}%)")
print(f"Missing values: {df[target].isna().sum():,} ({df[target].isna().sum()/len(df)*100:.1f}%)")
print(f"\nRevenue Statistics:")
print(df[target].describe())
print(f"\nRevenue Range: ${df[target].min():.2f}M - ${df[target].max():.2f}M")
print(f"Median Revenue: ${df[target].median():.2f}M")

# 3. Feature Completeness Analysis
print("\n3. FEATURE COMPLETENESS ANALYSIS")
print("-" * 80)
missing_stats = pd.DataFrame({
    'Column': df.columns,
    'Missing_Count': df.isnull().sum(),
    'Missing_Percent': (df.isnull().sum() / len(df) * 100).round(2),
    'Non_Missing': df.notnull().sum(),
    'Dtype': df.dtypes
}).sort_values('Missing_Percent', ascending=False)

print("\nTop 15 Features with Missing Values:")
print(missing_stats.head(15).to_string(index=False))

# 4. Feature Categories
print("\n4. FEATURE CATEGORIES")
print("-" * 80)
numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_features = df.select_dtypes(include=['object']).columns.tolist()

print(f"Numeric features: {len(numeric_features)}")
print(f"Categorical features: {len(categorical_features)}")

# 5. Key Features for Revenue Prediction
print("\n5. KEY FEATURES AVAILABILITY")
print("-" * 80)
key_features = [
    'pitchbook_valuation_usd_millions',
    'employee_count_pitchbook',
    'employee_count_linkedin_scraped',
    'employee_count_crunchbase_range',
    'total_funding_usd',
    'num_funding_rounds',
    'company_age_years',
    'num_pe_investors',
    'pitchbook_primary_industry_sector',
    'pitchbook_hq_country',
    'company_size_category',
    'crunchbase_revenue_range'
]

for feature in key_features:
    if feature in df.columns:
        non_null = df[feature].notna().sum()
        pct = non_null / len(df) * 100
        print(f"{feature:45s}: {non_null:5,} ({pct:5.1f}%)")

# 6. Correlation Analysis with Revenue
print("\n6. CORRELATION ANALYSIS WITH REVENUE")
print("-" * 80)
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
if target in numeric_cols:
    numeric_cols.remove(target)

correlations = {}
for col in numeric_cols:
    if df[col].notna().sum() > 100:  # Only calculate if enough non-null values
        valid_data = df[[target, col]].dropna()
        if len(valid_data) > 10:
            corr = valid_data[target].corr(valid_data[col])
            correlations[col] = corr

# Sort by absolute correlation
sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
print("\nTop 15 Features by Correlation with Revenue:")
for i, (feature, corr) in enumerate(sorted_corr[:15], 1):
    print(f"{i:2d}. {feature:45s}: {corr:7.4f}")

# 7. Data Quality Assessment
print("\n7. DATA QUALITY ASSESSMENT")
print("-" * 80)

# Check for duplicates
duplicates = df.duplicated().sum()
print(f"Duplicate rows: {duplicates}")

# Check for infinite values
inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
print(f"Infinite values: {inf_count}")

# Check for negative revenue
if target in df.columns:
    negative_revenue = (df[target] < 0).sum()
    print(f"Negative revenue values: {negative_revenue}")

# Check for outliers in revenue
revenue_data = df[target].dropna()
Q1 = revenue_data.quantile(0.25)
Q3 = revenue_data.quantile(0.75)
IQR = Q3 - Q1
outliers = ((revenue_data < (Q1 - 1.5 * IQR)) | (revenue_data > (Q3 + 1.5 * IQR))).sum()
print(f"Revenue outliers (IQR method): {outliers} ({outliers/len(revenue_data)*100:.1f}%)")

# 8. Training Data Availability
print("\n8. TRAINING DATA AVAILABILITY")
print("-" * 80)
complete_cases = df.dropna(subset=[target])
print(f"Records with revenue data: {len(complete_cases):,}")
print(f"Percentage of total: {len(complete_cases)/len(df)*100:.1f}%")

# Check how many records have both revenue and key features
key_numeric_features = [f for f in key_features if f in numeric_features]
sufficient_data = complete_cases.dropna(subset=key_numeric_features[:5])  # Check top 5
print(f"Records with revenue + key features: {len(sufficient_data):,}")

# 9. ML Model Feasibility Assessment
print("\n9. ML MODEL FEASIBILITY ASSESSMENT")
print("=" * 80)

feasibility_score = 0
max_score = 7

# Criterion 1: Sufficient training samples
if len(complete_cases) >= 1000:
    print("✓ PASS: Sufficient training samples (≥1000)")
    feasibility_score += 1
else:
    print("✗ FAIL: Insufficient training samples (<1000)")

# Criterion 2: Target variable quality
missing_target_pct = df[target].isna().sum() / len(df) * 100
if missing_target_pct < 50:
    print(f"✓ PASS: Target variable completeness ({100-missing_target_pct:.1f}%)")
    feasibility_score += 1
else:
    print(f"✗ FAIL: High target missingness ({missing_target_pct:.1f}%)")

# Criterion 3: Feature richness
if len(numeric_features) >= 10:
    print(f"✓ PASS: Rich feature set ({len(numeric_features)} numeric features)")
    feasibility_score += 1
else:
    print(f"✗ FAIL: Limited features ({len(numeric_features)} numeric features)")

# Criterion 4: Feature completeness
avg_completeness = (1 - missing_stats['Missing_Percent'].mean() / 100)
if avg_completeness >= 0.5:
    print(f"✓ PASS: Reasonable feature completeness ({avg_completeness*100:.1f}%)")
    feasibility_score += 1
else:
    print(f"✗ FAIL: Poor feature completeness ({avg_completeness*100:.1f}%)")

# Criterion 5: Strong correlations exist
strong_corr_count = sum(1 for _, corr in sorted_corr if abs(corr) > 0.3)
if strong_corr_count >= 3:
    print(f"✓ PASS: Strong predictive features exist ({strong_corr_count} with |r| > 0.3)")
    feasibility_score += 1
else:
    print(f"✗ FAIL: Weak correlations with revenue")

# Criterion 6: Data quality
if duplicates == 0 and inf_count == 0:
    print("✓ PASS: Good data quality (no duplicates/infinites)")
    feasibility_score += 1
else:
    print("✗ FAIL: Data quality issues detected")

# Criterion 7: Revenue distribution
skewness = revenue_data.skew()
if abs(skewness) < 3:
    print(f"✓ PASS: Reasonable revenue distribution (skewness: {skewness:.2f})")
    feasibility_score += 1
else:
    print(f"⚠ WARNING: Highly skewed revenue (skewness: {skewness:.2f}) - may need transformation")

# Final Assessment
print("\n" + "=" * 80)
print(f"FEASIBILITY SCORE: {feasibility_score}/{max_score}")
print("=" * 80)

if feasibility_score >= 6:
    print("\n🎉 RECOMMENDATION: HIGHLY FEASIBLE")
    print("The dataset is well-suited for building a robust ML model for revenue prediction.")
elif feasibility_score >= 4:
    print("\n✓ RECOMMENDATION: FEASIBLE WITH CONSIDERATIONS")
    print("The dataset can support ML modeling with some data preprocessing and feature engineering.")
elif feasibility_score >= 2:
    print("\n⚠ RECOMMENDATION: CHALLENGING BUT POSSIBLE")
    print("Significant data preprocessing and feature engineering will be required.")
else:
    print("\n✗ RECOMMENDATION: NOT RECOMMENDED")
    print("The dataset has significant limitations that may prevent robust modeling.")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
if feasibility_score >= 4:
    print("1. Perform feature engineering to create derived features")
    print("2. Handle missing values using appropriate imputation strategies")
    print("3. Apply feature scaling and transformation")
    print("4. Try multiple algorithms (Random Forest, XGBoost, LightGBM, Neural Networks)")
    print("5. Use cross-validation for robust model evaluation")
    print("6. Implement ensemble methods for improved predictions")
    print("7. Focus on feature importance analysis")
else:
    print("1. Collect more labeled data (companies with known revenue)")
    print("2. Improve feature quality and completeness")
    print("3. Enhance data collection process")
    print("4. Consider alternative modeling approaches")
