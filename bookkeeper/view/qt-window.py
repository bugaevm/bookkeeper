"""
Графическое окно
"""

import sys
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui

import os.path
sys.path.insert(0, os.path.dirname(sys.argv[0]) + '/..')

import presenter

SUGGESTED_ACTION_COLOR = "#CCCCCC"
DESTRUCTIVE_COLOR = "#AA0000"

class TitledTable(QtWidgets.QWidget):
    """
    Таблица, имеющая заголовок.
    Имеются методы для отображения и редактирования динамически меняющихся данных
    """

    def __init__(
            self,
            title : str,
            RequestContent,
            NotifyItemChanged,
            hheaders=None,
            vheaders=None
    ):
        super().__init__()

        self.title = title

        self.text_title = QtWidgets.QLabel(self.title)
        self.table = QtWidgets.QTableWidget(self)

        self.RequestContent = RequestContent
        self.NotifyItemChanged = NotifyItemChanged

        self.hheaders = hheaders
        self.vheaders = vheaders

        self.refresh()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text_title)
        self.layout.addWidget(self.table)

        self.table.itemChanged.connect(self.item_changed_cb)

    def refresh(self):
        """
        Перерисовывает таблицу.
        Нужен, если данные, показываемые таблицей, были обновлены.
        """

        content = self.RequestContent()
        self.table.setRowCount(len(content))
        if content:
            self.table.setColumnCount(len(content[0]))

        if self.hheaders:
            self.table.setHorizontalHeaderLabels(self.hheaders)
        if self.vheaders:
            self.table.setVerticalHeaderLabels(self.vheaders)

        for i, line in enumerate(content):
            for j, item_text in enumerate(line):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(item_text))

        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table.resizeColumnsToContents()

    def get_selected_rows(self):
        """
        Возвращает список индексов выделенных строк (строка считается выделенной, если в ней выделены все клетки).
        Используется, чтобы удалить данные из выделенных строк.
        """

        return sorted([selected.row() for selected in self.table.selectionModel().selectedRows()])

    def item_changed_cb(self, item):
        """
        Метод, уведомляющий о том, что некоторый элемент изменился (был отредактирован пользователем).
        """
        row = item.row()
        column = item.column()
        new_text = item.text()

        self.NotifyItemChanged(row, column, new_text)


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.presenter = presenter.Presenter()

        self.categories_ids_list = list()
        self.expenses_ids_list = list()
        self.budgets_ids_list = list()


        def change_exspense_item(row, column, new_text):
            changed_exp_id = self.expenses_ids_list[row]

            old_expense = self.presenter.ExpensesGetById(changed_exp_id)
            match column:
                case 0:
                    old_text = old_expense.expense_date.strftime("%d.%m.%y %H:%M:%S")
                case 1:
                    old_text = str(old_expense.amount)
                case 2:
                    try:
                        old_text = self.presenter.CategoryGetById(old_expense.category_id).name
                    except ValueError:
                        old_text = "Неизвестная категория"
                case 3:
                    old_text = old_expense.comment
                case _:
                    raise ValueError("Wrong column index")

            if old_text == new_text:
                return

            correct_data = True

            if column == 0:
                try:
                    new_date = datetime.strptime(new_text, "%d.%m.%y %H:%M:%S")
                except ValueError:
                    show_dialog(self, "Не удалось изменить данные", f"Некорректная дата: {new_text}")
                    correct_data = False
            elif column == 1:
                try:
                    new_cost = float(new_text)
                except ValueError:
                    show_dialog(self, "Не удалось изменить данные", f"Некорректная сумма: {new_text}")
                    correct_data = False

            if correct_data:
                match column:
                    case 0:
                        self.presenter.ExpenseEditDate(changed_exp_id, new_date)
                    case 1:
                        self.presenter.ExpenseEditCost(changed_exp_id, new_cost)
                    case 2:
                        try:
                            self.presenter.ExpenseEditCategoryByName(changed_exp_id, new_text)
                        except NameError:
                            show_dialog(self, "Не удалось изменить данные", f"Некорректная категория: {new_text}")
                    case 3:
                        self.presenter.ExpenseEditComment(changed_exp_id, new_text)
                    case _:
                        raise ValueError("Wrong column index")

            self.table_expenses.refresh()
            self.table_budget.refresh()

        self.table_expenses = TitledTable(
            "Последние расходы",
            self.get_expences_list,
            change_exspense_item,
            hheaders=("Дата", "Сумма", "Категория", "Комментарий")
        )


        # begin 'add expense' box
        self.cost_label = QtWidgets.QLabel("Сумма:")
        self.cost_entry = QtWidgets.QLineEdit()
        self.category_label = QtWidgets.QLabel("Категория:")
        self.category_combo_box = QtWidgets.QComboBox()
        self.category_combo_box.addItems([line[0] for line in self.get_categories_list(update_inds=False)])
        self.comment_label = QtWidgets.QLabel("Комментарий:")
        self.comment_entry = QtWidgets.QLineEdit()

        self.add_expense_button = QtWidgets.QPushButton("Добавить расход")
        self.add_expense_button.setStyleSheet(f"background-color: {SUGGESTED_ACTION_COLOR}")
        self.add_expense_button.clicked.connect(self.add_expense_cb)

        self.add_expense_box = QtWidgets.QHBoxLayout()
        self.add_expense_box.addWidget(self.cost_label)
        self.add_expense_box.addWidget(self.cost_entry)
        self.add_expense_box.addWidget(self.category_label)
        self.add_expense_box.addWidget(self.category_combo_box)
        self.add_expense_box.addWidget(self.comment_label)
        self.add_expense_box.addWidget(self.comment_entry)
        self.add_expense_box.addWidget(self.add_expense_button)
        # end 'add expense' box


        def delete_expenses():
            deleted = 0
            for index in self.table_expenses.get_selected_rows():
                exp_id = self.expenses_ids_list.pop(index - deleted)
                self.presenter.ExpenseDelete(exp_id)
                deleted += 1
            self.table_expenses.refresh()
            self.table_budget.refresh()

        self.delete_expenses_button = QtWidgets.QPushButton("Удалить выделенные расходы")
        self.delete_expenses_button.setStyleSheet(f"color: white; background-color: {DESTRUCTIVE_COLOR}")
        self.delete_expenses_button.clicked.connect(delete_expenses)


        def change_category_item(row, column, new_text):
            changed_cat_id = self.categories_ids_list[row]
            old_text = self.presenter.CategoryGetById(changed_cat_id).name
            if old_text == new_text:
                return

            correct_data = True
            if not new_text:
                show_dialog(self, "Не удалось изменить категорию", "Имя категории не должно быть пустым")
                correct_data = False

            if correct_data:
                try:
                    self.presenter.CategoryEditName(changed_cat_id, new_text)
                except NameError:
                    show_dialog(self, "Не удалось изменить категорию", f"Категория \"{new_text}\" уже существует")
                else:
                    self.category_combo_box.removeItem(row)
                    self.category_combo_box.insertItem(row, new_text)

            self.table_categories.refresh()
            self.table_expenses.refresh()

        self.table_categories = TitledTable(
            "Категории",
            self.get_categories_list,
            change_category_item,
            hheaders=["Название категории"]
        )

        # begin 'add category' box
        self.new_category_label = QtWidgets.QLabel("Новая категория:")
        self.new_category_entry = QtWidgets.QLineEdit()

        self.add_category_button = QtWidgets.QPushButton("Добавить категорию")
        self.add_category_button.setStyleSheet(f"background-color: {SUGGESTED_ACTION_COLOR}")
        self.add_category_button.clicked.connect(self.add_category_cb)

        self.add_category_box = QtWidgets.QHBoxLayout()
        self.add_category_box.addWidget(self.new_category_label)
        self.add_category_box.addWidget(self.new_category_entry)
        self.add_category_box.addWidget(self.add_category_button)
        # end 'add expense' box

        def delete_categories():
            deleted = 0
            for index in self.table_categories.get_selected_rows():
                cat_id = self.categories_ids_list.pop(index - deleted)
                self.presenter.CategoryDelete(cat_id)
                self.category_combo_box.removeItem(index - deleted)
                deleted += 1
            self.table_categories.refresh()
            self.table_expenses.refresh()

        self.delete_categories_button = QtWidgets.QPushButton("Удалить выделенные категории")
        self.delete_categories_button.setStyleSheet(f"color: white; background-color: {DESTRUCTIVE_COLOR}")
        self.delete_categories_button.clicked.connect(delete_categories)


        def change_budget_item(row, column, new_text):
            old_text = self.get_budget()[row][column]
            if old_text == new_text:
                return

            if column != 1:
                self.table_budget.refresh()
                return


            correct_data = True
            if not new_text:
                new_text = "0"
            try:
                limit = int(new_text)
            except ValueError:
                show_dialog(self, "Не удалось изменить бюджет", f"Некорректная сумма: {new_text}")
                correct_data = False

            if correct_data:
                self.presenter.BudgetEditLimit(self.budgets_ids_list[row], limit)
            self.table_budget.refresh()

        table_budget_hheaders = ("Сумма", "Бюджет", "Статус")
        table_budget_vheaders = ("День", "Неделя", "Месяц")
        self.table_budget = TitledTable(
            "Бюджет",
            self.get_budget,
            change_budget_item,
            hheaders=table_budget_hheaders,
            vheaders=table_budget_vheaders
        )

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.table_expenses)
        self.layout.addLayout(self.add_expense_box)
        self.layout.addWidget(self.delete_expenses_button, alignment=QtCore.Qt.AlignRight)
        self.layout.addWidget(self.table_categories)
        self.layout.addLayout(self.add_category_box)
        self.layout.addWidget(self.delete_categories_button, alignment=QtCore.Qt.AlignRight)
        self.layout.addWidget(self.table_budget)


    def add_expense_cb(self):
        cost = self.cost_entry.text()
        category = self.category_combo_box.currentText()
        comment = self.comment_entry.text()

        if not comment:
            comment = "Расход создан"

        if not cost:
            show_dialog(self, "Не удалось добавить расход", "Укажите сумму")
            return
        try:
            fcoast = float(cost)
        except ValueError:
            show_dialog(self, "Не удалось добавить расход", f"Некорректная сумма: {cost}")
            return

        if not category:
            show_dialog(self, "Не удалось добавить расход", "Укажите категорию")
            return

        try:
            self.presenter.ExpenseAdd(fcoast, category, comment)
        except NameError:
            show_dialog(self, "Не удалось добавить расход", f"Некорректная категория: {category}")

        self.table_expenses.refresh()
        self.table_budget.refresh()

        self.cost_entry.clear()
        self.comment_entry.clear()

    def add_category_cb(self):
        category_name = self.new_category_entry.text()
        if not category_name:
            show_dialog(self, "Не удалось добавить категорию", "Имя категории не должно быть пустым")
            return

        try:
            self.presenter.CategoryAdd(category_name)
        except NameError:
            show_dialog(self, "Не удалось добавить категорию", f"Категория \"{category_name}\" уже существует")
            return

        self.table_categories.refresh()
        self.category_combo_box.addItem(category_name)

        self.new_category_entry.clear()


    def get_expences_list(self):
        self.expenses_ids_list = list()
        res = list()

        for expense in self.presenter.ExpensesGetList():
            self.expenses_ids_list.append(expense.obj_id)

            try:
                cat_name = self.presenter.CategoryGetById(expense.category_id).name
            except ValueError:
                cat_name = "Неизвестная категория"

            res.append([
                expense.expense_date.strftime("%d.%m.%y %H:%M:%S"),
                str(expense.amount),
                cat_name,
                expense.comment
            ])

        return res

    def get_categories_list(self, update_inds=True):
        if update_inds:
            self.categories_ids_list = list()

        res = list()
        for category in self.presenter.CategoriesGetList():
            if update_inds:
                self.categories_ids_list.append(category.obj_id)
            res.append([category.name])
        return res

    def get_budget(self):
        bdg_day = self.presenter.BudgetGetSumForPeriod(0)
        bdg_week = self.presenter.BudgetGetSumForPeriod(1)
        bdg_month = self.presenter.BudgetGetSumForPeriod(2)

        day_bdg = self.presenter.BudgetGetByPeriod(0)
        week_bdg = self.presenter.BudgetGetByPeriod(1)
        month_bdg = self.presenter.BudgetGetByPeriod(2)

        day_limit = day_bdg.limit
        week_limit = week_bdg.limit
        month_limit = month_bdg.limit

        self.budgets_ids_list = [day_bdg.obj_id, week_bdg.obj_id, month_bdg.obj_id]

        warning = "Расходы превышают установленный бюджет"
        return [
            [str(bdg_day), str(day_limit), "" if bdg_day <= day_limit else warning],
            [str(bdg_week), str(week_limit), "" if bdg_week <= week_limit else warning],
            [str(bdg_month), str(month_limit), "" if bdg_month <= month_limit else warning]
        ]




def show_dialog(widget, title, message):
    dialog = QtWidgets.QMessageBox(widget)
    dialog.setModal(True)
    dialog.setWindowTitle(title)
    dialog.setText(message)

    for button in dialog.buttons():
        dialog.removeButton(button)
    dialog.addButton(QtWidgets.QMessageBox.Close)
    dialog.show()




if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = Window()
    widget.setWindowTitle("The Bookkeeper App")
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
