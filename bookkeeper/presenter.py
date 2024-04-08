# from db_connector import db

# from entities.budget import Budget
# from entities.category import Category
# from entities.expense import Expense

from pony import orm
from datetime import datetime, timedelta

db = orm.Database()
db.bind(provider='sqlite', filename=':memory:', create_db=True)


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
    # expenses = orm.Set('Expense')


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
    # category = orm.Required(Category)
    category_id = orm.Required(int)
    expense_date = orm.Required(datetime)
    comment = orm.Required(str)
    # pk: int = 0


db.generate_mapping(create_tables=True)


class Presenter:
    @orm.db_session
    def __init__(self):
        Budget(period=0, limit=0)
        Budget(period=1, limit=0)
        Budget(period=2, limit=0)


    def CategoriesGetByName(self, category_name):
        count = Category.select().count()
        if count:
            # return orm.select(cat for cat in Category if cat.name == category_name)[:]
            return [cat for cat in Category.select()[:] if cat.name == category_name]  # TODO
        return []

    @orm.db_session
    def CategoryAdd(self, category_name):
        if self.CategoriesGetByName(category_name):
            raise NameError(f"Category with name {category_name} already exists")

        Category(name=category_name)

    @orm.db_session
    def CategoryEditName(self, cat_id, new_name):
        if self.CategoriesGetByName(new_name):
            raise NameError(f"Category with name {new_name} already exists")
        Category[cat_id].name = new_name

    @orm.db_session
    def CategoryDelete(self, cat_id):
        Category[cat_id].delete()

    @orm.db_session
    def CategoriesGetList(self):
        return Category.select()[:]

    @orm.db_session
    def CategoryGetById(self, cat_id):
        try:
            return Category[cat_id]
        except orm.core.ObjectNotFound:
            raise ValueError("Category id is incorrect")


    @orm.db_session
    def BudgetsGetByPeriod(self, period):
        count = Budget.select().count()
        if count:
            return [bdg for bdg in Budget.select()[:] if bdg.period == period]  # TODO
        return []

    @orm.db_session
    def BudgetGetByPeriod(self, period):
        bdgs = self.BudgetsGetByPeriod(period)
        if not bdgs:
            raise ValueError("Wrong period")
        return bdgs[0]

    @orm.db_session
    def BudgetGetLimitForPeriod(self, period):
        return self.BudgetGetByPeriod().limit

    @orm.db_session
    def BudgetEditLimit(self, bdg_id, new_limit):
        Budget[bdg_id].limit = new_limit

    @orm.db_session
    def BudgetGetSumForPeriod(self, period):
        match period:
            case 0:
                delta = timedelta(days=1)
            case 1:
                delta = timedelta(days=7)
            case 2:
                delta = timedelta(days=30)
            case _:
                raise ValueError("Wrong period")

        dn = datetime.now()
        #return sum(orm.select(exp.amount for exp in Expense if dn - exp.expense_date <= delta))
        return sum([exp.amount for exp in Expense.select()[:] if dn - exp.expense_date <= delta])


    @orm.db_session
    def ExpenseAdd(self, cost, category_name, comment):
        cats = self.CategoriesGetByName(category_name)
        if not cats:
            print(f"No category named {category_name}")
            raise NameError(f"No category named {category_name}")
        Expense(amount=cost, category_id=cats[0].obj_id, expense_date=datetime.now(), comment=comment)

    @orm.db_session
    def ExpenseEditCost(self, exp_id, new_cost):
        Expense[exp_id].amount = new_cost

    @orm.db_session
    def ExpenseEditCategoryByName(self, exp_id, new_category_name):
        cats = self.CategoriesGetByName(new_category_name)
        if not cats:
            raise NameError(f"No category named {new_category_name}")
        Expense[exp_id].category_id = cats[0].obj_id

    @orm.db_session
    def ExpenseEditDate(self, exp_id, new_date):
        Expense[exp_id].expense_date = new_date

    @orm.db_session
    def ExpenseEditComment(self, exp_id, new_comment):
        Expense[exp_id].comment = new_comment

    @orm.db_session
    def ExpenseDelete(self, exp_id):
        Expense[exp_id].delete()

    @orm.db_session
    def ExpensesGetList(self):
        return Expense.select()[:]

    @orm.db_session
    def ExpensesGetById(self, exp_id):
        return Expense[exp_id]
