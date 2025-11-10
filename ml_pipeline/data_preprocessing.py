"""
Data Preprocessing and Feature Engineering Pipeline
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
from typing import Tuple, List, Dict, Any
import pickle
import json
from pathlib import Path


class FeatureEngineer:
    """Advanced feature engineering for revenue prediction"""

    def __init__(self):
        self.label_encoders = {}
        self.scaler = RobustScaler()  # More robust to outliers than StandardScaler
        self.feature_names = []
        self.numeric_features = []
        self.categorical_features = []

    def create_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create advanced derived features"""
        df = df.copy()

        # 1. Employee-based features
        if 'employee_count_pitchbook' in df.columns:
            df['log_employees'] = np.log1p(df['employee_count_pitchbook'].fillna(0))
            df['employees_squared'] = df['employee_count_pitchbook'] ** 2

        # 2. Funding-based features
        if 'total_funding_usd' in df.columns and 'num_funding_rounds' in df.columns:
            df['avg_funding_per_round'] = df['total_funding_usd'] / (df['num_funding_rounds'] + 1)
            df['log_total_funding'] = np.log1p(df['total_funding_usd'])
            df['funding_efficiency'] = df['total_funding_usd'] / (df['employee_count_pitchbook'].fillna(1) + 1)

        # 3. Valuation-based features
        if 'pitchbook_valuation_usd_millions' in df.columns:
            df['log_valuation'] = np.log1p(df['pitchbook_valuation_usd_millions'].fillna(0))
            df['valuation_per_employee'] = df['pitchbook_valuation_usd_millions'] / (df['employee_count_pitchbook'].fillna(1) + 1)

        # 4. Age and timing features
        if 'company_age_years' in df.columns:
            df['age_squared'] = df['company_age_years'] ** 2
            df['is_young_company'] = (df['company_age_years'] <= 5).astype(int)
            df['is_mature_company'] = (df['company_age_years'] >= 15).astype(int)

        if 'months_since_last_funding' in df.columns:
            filled_months = df['months_since_last_funding'].fillna(60)
            df['funding_recency_score'] = 1 / (filled_months + 1)

        # 5. PE investor features
        if 'num_pe_investors' in df.columns:
            df['has_pe_backing'] = (df['num_pe_investors'] > 0).astype(int)
            df['pe_investor_strength'] = np.where(
                df['num_pe_investors'] > 0,
                np.log1p(df['num_pe_investors']),
                0
            )

        # 6. Funding stage features
        if 'funding_stage_encoded' in df.columns:
            df['is_growth_stage'] = (df['funding_stage_encoded'] >= 4).astype(int)
            df['is_early_stage'] = (df['funding_stage_encoded'] <= 2).astype(int)

        # 7. Geographic concentration
        if 'pitchbook_hq_country' in df.columns:
            top_countries = ['United States', 'Canada', 'United Kingdom']
            df['is_top_country'] = df['pitchbook_hq_country'].isin(top_countries).astype(int)

        # 8. Industry concentration
        if 'pitchbook_primary_industry_sector' in df.columns:
            tech_sectors = ['Information Technology', 'Software']
            df['is_tech_sector'] = df['pitchbook_primary_industry_sector'].isin(tech_sectors).astype(int)

        # 9. Multiple employee data sources consistency
        employee_cols = ['employee_count_pitchbook', 'employee_count_linkedin_scraped']
        available_cols = [col for col in employee_cols if col in df.columns]
        if len(available_cols) >= 2:
            df['employee_data_consistency'] = df[available_cols].std(axis=1, skipna=True)
            df['employee_avg_all_sources'] = df[available_cols].mean(axis=1, skipna=True)

        # 10. Interaction features
        if 'employee_count_pitchbook' in df.columns and 'funding_stage_encoded' in df.columns:
            df['employees_x_stage'] = df['employee_count_pitchbook'] * df['funding_stage_encoded']

        if 'pitchbook_valuation_usd_millions' in df.columns and 'company_age_years' in df.columns:
            df['valuation_growth_rate'] = df['pitchbook_valuation_usd_millions'] / (df['company_age_years'].fillna(1) + 1)

        return df

    def handle_missing_values(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Intelligent missing value imputation"""
        df = df.copy()

        # Strategy 1: Fill with 0 for counts/amounts where missing = none
        zero_fill_cols = [
            'total_funding_usd', 'num_funding_rounds', 'num_pe_investors',
            'total_investors', 'avg_round_size_usd'
        ]
        for col in zero_fill_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # Strategy 2: Fill with median for continuous variables
        median_fill_cols = [
            'pitchbook_valuation_usd_millions', 'employee_count_pitchbook',
            'pitchbook_last_financing_size_usd_millions', 'company_age_years',
            'months_since_last_funding'
        ]
        for col in median_fill_cols:
            if col in df.columns:
                if fit:
                    median_val = df[col].median()
                    self.__dict__[f'{col}_median'] = median_val
                else:
                    median_val = self.__dict__.get(f'{col}_median', df[col].median())
                filled_values = df[col].fillna(median_val)
                df[col] = filled_values

        # Strategy 3: Fill categorical with 'Unknown'
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            filled_values = df[col].fillna('Unknown')
            df[col] = filled_values.infer_objects(copy=False)

        return df

    def encode_categorical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Encode categorical features with frequency encoding for high cardinality"""
        df = df.copy()

        categorical_cols = [
            'pitchbook_primary_industry_sector',
            'pitchbook_primary_industry_group',
            'pitchbook_hq_country',
            'latest_funding_type',
            'crunchbase_revenue_range',
            'company_size_category'
        ]

        for col in categorical_cols:
            if col not in df.columns:
                continue

            # Frequency encoding for high cardinality
            if fit:
                freq_map = df[col].value_counts(normalize=True).to_dict()
                self.label_encoders[f'{col}_freq'] = freq_map
            else:
                freq_map = self.label_encoders.get(f'{col}_freq', {})

            df[f'{col}_freq'] = df[col].map(freq_map).fillna(0)

            # Label encoding as backup
            if fit:
                le = LabelEncoder()
                # Fit on all unique values including 'Unknown'
                unique_vals = df[col].unique().tolist()
                if 'Unknown' not in unique_vals:
                    unique_vals.append('Unknown')
                le.fit(unique_vals)
                self.label_encoders[col] = le

            le = self.label_encoders.get(col)
            if le:
                df[f'{col}_encoded'] = df[col].map(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )

        return df

    def select_features(self, df: pd.DataFrame, target: str = 'revenue_usd_millions') -> pd.DataFrame:
        """Select final features for modeling"""
        # Define feature sets
        numeric_base_features = [
            'pitchbook_valuation_usd_millions',
            'employee_count_pitchbook',
            'pitchbook_last_financing_size_usd_millions',
            'total_funding_usd',
            'num_funding_rounds',
            'avg_round_size_usd',
            'total_investors',
            'months_since_last_funding',
            'funding_stage_encoded',
            'company_age_years',
            'num_pe_investors',
            'is_pe_backed'
        ]

        # Derived features
        derived_features = [
            'log_employees', 'employees_squared', 'avg_funding_per_round',
            'log_total_funding', 'funding_efficiency', 'log_valuation',
            'valuation_per_employee', 'age_squared', 'is_young_company',
            'is_mature_company', 'funding_recency_score', 'has_pe_backing',
            'pe_investor_strength', 'is_growth_stage', 'is_early_stage',
            'is_top_country', 'is_tech_sector', 'employees_x_stage',
            'valuation_growth_rate'
        ]

        # Encoded categorical features
        encoded_features = [
            col for col in df.columns
            if col.endswith('_freq') or (col.endswith('_encoded') and col != 'funding_stage_encoded')
        ]

        # Combine all features
        all_features = numeric_base_features + derived_features + encoded_features

        # Only select features that exist in the dataframe
        available_features = [f for f in all_features if f in df.columns]

        # Add target if it exists
        if target in df.columns:
            available_features.append(target)

        self.feature_names = [f for f in available_features if f != target]

        return df[available_features]

    def scale_features(self, df: pd.DataFrame, target: str = 'revenue_usd_millions', fit: bool = True) -> pd.DataFrame:
        """Scale numeric features"""
        df = df.copy()

        # Separate features and target
        feature_cols = [col for col in df.columns if col != target]

        if fit:
            self.scaler.fit(df[feature_cols])

        df[feature_cols] = self.scaler.transform(df[feature_cols])

        return df

    def fit_transform(self, df: pd.DataFrame, target: str = 'revenue_usd_millions') -> pd.DataFrame:
        """Full pipeline: fit and transform"""
        print("Starting feature engineering pipeline...")
        print(f"Initial shape: {df.shape}")

        # Step 1: Create derived features
        print("Creating derived features...")
        df = self.create_derived_features(df)
        print(f"After derived features: {df.shape}")

        # Step 2: Handle missing values
        print("Handling missing values...")
        df = self.handle_missing_values(df, fit=True)

        # Step 3: Encode categorical features
        print("Encoding categorical features...")
        df = self.encode_categorical_features(df, fit=True)
        print(f"After encoding: {df.shape}")

        # Step 4: Select features
        print("Selecting features...")
        df = self.select_features(df, target)
        print(f"After feature selection: {df.shape}")
        print(f"Selected {len(self.feature_names)} features")

        # Step 5: Scale features
        print("Scaling features...")
        df = self.scale_features(df, target, fit=True)

        print("Feature engineering complete!")
        return df

    def transform(self, df: pd.DataFrame, target: str = 'revenue_usd_millions') -> pd.DataFrame:
        """Transform new data using fitted pipeline"""
        df = df.copy()
        df = self.create_derived_features(df)
        df = self.handle_missing_values(df, fit=False)
        df = self.encode_categorical_features(df, fit=False)

        # Drop the original categorical columns before selecting features
        categorical_base_cols = [
            'pitchbook_primary_industry_sector',
            'pitchbook_primary_industry_group',
            'pitchbook_hq_country',
            'latest_funding_type',
            'crunchbase_revenue_range',
            'company_size_category'
        ]
        cols_to_drop = [col for col in categorical_base_cols if col in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        df = self.select_features(df, target)
        df = self.scale_features(df, target, fit=False)
        return df

    def save(self, filepath: str):
        """Save the feature engineer"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Feature engineer saved to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'FeatureEngineer':
        """Load a saved feature engineer"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


def prepare_data(csv_path: str, target: str = 'revenue_usd_millions',
                 test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
    """
    Load and prepare data for modeling

    Returns:
        Dictionary containing X_train, X_test, y_train, y_test, feature_engineer
    """
    from sklearn.model_selection import train_test_split

    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records")

    # Initialize feature engineer
    feature_engineer = FeatureEngineer()

    # Apply feature engineering
    df_processed = feature_engineer.fit_transform(df, target)

    # Split features and target
    X = df_processed.drop(columns=[target])
    y = df_processed[target]

    # Log transform target (revenue)
    y_log = np.log1p(y)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_log, test_size=test_size, random_state=random_state
    )

    print(f"\nData split:")
    print(f"Training set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")

    return {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'y_train_original': np.expm1(y_train),
        'y_test_original': np.expm1(y_test),
        'feature_engineer': feature_engineer,
        'feature_names': feature_engineer.feature_names
    }


if __name__ == "__main__":
    # Test the preprocessing pipeline
    data = prepare_data('ml_features_combined_cleaned.csv')
    print("\n" + "="*80)
    print("PREPROCESSING COMPLETE")
    print("="*80)
    print(f"Number of features: {len(data['feature_names'])}")
    print(f"Training samples: {len(data['X_train'])}")
    print(f"Test samples: {len(data['X_test'])}")
    print(f"\nFeature names: {data['feature_names'][:10]}...")
