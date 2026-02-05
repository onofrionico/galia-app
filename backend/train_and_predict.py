"""
Script to train the ML model and generate predictions.
Run this after generating sample data.
"""
from app import create_app
from app.ml.staffing_predictor import StaffingPredictor
from datetime import datetime, timedelta

app = create_app()

def train_and_predict():
    """Train model and generate predictions for next 2 weeks"""
    with app.app_context():
        print("🧠 Iniciando entrenamiento del modelo ML...")
        print("-" * 50)
        
        # Initialize predictor
        predictor = StaffingPredictor()
        
        # Train model
        print("\n1. Entrenando modelo con datos históricos...")
        result = predictor.train(min_weeks=8)
        
        if result['success']:
            print(f"   ✅ Modelo entrenado exitosamente!")
            print(f"   - Registros utilizados: {result['records']}")
            print(f"   - Score de entrenamiento: {result['train_score']}")
            print(f"   - Score de prueba: {result['test_score']}")
            print(f"   - Versión del modelo: {result['model_version']}")
        else:
            print(f"   ❌ Error: {result.get('error')}")
            return
        
        # Generate predictions for next 2 weeks
        print("\n2. Generando predicciones para las próximas 2 semanas...")
        start_date = datetime.now().date()
        end_date = start_date + timedelta(weeks=2)
        
        pred_result = predictor.generate_predictions(start_date, end_date)
        
        if pred_result['success']:
            print(f"   ✅ Predicciones generadas!")
            print(f"   - Total de predicciones: {pred_result['predictions_created']}")
            print(f"   - Rango: {pred_result['date_range']}")
        else:
            print(f"   ❌ Error: {pred_result.get('error')}")
            return
        
        print("\n" + "=" * 50)
        print("✨ ¡Proceso completado exitosamente!")
        print("=" * 50)
        print("\n📊 Ahora puedes:")
        print("   1. Crear una nueva grilla horaria")
        print("   2. Ver las recomendaciones ML en el modal")
        print("   3. Usar las predicciones para optimizar el personal")

if __name__ == '__main__':
    train_and_predict()
