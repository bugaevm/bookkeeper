import sys
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui

SUGGESTED_ACTION_COLOR = "#CCCCCC"
DESTRUCTIVE_COLOR = "#AA0000"

class TitledTable(QtWidgets.QWidget):
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
        return sorted([selected.row() for selected in self.table.selectionModel().selectedRows()])

    def item_changed_cb(self, item):
        row = item.row()
        column = item.column()
        new_text = item.text()

        self.NotifyItemChanged(row, column, new_text)


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.categories_list = []
        self.expenses_list = list()

        def change_exspense_item(row, column, new_text):
            old_text = self.expenses_list[row][column]
            if old_text == new_text:
                return

            correct_data = True

            if column == 0:
                try:
                    datetime.strptime(new_text, "%d.%m.%y %H:%M:%S")
                except ValueError:
                    show_dialog(self, "Не удалось изменить данные", f"Некорректная дата: {new_text}")
                    correct_data = False
            elif column == 1:
                try:
                    float(new_text)
                except ValueError:
                    show_dialog(self, "Не удалось изменить данные", f"Некорректная сумма: {new_text}")
                    correct_data = False
            elif column == 2:
                if not [new_text] in self.categories_list:
                    show_dialog(self, "Не удалось изменить данные", f"Некорректная категория: {new_text}")
                    correct_data = False

            if correct_data:
                self.expenses_list[row][column] = new_text
            self.table_expenses.refresh()

        self.table_expenses = TitledTable(
            "Последние расходы",
            lambda : self.expenses_list,
            change_exspense_item,
            hheaders=("Дата", "Сумма", "Категория", "Комментарий")
        )

        # begin 'add expense' box
        self.cost_label = QtWidgets.QLabel("Сумма:")
        self.cost_entry = QtWidgets.QLineEdit()
        self.category_label = QtWidgets.QLabel("Категория:")
        self.category_combo_box = QtWidgets.QComboBox()
        self.category_combo_box.addItems([line[0] for line in self.categories_list])
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
                self.expenses_list.pop(index - deleted)
                deleted += 1
            self.table_expenses.refresh()

        self.delete_expenses_button = QtWidgets.QPushButton("Удалить выделенные расходы")
        self.delete_expenses_button.setStyleSheet(f"color: white; background-color: {DESTRUCTIVE_COLOR}")
        self.delete_expenses_button.clicked.connect(delete_expenses)


        def change_category_item(row, column, new_text):
            old_text = self.categories_list[row][0]
            if old_text == new_text:
                return

            correct_data = True
            if not new_text:
                show_dialog(self, "Не удалось изменить категорию", "Имя категории не должно быть пустым")
                correct_data = False
            if [new_text] in self.categories_list:
                show_dialog(self, "Не удалось изменить категорию", f"Категория \"{new_text}\" уже существует")
                correct_data = False

            if correct_data:
                self.categories_list[row][0] = new_text
                self.category_combo_box.removeItem(row)
                self.category_combo_box.insertItem(row, new_text)
            self.table_categories.refresh()
            self.table_expenses.refresh()

        self.table_categories = TitledTable(
            "Категории",
            lambda : self.categories_list,
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
                self.categories_list.pop(index - deleted)
                self.category_combo_box.removeItem(index - deleted)
                deleted += 1
            self.table_categories.refresh()
            self.table_expenses.refresh()

        self.delete_categories_button = QtWidgets.QPushButton("Удалить выделенные категории")
        self.delete_categories_button.setStyleSheet(f"color: white; background-color: {DESTRUCTIVE_COLOR}")
        self.delete_categories_button.clicked.connect(delete_categories)


        second_table_content = [
            ["705.43", "1000"],
            ["6719.43", "7000"],
            ["10592.96", "30000"]
        ]
        second_table_hheaders = ("Сумма", "Бюджет")
        second_table_vheaders = ("День", "Неделя", "Месяц")
        self.table_budget = TitledTable(
            "Бюджет",
            lambda : second_table_content,
            lambda : None,
            hheaders=second_table_hheaders,
            vheaders=second_table_vheaders
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
        date = datetime.now().strftime("%d.%m.%y %H:%M:%S")
        cost = self.cost_entry.text()
        category = self.category_combo_box.currentText()
        comment = self.comment_entry.text()

        if not cost:
            show_dialog(self, "Не удалось добавить расход", "Укажите сумму")
            return
        try:
            float(cost)
        except ValueError:
            show_dialog(self, "Не удалось добавить расход", f"Некорректная сумма: {cost}")
            return

        if not category:
            show_dialog(self, "Не удалось добавить расход", "Укажите категорию")
            return
        if not [category] in self.categories_list:
            show_dialog(self, "Не удалось добавить расход", f"Некорректная категория: {category}")
            return

        self.expenses_list.append([date, cost, category, comment])
        self.table_expenses.refresh()

        self.cost_entry.clear()
        self.comment_entry.clear()

    def add_category_cb(self):
        category_name = self.new_category_entry.text()
        if not category_name:
            show_dialog(self, "Не удалось добавить категорию", "Имя категории не должно быть пустым")
            return
        if [category_name] in self.categories_list:
            show_dialog(self, "Не удалось добавить категорию", f"Категория \"{category_name}\" уже существует")
            return

        self.categories_list.append([category_name])
        self.table_categories.refresh()
        self.category_combo_box.addItem(category_name)

        self.new_category_entry.clear()

    def get_expences_list(self):
        return self.expenses_list
    def get_categories_list(self):
        return self.categories_list


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

    # widget = MyWidget()
    widget = Window()
    widget.setWindowTitle("The Bookkeeper App")
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
