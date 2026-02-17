"""
Trend Forecasting Module.
Uses linear regression to predict future trends.

IMPORTANT: This provides directional forecasting, not exact predictions.
YouTube data is inherently noisy, and external factors (trends, algorithm
changes, viral content) can significantly impact results. Use these forecasts
as guidance rather than precise predictions.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


class TrendForecasting:
    """Predict future trends using linear regression."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with video data."""
        self.df = df.copy()
        self.df['date'] = pd.to_datetime(self.df['published_at']).dt.date
    
    def prepare_data(self, metric: str = 'views') -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for forecasting."""
        # Aggregate by date
        daily_data = self.df.groupby('date')[metric].sum().reset_index()
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        daily_data['days'] = (daily_data['date'] - daily_data['date'].min()).dt.days
        
        X = daily_data['days'].values.reshape(-1, 1)
        y = daily_data[metric].values
        
        return X, y
    
    def forecast_views(self, days: int = 30) -> Dict:
        """Forecast views for the next N days."""
        X, y = self.prepare_data('views')
        
        if len(X) < 2:
            return {'error': 'Not enough data for forecasting'}
        
        # Choose model: use simple polynomial regression when we have enough history,
        # otherwise fall back to linear regression.
        use_poly = len(X) >= 10
        
        last_date = self.df['date'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, days + 1)]
        future_days = [(d - self.df['date'].min()).days for d in future_dates]
        
        X_future = np.array(future_days).reshape(-1, 1)
        
        if use_poly:
            poly = PolynomialFeatures(degree=2, include_bias=False)
            X_trans = poly.fit_transform(X)
            X_future_trans = poly.transform(X_future)
            
            model = LinearRegression()
            model.fit(X_trans, y)
            predictions = model.predict(X_future_trans)
            
            y_pred = model.predict(X_trans)
            r_squared = float(model.score(X_trans, y))
            model_type = "polynomial"
        else:
            model = LinearRegression()
            model.fit(X, y)
            predictions = model.predict(X_future)
            
            y_pred = model.predict(X)
            r_squared = float(model.score(X, y))
            model_type = "linear"
        
        # Get historical stats for capping
        max_views = np.max(y)
        min_views = np.min(y)
        
        # Cap predictions to reasonable bounds (between 50% and 150% of historical max)
        lower_bound = max(0, min_views * 0.5)
        upper_bound = max_views * 2  # Allow some growth but cap it
        
        predictions = np.clip(predictions, lower_bound, upper_bound)
        
        # Ensure no negative values
        predictions = np.maximum(predictions, 0)
        
        # Calculate confidence interval
        residuals = y - y_pred
        std_error = np.std(residuals)
        
        return {
            'predictions': predictions.tolist(),
            'dates': [d.isoformat() for d in future_dates],
            'model': {
                'type': model_type,
                'coefficient': float(model.coef_[0]),
                'intercept': float(model.intercept_),
                'r_squared': r_squared
            },
            'confidence_interval': {
                'lower': (predictions - 1.96 * std_error).tolist(),
                'upper': (predictions + 1.96 * std_error).tolist()
            },
            'total_forecasted_views': int(sum(predictions)),
            'average_daily_views': int(sum(predictions) / days)
        }
    
    def forecast_subscribers(self, days: int = 30) -> Dict:
        """Forecast subscriber growth for the next N days."""
        if 'subscribers_gained' not in self.df.columns:
            return {'error': 'Subscriber data not available'}
        
        X, y = self.prepare_data('subscribers_gained')
        
        if len(X) < 2:
            return {'error': 'Not enough data for forecasting'}
        
        # Fit model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict
        last_date = self.df['date'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, days + 1)]
        future_days = [(d - self.df['date'].min()).days for d in future_dates]
        
        X_future = np.array(future_days).reshape(-1, 1)
        predictions = model.predict(X_future)
        
        # Ensure non-negative
        predictions = np.maximum(predictions, 0)
        
        return {
            'predictions': predictions.tolist(),
            'dates': [d.isoformat() for d in future_dates],
            'model': {
                'coefficient': float(model.coef_[0]),
                'intercept': float(model.intercept_),
                'r_squared': float(model.score(X, y))
            },
            'total_forecasted_subscribers': int(sum(predictions)),
            'average_daily_subscribers': int(sum(predictions) / days)
        }
    
    def forecast_engagement(self, days: int = 30) -> Dict:
        """Forecast engagement rate for the next N days."""
        X, y = self.prepare_data('engagement_rate')
        
        if len(X) < 2:
            return {'error': 'Not enough data for forecasting'}
        
        # Fit model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict
        last_date = self.df['date'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, days + 1)]
        future_days = [(d - self.df['date'].min()).days for d in future_dates]
        
        X_future = np.array(future_days).reshape(-1, 1)
        predictions = model.predict(X_future)
        
        # Ensure 0-100 range
        predictions = np.clip(predictions, 0, 100)
        
        return {
            'predictions': predictions.tolist(),
            'dates': [d.isoformat() for d in future_dates],
            'model': {
                'coefficient': float(model.coef_[0]),
                'intercept': float(model.intercept_),
                'r_squared': float(model.score(X, y))
            },
            'average_engagement_forecast': float(sum(predictions) / days)
        }
    
    def get_growth_trajectory(self) -> Dict:
        """Get overall growth trajectory analysis."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # Calculate growth rates
        sorted_df = self.df.sort_values('published_at')
        
        # Split into halves
        mid_point = len(sorted_df) // 2
        first_half = sorted_df.iloc[:mid_point]
        second_half = sorted_df.iloc[mid_point:]
        
        views_growth = 0
        if first_half['views'].sum() > 0:
            views_growth = ((second_half['views'].sum() - first_half['views'].sum()) 
                          / first_half['views'].sum() * 100)
        
        engagement_growth = 0
        if first_half['engagement_rate'].mean() > 0:
            engagement_growth = ((second_half['engagement_rate'].mean() - first_half['engagement_rate'].mean()) 
                               / first_half['engagement_rate'].mean() * 100)
        
        return {
            'views_growth_percentage': float(views_growth),
            'engagement_growth_percentage': float(engagement_growth),
            'trend': 'Growing' if views_growth > 0 else 'Declining',
            'first_half_avg_views': float(first_half['views'].mean()),
            'second_half_avg_views': float(second_half['views'].mean()),
            'recommendation': self._get_growth_recommendation(views_growth, engagement_growth)
        }
    
    def _get_growth_recommendation(self, views_growth: float, engagement_growth: float) -> str:
        """Get growth recommendation based on trends."""
        if views_growth > 20 and engagement_growth > 10:
            return "Excellent growth! Continue current strategy."
        elif views_growth > 0 and engagement_growth > 0:
            return "Moderate growth. Consider increasing upload frequency."
        elif views_growth > 0 and engagement_growth < 0:
            return "Views up but engagement down. Focus on content quality."
        elif views_growth < 0 and engagement_growth > 0:
            return "Fewer views but higher engagement. Content is resonating."
        else:
            return "Declining performance. Review content strategy and posting schedule."
    
    def forecast_all(self, days: int = 30) -> Dict:
        """Get complete forecast for all metrics."""
        return {
            'views_forecast': self.forecast_views(days),
            'subscribers_forecast': self.forecast_subscribers(days),
            'engagement_forecast': self.forecast_engagement(days),
            'growth_trajectory': self.get_growth_trajectory()
        }
    
    def get_forecast_dataframe(self, days: int = 30) -> pd.DataFrame:
        """Get a DataFrame with historical and forecast data for visualization."""
        if self.df.empty:
            return pd.DataFrame()
        
        try:
            # Get historical data
            df_sorted = self.df.sort_values('published_at').copy()
            df_sorted['date'] = pd.to_datetime(df_sorted['published_at']).dt.date
            daily_views = df_sorted.groupby('date')['views'].sum().reset_index()
            daily_views['date'] = pd.to_datetime(daily_views['date'])
            
            # Get forecast
            forecast_result = self.forecast_views(days)
            
            if 'error' in forecast_result:
                return pd.DataFrame()
            
            # Create forecast dataframe
            forecast_dates = [pd.to_datetime(d) for d in forecast_result['dates']]
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'forecast': forecast_result['predictions']
            })
            
            # Combine historical and forecast
            result = pd.DataFrame()
            
            # Historical (with some padding for visualization)
            if not daily_views.empty:
                result = pd.concat([result, daily_views[['date', 'views']].rename(columns={'views': 'historical'})], ignore_index=True)
            
            # Forecast
            if not forecast_df.empty:
                result = pd.concat([result, forecast_df], ignore_index=True)
            
            result = result.set_index('date')
            return result
            
        except Exception as e:
            print(f"Error creating forecast dataframe: {e}")
            return pd.DataFrame()


