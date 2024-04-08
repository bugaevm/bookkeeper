"""
Описывает класс Presenter,
осуществляющий взаимодействие с базой данных
"""

from pony import orm
from datetime import datetime, timedelta

db = orm.Database()
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)


class Budget(db.Entity):
    """
    Бюджет, хранит лимит расходов (бюджет) за период (день/неделя/месяц)

    period - 0 если день, 1 если неделя, 2 если месяц
    limit - бюджет за этот период
    """

    obj_id = orm.PrimaryKey(int, auto=True)
    period = orm.Required(int)
    limit = orm.Required(float)


class Category(db.Entity):
    """
    Класс категории, хранит название и TODO ссылку на родителя
    """

    obj_id = orm.PrimaryKey(int, auto=True)
    name = orm.Required(str)


class Expense(db.Entity):
    """
    Расходная операция.
    amount - сумма
    category - id категории расходов
    expense_date - дата расхода
    comment - комментарий
    pk - id записи в базе данных
    """

    obj_id = orm.PrimaryKey(int, auto=True)
    amount = orm.Required(float)
    category_id = orm.Required(int)
    expense_date = orm.Required(datetime)
    comment = orm.Required(str)


db.generate_mapping(create_tables=True)


class Presenter:
    """
    Класс, осуществляющий общение с базой данных.
    Имеет методы для получения данных из базы и отправки данных в базу.
    """

    @orm.db_session
    def __init__(self):
        """
        Конструктор презентера.
        Создаёт фиксированные типы ограничения бюджета --- на день, неделю и месяц.
        """

        Budget(period=0, limit=0)
        Budget(period=1, limit=0)
        Budget(period=2, limit=0)

    def categories_get_by_name(self, category_name: str) -> list[Category]:
        """
        Получает список категорий с заданным именем.
        Так как не позволяется создавать две разные категории с одинаковым именем,
        такой список будет содержать один или ноль элементов.
        """

        count: int = Category.select().count()
        if count:
            return [
                cat for cat in Category.select()[:] if cat.name == category_name
            ]
        return []

    @orm.db_session
    def category_add(self, category_name: str) -> None:
        """
        Создаёт категорию с заданным именем.
        Проверяет, что имя уникально.
        """

        if self.categories_get_by_name(category_name):
            raise NameError(f"Category with name {category_name} already exists")

        Category(name=category_name)

    @orm.db_session
    def category_edit_name(self, cat_id: int, new_name: str) -> None:
        """
        Изменяет имя категории, заданной по id.
        Проверяет, что новое имя уникально.
        """

        if self.categories_get_by_name(new_name):
            raise NameError(f"Category with name {new_name} already exists")
        Category[cat_id].name = new_name

    @orm.db_session
    def categories_get_list(self) -> list[Category]:
        """
        Получает список всех категорий
        """

        return Category.select()[:]

    @orm.db_session
    def category_get_by_id(self, cat_id: int) -> Category:
        """
        Получает категорию по id.
        Проверяет корректность id.
        """

        try:
            return Category[cat_id]
        except orm.core.ObjectNotFound:
            raise ValueError("Category id is incorrect")

    @orm.db_session
    def category_delete(self, cat_id: int) -> None:
        """
        Удаляет категорию по id.
        """

        Category[cat_id].delete()

    @orm.db_session
    def budgets_get_by_period(self, period: int) -> list[Budget]:
        """
        Получает список бюджетов, соответствующих данному периоду
        0 --- день
        1 --- неделя
        2 --- месяц.
        Так как периоды бюджетов уникальны,
        список будет состоять из одного или нуля элементов.
        """

        count: int = Budget.select().count()
        if count:
            return [bdg for bdg in Budget.select()[:] if bdg.period == period]
        return []

    @orm.db_session
    def budget_get_by_period(self, period: int) -> Budget:
        """
        Получает бюджет, соответствующий данному периоду
        0 --- день
        1 --- неделя
        2 --- месяц.
        Проверяет корректность периода
        """

        bdgs: list[Budget] = self.budgets_get_by_period(period)
        if not bdgs:
            raise ValueError("Wrong period")
        return bdgs[0]

    @orm.db_session
    def budget_get_limit_for_period(self, period: int) -> float:
        """
        Получает лимит бюджета по периоду.
        """

        return self.budget_get_by_period(period).limit

    @orm.db_session
    def budget_edit_limit(self, bdg_id: int, new_limit: float) -> None:
        """
        Редактирует лимит бюджета, заданного с помощью id.
        Проверяет корректность id
        """

        try:
            Budget[bdg_id].limit = new_limit
        except orm.core.ObjectNotFound:
            raise ValueError("Budget id is incorrect")

    @orm.db_session
    def budget_get_sum_for_period(self, period: int) -> float:
        """
        Вычисляет сумму расходов за заданный период
        """

        match period:
            case 0:
                delta: timedelta = timedelta(days=1)
            case 1:
                delta: timedelta = timedelta(days=7)
            case 2:
                delta: timedelta = timedelta(days=30)
            case _:
                raise ValueError("Wrong period")

        dn: datetime = datetime.now()

        return sum(
            [exp.amount for exp in Expense.select()[:] if dn - exp.expense_date <= delta]
        )

    @orm.db_session
    def expense_add(self, cost: float, category_name: str, comment: str) -> None:
        """
        Добавляет расход в базу
        """

        cats: list[Category] = self.categories_get_by_name(category_name)
        if not cats:
            print(f"No category named {category_name}")
            raise NameError(f"No category named {category_name}")

        comment = comment if comment else "-"
        Expense(
            amount=cost, category_id=cats[0].obj_id,
            expense_date=datetime.now(), comment=comment
        )

    @orm.db_session
    def expense_get_by_id(self, exp_id: int) -> Expense:
        """
        Получает расход по id.
        Проверяет корректность id.
        """

        try:
            return Expense[exp_id]
        except orm.core.ObjectNotFound:
            raise ValueError("Expense id is incorrect")

    @orm.db_session
    def expense_edit_cost(self, exp_id: int, new_cost: float) -> None:
        """
        Позволяет редактировать сумму расхода, заданного по id.
        """

        self.expense_get_by_id(exp_id).amount = new_cost

    @orm.db_session
    def expense_edit_category_by_name(self, exp_id: int, new_category_name: str) -> None:
        """
        Позволяет редактировать категорию расхода.
        Проверяет, что категория с новым именем категории существует.
        """

        cats = self.categories_get_by_name(new_category_name)
        if not cats:
            raise NameError(f"No category named {new_category_name}")
        Expense[exp_id].category_id = cats[0].obj_id

    @orm.db_session
    def expense_edit_date(self, exp_id: int, new_date: datetime) -> None:
        """
        Позволяет редактировать дату расхода
        """

        Expense[exp_id].expense_date = new_date

    @orm.db_session
    def expense_edit_comment(self, exp_id: int, new_comment: str) -> None:
        """
        Позволяет редактировать комментарий расхода.
        """

        new_comment = new_comment if new_comment else "-"
        Expense[exp_id].comment = new_comment

    @orm.db_session
    def expense_delete(self, exp_id: int) -> None:
        """
        Удаляет расход, заданный по id.
        """

        self.expense_get_by_id(exp_id).delete()

    @orm.db_session
    def expenses_get_list(self) -> list[Expense]:
        """
        Получает список всех расходов.
        """
        return Expense.select()[:]
