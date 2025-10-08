"""
Tipos compartilhados para adapters.
"""

from typing import Tuple, List, Optional, Any
from datetime import datetime


# Formato normalizado: (timestamp, lista de pontos, metadata)
# Cada ponto: (nome, tipo, valor, unidade_opcional)
Normalized = Tuple[
    datetime,  # timestamp como datetime object (não string!)
    List[Tuple[str, str, Any, Optional[str]]],  # [(name, type, value, unit), ...]
    dict  # metadata adicional
]
