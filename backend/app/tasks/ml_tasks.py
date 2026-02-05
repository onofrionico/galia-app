"""
Background tasks for ML model maintenance.
These should be run periodically via cron or task scheduler.
"""
from app import create_app
from app.ml.staffing_predictor import StaffingPredictor
from app.services.ml_accuracy_service import MLAccuracyService
from app.services.alert_service import AlertService
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def daily_accuracy_update():
    """
    Update accuracy metrics for yesterday.
    Should run daily at midnight or early morning.
    """
    with app.app_context():
        logger.info("Starting daily accuracy update...")
        
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        result = MLAccuracyService.update_accuracy_for_date(yesterday)
        
        if result['success']:
            logger.info(f"✅ Updated accuracy for {yesterday}: {result['records_updated']} records")
        else:
            logger.error(f"❌ Failed to update accuracy for {yesterday}")
        
        return result

def weekly_retrain_check():
    """
    Check if model needs retraining.
    Should run weekly (e.g., every Monday).
    """
    with app.app_context():
        logger.info("Checking if model needs retraining...")
        
        result = MLAccuracyService.should_retrain_model()
        
        if result['should_retrain']:
            logger.warning(f"⚠️ Model retraining recommended!")
            logger.warning(f"   Recent MAPE: {result['recent_mape']}%")
            logger.warning(f"   Historical MAPE: {result['historical_mape']}%")
            logger.warning(f"   Degradation: {result['degradation_percentage']}%")
            
            # Optionally auto-retrain
            # auto_retrain = input("Retrain now? (y/n): ")
            # if auto_retrain.lower() == 'y':
            #     predictor = StaffingPredictor()
            #     train_result = predictor.train()
            #     logger.info(f"✅ Model retrained: {train_result}")
        else:
            logger.info(f"✅ Model accuracy is stable (MAPE: {result['recent_mape']}%)")
        
        return result

def weekly_prediction_generation():
    """
    Generate predictions for next 2 weeks.
    Should run weekly (e.g., every Sunday).
    """
    with app.app_context():
        logger.info("Generating predictions for next 2 weeks...")
        
        predictor = StaffingPredictor()
        
        start_date = datetime.now().date()
        end_date = start_date + timedelta(weeks=2)
        
        result = predictor.generate_predictions(start_date, end_date)
        
        if result['success']:
            logger.info(f"✅ Generated {result['predictions_created']} predictions")
        else:
            logger.error(f"❌ Failed to generate predictions: {result.get('error')}")
        
        return result

def daily_alert_check():
    """
    Check for critical alerts and send notifications.
    Should run daily.
    """
    with app.app_context():
        logger.info("Checking for critical alerts...")
        
        result = AlertService.notify_critical_alerts()
        
        if result['success']:
            if result['notifications_sent'] > 0:
                logger.warning(f"⚠️ Sent {result['notifications_sent']} critical alert notifications")
            else:
                logger.info("✅ No critical alerts")
        
        return result

def monthly_full_retrain():
    """
    Full model retraining with all available data.
    Should run monthly (e.g., first day of month).
    """
    with app.app_context():
        logger.info("Starting monthly full model retraining...")
        
        predictor = StaffingPredictor()
        
        # Train with more weeks of data
        result = predictor.train(min_weeks=12)
        
        if result['success']:
            logger.info(f"✅ Model retrained successfully!")
            logger.info(f"   Records: {result['records']}")
            logger.info(f"   Train Score: {result['train_score']}")
            logger.info(f"   Test Score: {result['test_score']}")
            
            # Generate predictions for next month
            start_date = datetime.now().date()
            end_date = start_date + timedelta(weeks=4)
            
            pred_result = predictor.generate_predictions(start_date, end_date)
            logger.info(f"✅ Generated {pred_result['predictions_created']} predictions")
        else:
            logger.error(f"❌ Failed to retrain model: {result.get('error')}")
        
        return result

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ml_tasks.py [daily_accuracy|weekly_retrain_check|weekly_predictions|daily_alerts|monthly_retrain]")
        sys.exit(1)
    
    task = sys.argv[1]
    
    if task == 'daily_accuracy':
        daily_accuracy_update()
    elif task == 'weekly_retrain_check':
        weekly_retrain_check()
    elif task == 'weekly_predictions':
        weekly_prediction_generation()
    elif task == 'daily_alerts':
        daily_alert_check()
    elif task == 'monthly_retrain':
        monthly_full_retrain()
    else:
        print(f"Unknown task: {task}")
        sys.exit(1)
