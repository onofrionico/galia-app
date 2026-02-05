import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime, timedelta
from app.extensions import db
from app.models.staffing_metrics import StaffingMetrics, StaffingPrediction
from app.models.ml_tracking import MLModelVersion, Holiday

class StaffingPredictor:
    """
    Machine Learning model for predicting staffing needs based on historical data.
    Uses Random Forest Regressor to predict sales and recommend staff count.
    """
    
    def __init__(self):
        self.sales_model = None
        self.staff_model = None
        self.scaler = StandardScaler()
        self.model_version = "1.0.0"
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        
        # Create models directory if it doesn't exist
        os.makedirs(self.models_dir, exist_ok=True)
    
    def prepare_features(self, metrics_df):
        """
        Prepare features from metrics dataframe for ML model.
        
        Features:
        - hour: Hour of day (0-23)
        - day_of_week: Day of week (0-6, Monday=0)
        - is_weekend: Boolean
        - is_morning: 6-12
        - is_afternoon: 12-18
        - is_evening: 18-24
        - employees_scheduled: Number of employees
        - hour_sin, hour_cos: Cyclical encoding of hour
        - day_sin, day_cos: Cyclical encoding of day
        """
        df = metrics_df.copy()
        
        # Cyclical features for hour (24-hour cycle)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Cyclical features for day of week (7-day cycle)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Time of day features
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_morning'] = ((df['hour'] >= 6) & (df['hour'] < 12)).astype(int)
        df['is_afternoon'] = ((df['hour'] >= 12) & (df['hour'] < 18)).astype(int)
        df['is_evening'] = ((df['hour'] >= 18) & (df['hour'] < 24)).astype(int)
        
        # Holiday feature - check database
        df['is_holiday'] = 0
        df['holiday_impact'] = 1.0
        
        for idx, row in df.iterrows():
            holiday = Holiday.query.filter_by(date=row['date']).first()
            if holiday:
                df.at[idx, 'is_holiday'] = 1
                df.at[idx, 'holiday_impact'] = holiday.impact_multiplier
        
        return df
    
    def load_training_data(self, min_weeks=4):
        """
        Load historical data from database for training.
        Returns pandas DataFrame with metrics.
        """
        # Get data from last N weeks
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=min_weeks)
        
        metrics = StaffingMetrics.query.filter(
            StaffingMetrics.date >= start_date,
            StaffingMetrics.date <= end_date
        ).all()
        
        if not metrics:
            return None
        
        # Convert to DataFrame
        data = []
        for m in metrics:
            data.append({
                'date': m.date,
                'hour': m.hour,
                'day_of_week': m.day_of_week,
                'employees_scheduled': m.employees_scheduled,
                'sales_count': m.sales_count,
                'sales_amount': float(m.sales_amount) if m.sales_amount else 0,
                'is_holiday': m.is_holiday
            })
        
        return pd.DataFrame(data)
    
    def train(self, min_weeks=8, test_size=0.2):
        """
        Train the ML models using historical data.
        
        Returns:
        - Dictionary with training metrics (accuracy, etc.)
        """
        # Load data
        df = self.load_training_data(min_weeks=min_weeks)
        
        if df is None or len(df) < 50:
            return {
                'success': False,
                'error': 'Insufficient data for training (minimum 50 records needed)',
                'records': len(df) if df is not None else 0
            }
        
        # Prepare features
        df = self.prepare_features(df)
        
        # Feature columns
        feature_cols = [
            'hour', 'day_of_week', 'is_weekend', 'is_morning', 
            'is_afternoon', 'is_evening', 'is_holiday', 'holiday_impact',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
        ]
        
        X = df[feature_cols].values
        y_sales = df['sales_count'].values
        y_amount = df['sales_amount'].values
        
        # Split data
        X_train, X_test, y_sales_train, y_sales_test = train_test_split(
            X, y_sales, test_size=test_size, random_state=42
        )
        
        _, _, y_amount_train, y_amount_test = train_test_split(
            X, y_amount, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train sales count model
        self.sales_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.sales_model.fit(X_train_scaled, y_sales_train)
        
        # Evaluate
        train_score = self.sales_model.score(X_train_scaled, y_sales_train)
        test_score = self.sales_model.score(X_test_scaled, y_sales_test)
        
        # Save models
        self.save_models()
        
        # Save model version to database
        model_version_record = MLModelVersion(
            version=self.model_version,
            trained_at=datetime.utcnow(),
            training_records=len(df),
            train_score=train_score,
            test_score=test_score,
            features_used=feature_cols,
            hyperparameters={
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5
            },
            is_active=True
        )
        
        # Deactivate previous versions
        MLModelVersion.query.update({'is_active': False})
        
        db.session.add(model_version_record)
        db.session.commit()
        
        return {
            'success': True,
            'records': len(df),
            'train_score': round(train_score, 3),
            'test_score': round(test_score, 3),
            'model_version': self.model_version,
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def predict_for_date_hour(self, date, hour):
        """
        Predict sales and recommend staff for a specific date and hour.
        
        Returns:
        - predicted_sales_count
        - predicted_sales_amount
        - recommended_staff_count
        - confidence_score
        """
        if self.sales_model is None:
            self.load_models()
        
        if self.sales_model is None:
            return None
        
        # Prepare features
        day_of_week = date.weekday()
        
        # Check for holiday
        holiday = Holiday.query.filter_by(date=date).first()
        is_holiday = 1 if holiday else 0
        holiday_impact = holiday.impact_multiplier if holiday else 1.0
        
        features = {
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': 1 if day_of_week >= 5 else 0,
            'is_morning': 1 if 6 <= hour < 12 else 0,
            'is_afternoon': 1 if 12 <= hour < 18 else 0,
            'is_evening': 1 if 18 <= hour < 24 else 0,
            'is_holiday': is_holiday,
            'holiday_impact': holiday_impact,
            'hour_sin': np.sin(2 * np.pi * hour / 24),
            'hour_cos': np.cos(2 * np.pi * hour / 24),
            'day_sin': np.sin(2 * np.pi * day_of_week / 7),
            'day_cos': np.cos(2 * np.pi * day_of_week / 7)
        }
        
        feature_cols = [
            'hour', 'day_of_week', 'is_weekend', 'is_morning', 
            'is_afternoon', 'is_evening', 'is_holiday', 'holiday_impact',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
        ]
        
        X = np.array([[features[col] for col in feature_cols]])
        X_scaled = self.scaler.transform(X)
        
        # Predict sales count
        predicted_sales = max(0, self.sales_model.predict(X_scaled)[0])
        
        # Estimate sales amount (average $500 per sale)
        predicted_amount = predicted_sales * 500
        
        # Calculate recommended staff (1 staff per 8-10 sales, minimum 1)
        recommended_staff = max(1, int(np.ceil(predicted_sales / 9)))
        
        # Confidence based on model's feature importances and variance
        confidence = min(0.95, self.sales_model.score(X_scaled, [predicted_sales]))
        
        return {
            'predicted_sales_count': int(round(predicted_sales)),
            'predicted_sales_amount': round(predicted_amount, 2),
            'recommended_staff_count': recommended_staff,
            'confidence_score': round(confidence, 2)
        }
    
    def generate_predictions(self, start_date, end_date):
        """
        Generate predictions for a date range and save to database.
        """
        if self.sales_model is None:
            self.load_models()
        
        if self.sales_model is None:
            return {'success': False, 'error': 'Model not trained'}
        
        predictions_created = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Generate predictions for business hours (8-20)
            for hour in range(8, 21):
                prediction = self.predict_for_date_hour(current_date, hour)
                
                if prediction:
                    # Check if prediction already exists
                    existing = StaffingPrediction.query.filter_by(
                        date=current_date,
                        hour=hour
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.predicted_sales_count = prediction['predicted_sales_count']
                        existing.predicted_sales_amount = prediction['predicted_sales_amount']
                        existing.recommended_staff_count = prediction['recommended_staff_count']
                        existing.confidence_score = prediction['confidence_score']
                        existing.model_version = self.model_version
                    else:
                        # Create new
                        new_prediction = StaffingPrediction(
                            date=current_date,
                            hour=hour,
                            predicted_sales_count=prediction['predicted_sales_count'],
                            predicted_sales_amount=prediction['predicted_sales_amount'],
                            recommended_staff_count=prediction['recommended_staff_count'],
                            confidence_score=prediction['confidence_score'],
                            model_version=self.model_version
                        )
                        db.session.add(new_prediction)
                    
                    predictions_created += 1
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        
        return {
            'success': True,
            'predictions_created': predictions_created,
            'date_range': f"{start_date} to {end_date}"
        }
    
    def save_models(self):
        """Save trained models to disk."""
        if self.sales_model:
            joblib.dump(self.sales_model, os.path.join(self.models_dir, 'sales_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'scaler.pkl'))
            
            # Save metadata
            metadata = {
                'model_version': self.model_version,
                'trained_at': datetime.utcnow().isoformat()
            }
            joblib.dump(metadata, os.path.join(self.models_dir, 'metadata.pkl'))
    
    def load_models(self):
        """Load trained models from disk."""
        sales_model_path = os.path.join(self.models_dir, 'sales_model.pkl')
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        
        if os.path.exists(sales_model_path) and os.path.exists(scaler_path):
            self.sales_model = joblib.load(sales_model_path)
            self.scaler = joblib.load(scaler_path)
            
            # Load metadata if available
            metadata_path = os.path.join(self.models_dir, 'metadata.pkl')
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                self.model_version = metadata.get('model_version', '1.0.0')
            
            return True
        return False
