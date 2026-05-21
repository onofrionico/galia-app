import os
import sys
from app import create_app

app = create_app('development')

# Listar todos los endpoints registrados
print("📋 Endpoints registrados en la aplicación:\n")

for rule in app.url_map.iter_rules():
    if 'modules' in rule.rule or 'permissions' in rule.rule or 'auth' in rule.rule:
        print(f"  {rule.rule}")
        print(f"    Métodos: {', '.join(rule.methods - {'HEAD', 'OPTIONS'})}")
        print(f"    Función: {rule.endpoint}\n")
