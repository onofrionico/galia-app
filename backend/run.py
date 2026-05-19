import os
import logging
from app import create_app
from app.extensions import db

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

# Enable detailed error logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
