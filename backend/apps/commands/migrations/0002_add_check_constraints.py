# Generated manually - Fase R
# Adiciona CHECK constraints SQL para Command model

from django.db import migrations


class Migration(migrations.Migration):
    """
    Adiciona CHECK constraint para Command.status.
    
    Constraint:
    ----------
    status IN ('PENDING','ACK','TIMEOUT','ERROR')
    """

    dependencies = [
        ('commands', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- CHECK: status deve ser 'PENDING', 'ACK', 'TIMEOUT' ou 'ERROR'
            ALTER TABLE commands_command
            ADD CONSTRAINT commands_command_status_check
            CHECK (status IN ('PENDING', 'ACK', 'TIMEOUT', 'ERROR'));
            """,
            reverse_sql="""
            ALTER TABLE commands_command
            DROP CONSTRAINT IF EXISTS commands_command_status_check;
            """
        ),
        
        # Índice adicional para buscar por cmd_id (para ACKs)
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS commands_command_cmd_id_idx
            ON commands_command(cmd_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS commands_command_cmd_id_idx;
            """
        ),
    ]
