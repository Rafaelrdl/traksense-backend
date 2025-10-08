"""
Tipos compartilhados para adapters.
"""

from typing import Tuple, List, Optional, Any


# Formato normalizado: (timestamp, lista de pontos, metadata)
# Cada ponto: (nome, tipo, valor, unidade_opcional)
Normalized = Tuple[
    str,  # timestamp ISO 8601
    List[Tuple[str, str, Any, Optional[str]]],  # [(name, type, value, unit), ...]
    dict  # metadata adicional
]
