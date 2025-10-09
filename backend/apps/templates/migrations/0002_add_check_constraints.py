# Generated manually - Fase R
# Adiciona CHECK constraints SQL que Django não suporta nativamente

from django.db import migrations


class Migration(migrations.Migration):
    """
    Adiciona CHECK constraints para validações a nível de banco de dados.
    
    Constraints:
    -----------
    1. point_template.ptype: deve ser 'num', 'bool', 'enum' ou 'text'
    2. point_template.polarity: deve ser 'normal' ou 'inverted' (se preenchido)
    3. dashboard_template.schema: deve ser 'v1'
    """

    dependencies = [
        ('templates', '0001_initial'),
    ]

    operations = [
        # ============================================================================
        # CHECK CONSTRAINTS para point_template
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- CHECK: ptype deve ser 'num', 'bool', 'enum' ou 'text'
            ALTER TABLE point_template
            ADD CONSTRAINT point_template_ptype_check
            CHECK (ptype IN ('num', 'bool', 'enum', 'text'));
            """,
            reverse_sql="""
            ALTER TABLE point_template
            DROP CONSTRAINT IF EXISTS point_template_ptype_check;
            """
        ),
        
        migrations.RunSQL(
            sql="""
            -- CHECK: polarity deve ser 'normal' ou 'inverted' (se preenchido)
            ALTER TABLE point_template
            ADD CONSTRAINT point_template_polarity_check
            CHECK (polarity IS NULL OR polarity IN ('normal', 'inverted'));
            """,
            reverse_sql="""
            ALTER TABLE point_template
            DROP CONSTRAINT IF EXISTS point_template_polarity_check;
            """
        ),
        
        # ============================================================================
        # CHECK CONSTRAINTS para dashboard_template
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- CHECK: schema deve ser 'v1'
            ALTER TABLE dashboard_template
            ADD CONSTRAINT dashboard_template_schema_check
            CHECK (schema = 'v1');
            """,
            reverse_sql="""
            ALTER TABLE dashboard_template
            DROP CONSTRAINT IF EXISTS dashboard_template_schema_check;
            """
        ),
        
        # ============================================================================
        # ÍNDICES ADICIONAIS para performance
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Índice para buscar point_templates por device_template
            CREATE INDEX IF NOT EXISTS point_template_device_template_idx
            ON point_template(device_template_id);
            
            -- Índice para buscar dashboard_templates por device_template
            CREATE INDEX IF NOT EXISTS dashboard_template_device_template_idx
            ON dashboard_template(device_template_id);
            
            -- Índice para buscar device_templates não depreciados
            CREATE INDEX IF NOT EXISTS device_template_not_superseded_idx
            ON device_template(code, version)
            WHERE superseded_by_id IS NULL;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS point_template_device_template_idx;
            DROP INDEX IF EXISTS dashboard_template_device_template_idx;
            DROP INDEX IF EXISTS device_template_not_superseded_idx;
            """
        ),
    ]
