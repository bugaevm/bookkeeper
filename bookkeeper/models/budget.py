"""
Описан класс, представляющий бюджет
"""

from dataclasses import dataclass

@dataclass
class budget:
    """
    Бюджет, хранит лимит расходов (бюджет) за период (день/неделя/месяц)

    period - 0 если день, 1 если неделя, 2 если месяц
    limit - бюджет за этот период
    """

    period : int
    limit : int
