SET search_path TO umc, public;

-- Criar readings que vão disparar alertas
INSERT INTO reading (device_id, sensor_id, value, labels, ts, created_at) 
VALUES 
  ('CHILLER-001', 'sensor_13', 30.0, '{"unit": "°C"}'::jsonb, NOW(), NOW()),
  ('CHILLER-001', 'sensor_15', 15.0, '{}'::jsonb, NOW(), NOW());

-- Verificar readings criados
SELECT id, device_id, sensor_id, value, ts 
FROM reading 
WHERE device_id = 'CHILLER-001' 
ORDER BY ts DESC 
LIMIT 5;
