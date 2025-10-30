SET search_path TO umc, public;

-- Inserir alertas de teste diretamente no banco
INSERT INTO alerts_alert (
  rule_id,
  asset_tag,
  parameter_key,
  parameter_value,
  threshold,
  severity,
  message,
  triggered_at,
  acknowledged,
  resolved,
  notes
) VALUES 
  (
    1,  -- ID da regra "Temperatura Alta - Chiller 001"
    'CHILLER-001',
    'sensor_13',
    30.0,
    25.0,
    'High',
    'Temperatura acima do limite: 30.0°C (limite: 25.0°C)',
    NOW(),
    false,
    false,
    ''
  ),
  (
    2,  -- ID da regra "Chiller"
    'CHILLER-001',
    'sensor_15',
    15.0,
    10.0,
    'High',
    'Sensor 15 acima do limite: 15.0 (limite: 10.0)',
    NOW(),
    false,
    false,
    ''
  );

-- Verificar alertas criados
SELECT id, rule_id, asset_tag, severity, message, acknowledged, resolved, triggered_at
FROM alerts_alert
ORDER BY triggered_at DESC
LIMIT 5;