def forecast_trends(df: pd.DataFrame, days: int = 30) -> TrendForecasting:
    """Create TrendForecasting instance."""
    return TrendForecasting(df)


# Test forecasting
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    sample_data = pd.DataFrame({
        'video_id': [f'video_{i}' for i in range(1, 31)],
        'title': [f'Video {i}' for i in range(1, 31)],
        'published_at': dates,
        'views': [1000 + i * 100 + np.random.randint(-200, 200) for i in range(30)],
        'likes': [100 + i * 10 + np.random.randint(-20, 20) for i in range(30)],
        'comments': [20 + i * 2 + np.random.randint(-5, 5) for i in range(30)],
        'engagement_rate': [6.0 + i * 0.1 for i in range(30)],
        'subscribers_gained': [100 + i * 5 + np.random.randint(-20, 20) for i in range(30)]
    })
    
    forecast = TrendForecasting(sample_data)
    
    print("Views Forecast (7 days):")
    views_fc = forecast.forecast_views(7)
    print(f"Total: {views_fc.get('total_forecasted_views', 'N/A')}")
    print(f"Daily Average: {views_fc.get('average_daily_views', 'N/A')}")
    
    print("\nSubscribers Forecast (7 days):")
    subs_fc = forecast.forecast_subscribers(7)
    print(f"Total: {subs_fc.get('total_forecasted_subscribers', 'N/A')}")
    
    print("\nGrowth Trajectory:")
    trajectory = forecast.get_growth_trajectory()
    print(f"Trend: {trajectory.get('trend', 'N/A')}")
    print(f"Recommendation: {trajectory.get('recommendation', 'N/A')}")
