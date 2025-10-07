"""
Validators - Dashboards App

Validadores customizados para modelos de dashboard.
Usa jsonschema para validar estrutura JSON de DashboardTemplate.

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

import json
from pathlib import Path
from jsonschema import validate, Draft7Validator, ValidationError as JsonSchemaError


def validate_dashboard_template(payload: dict):
    """
    Valida a estrutura JSON de um DashboardTemplate contra o schema v1.
    
    Args:
        payload: Dicionário JSON a ser validado
        
    Raises:
        JsonSchemaError: Se o JSON for inválido
        
    Uso:
        from dashboards.validators import validate_dashboard_template
        
        try:
            validate_dashboard_template(dashboard_json)
        except JsonSchemaError as e:
            print(f"JSON inválido: {e.message}")
    """
    # Carregar schema do arquivo
    schema_path = Path(__file__).parent / "schema" / "dashboard_template_v1.json"
    
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema JSON não encontrado: {schema_path}"
        )
    
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    
    # Validar usando Draft7Validator (compatível com draft-07)
    validator = Draft7Validator(schema)
    validator.validate(payload)
