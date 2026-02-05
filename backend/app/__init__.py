from flask import Flask
from flask_cors import CORS
from app.config import config
from app.extensions import db, login_manager, bcrypt, migrate

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    CORS(app, 
         resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    
    from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule
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
    
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    return app
