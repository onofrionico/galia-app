from flask import Flask, request
from flask_cors import CORS
from app.config import config
from app.extensions import db, login_manager, bcrypt, migrate

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Log CORS configuration
    print(f"[CORS CONFIG] Allowed origins: {app.config['CORS_ORIGINS']}")
    
    CORS(app, 
         resources={r"/api/*": {
             "origins": app.config['CORS_ORIGINS'],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "max_age": 3600
         }},
         supports_credentials=True)
    
    # Middleware para loguear todas las requests
    @app.before_request
    def log_request_info():
        print(f"\n[REQUEST] {request.method} {request.path}")
        print(f"[REQUEST] Origin: {request.headers.get('Origin', 'No Origin header')}")
        print(f"[REQUEST] Authorization: {request.headers.get('Authorization', 'No Auth header')[:50] if request.headers.get('Authorization') else 'No Auth header'}")
        print(f"[REQUEST] Content-Type: {request.headers.get('Content-Type', 'No Content-Type')}")
        
        # Manejar preflight OPTIONS requests explícitamente
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            return response
    
    @app.after_request
    def log_response_info(response):
        print(f"[RESPONSE] Status: {response.status}")
        print(f"[RESPONSE] CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
        return response
    
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    
    from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import
    app.register_blueprint(auth.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(shifts.bp)
    app.register_blueprint(schedule_summary.bp)
    app.register_blueprint(notifications.bp)
    app.register_blueprint(coverage.bp)
    app.register_blueprint(ml_predictions.bp)
    app.register_blueprint(ml_dashboard.bp)
    app.register_blueprint(sales.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(employees.bp)
    app.register_blueprint(employee_schedule.bp)
    app.register_blueprint(job_positions.bp)
    app.register_blueprint(time_tracking.bp)
    app.register_blueprint(payroll.payroll_bp)
    app.register_blueprint(csv_import.csv_import_bp)
    
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    return app
