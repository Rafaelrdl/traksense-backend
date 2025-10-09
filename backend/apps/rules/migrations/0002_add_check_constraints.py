# Generated manually - Fase R
# Adiciona CHECK constraints SQL para Rule e RuleEvent models

from django.db import migrations


class Migration(migrations.Migration):
    """
    Adiciona CHECK constraints para Rule e RuleEvent.
    
    Constraints:
    -----------
    1. Rule.type: deve ser 'threshold', 'window' ou 'hysteresis'
    2. RuleEvent.state: deve ser 'ACTIVE' ou 'CLEARED'
    """

    dependencies = [
        ('rules', '0001_initial'),
    ]

    operations = [
        # ============================================================================
        # CHECK CONSTRAINTS para Rule
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- CHECK: type deve ser 'threshold', 'window' ou 'hysteresis'
            ALTER TABLE rules_rule
            ADD CONSTRAINT rules_rule_type_check
            CHECK (type IN ('threshold', 'window', 'hysteresis'));
            """,
            reverse_sql="""
            ALTER TABLE rules_rule
            DROP CONSTRAINT IF EXISTS rules_rule_type_check;
            """
        ),
        
        # ============================================================================
        # CHECK CONSTRAINTS para RuleEvent
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- CHECK: state deve ser 'ACTIVE' ou 'CLEARED'
            ALTER TABLE rules_ruleevent
            ADD CONSTRAINT rules_ruleevent_state_check
            CHECK (state IN ('ACTIVE', 'CLEARED'));
            """,
            reverse_sql="""
            ALTER TABLE rules_ruleevent
            DROP CONSTRAINT IF EXISTS rules_ruleevent_state_check;
            """
        ),
    ]
