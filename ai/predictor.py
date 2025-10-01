import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from datetime import datetime
import pickle
import os

class QueuePredictor:
    """AI predictor for queue wait times and patient flow."""
    
    def __init__(self):
        self.wait_time_model = None
        self.patient_flow_model = None
        self.is_trained = False
        self.model_path = 'ai_models'
        
    def prepare_queue_data(self, queue_data):
        """Prepare queue data for machine learning."""
        if not queue_data:
            return None
            
        df = pd.DataFrame([{
            'queue_number': q.queue_number,
            'priority': 1 if q.priority == 'urgent' else 0.5 if q.priority == 'high' else 0,
            'hour_of_day': q.created_at.hour if q.created_at else 0,
            'day_of_week': q.created_at.weekday() if q.created_at else 0,
            'actual_wait_time': q.actual_wait_time or 0,
            'status': 1 if q.status == 'completed' else 0
        } for q in queue_data])
        
        return df
    
    def train_wait_time_model(self, queue_data):
        """Train model to predict patient wait times."""
        df = self.prepare_queue_data(queue_data)
        if df is None or len(df) < 10:
            return False
            
        # Filter completed entries with valid wait times
        completed_df = df[(df['status'] == 1) & (df['actual_wait_time'] > 0)]
        if len(completed_df) < 5:
            return False
            
        # Features and target
        features = ['priority', 'hour_of_day', 'day_of_week']
        X = completed_df[features]
        y = completed_df['actual_wait_time']
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.wait_time_model = LinearRegression()
        self.wait_time_model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.wait_time_model.predict(X_test)
        r2 = r2_score(y_test, y_pred) if len(y_test) > 1 else 0
        
        self.is_trained = True
        return r2 > 0.1  # Basic threshold for model quality
    
    def predict_wait_time(self, priority='normal', hour_of_day=None, day_of_week=None):
        """Predict wait time for a new patient."""
        if not self.is_trained or not self.wait_time_model:
            # Return default estimates based on priority
            base_time = 30 if priority == 'normal' else 20 if priority == 'high' else 10
            return base_time
            
        # Prepare features
        priority_value = 1 if priority == 'urgent' else 0.5 if priority == 'high' else 0
        hour = hour_of_day if hour_of_day is not None else datetime.now().hour
        day = day_of_week if day_of_week is not None else datetime.now().weekday()
        
        features = np.array([[priority_value, hour, day]])
        prediction = self.wait_time_model.predict(features)[0]
        
        # Ensure reasonable bounds
        return max(5, min(120, int(prediction)))
    
    def analyze_patient_flow(self, queue_data, payment_data):
        """Analyze patient flow patterns."""
        analysis = {
            'total_patients': len(queue_data) if queue_data else 0,
            'average_wait_time': 0,
            'peak_hours': [],
            'busiest_days': [],
            'revenue_trend': 0
        }
        
        if not queue_data:
            return analysis
            
        df = self.prepare_queue_data(queue_data)
        if df is None:
            return analysis
            
        # Calculate average wait time
        completed_df = df[df['actual_wait_time'] > 0]
        if len(completed_df) > 0:
            analysis['average_wait_time'] = completed_df['actual_wait_time'].mean()
        
        # Find peak hours
        hour_counts = df.groupby('hour_of_day').size()
        if len(hour_counts) > 0:
            peak_hours = hour_counts.nlargest(3).index.tolist()
            analysis['peak_hours'] = [f"{h}:00" for h in peak_hours]
        
        # Find busiest days
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = df.groupby('day_of_week').size()
        if len(day_counts) > 0:
            busy_days = day_counts.nlargest(3).index.tolist()
            analysis['busiest_days'] = [day_names[d] for d in busy_days]
        
        # Revenue analysis
        if payment_data:
            total_revenue = sum(p.total_amount for p in payment_data if p.status == 'paid')
            analysis['revenue_trend'] = total_revenue
        
        return analysis
    
    def save_models(self):
        """Save trained models to disk."""
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
            
        if self.wait_time_model:
            with open(f"{self.model_path}/wait_time_model.pkl", 'wb') as f:
                pickle.dump(self.wait_time_model, f)
                
        # Save metadata
        metadata = {
            'is_trained': self.is_trained,
            'last_trained': datetime.now().isoformat()
        }
        with open(f"{self.model_path}/metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)
    
    def load_models(self):
        """Load trained models from disk."""
        try:
            if os.path.exists(f"{self.model_path}/wait_time_model.pkl"):
                with open(f"{self.model_path}/wait_time_model.pkl", 'rb') as f:
                    self.wait_time_model = pickle.load(f)
                    
            if os.path.exists(f"{self.model_path}/metadata.pkl"):
                with open(f"{self.model_path}/metadata.pkl", 'rb') as f:
                    metadata = pickle.load(f)
                    self.is_trained = metadata.get('is_trained', False)
                    
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False

# Global predictor instance
predictor = QueuePredictor()