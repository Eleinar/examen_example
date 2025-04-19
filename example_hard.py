from PySide6.QtWidgets import (QApplication, QMainWindow, QDialog, QFormLayout,
                               QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
                               QWidget, QPushButton, QTableWidget, QTableWidgetItem,
                               QDateEdit, QListWidget, QAbstractItemView, QMessageBox)
from sqlalchemy import Column, create_engine, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import date
from PySide6.QtCore import Qt

Base = declarative_base()

# Модели остаются без изменений
class Department(Base):
    __tablename__ = "department"
    id = Column(Integer, primary_key=True)
    department_name = Column(String)

class Duty(Base):
    __tablename__ = "duty"
    id = Column(Integer, primary_key=True)
    duty_name = Column(String)

class Skill(Base):
    __tablename__ = "skill"
    id = Column(Integer, primary_key=True)
    skill_name = Column(String)
    employee_rel = relationship("EmployeeSkill", back_populates="skill_rel")

class Employee(Base):
    __tablename__ = "employee"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    middle_name = Column(String)
    last_name = Column(String)
    id_duty = Column(Integer, ForeignKey('duty.id'))
    id_department = Column(Integer, ForeignKey('department.id'))
    date_in = Column(Date)
    dep_rel = relationship("Department")
    duty_rel = relationship("Duty")
    skill_rel = relationship("EmployeeSkill", back_populates="employee_rel")

class EmployeeSkill(Base):
    __tablename__ = "employee_skill"
    id = Column(Integer, primary_key=True)
    id_employee = Column(Integer, ForeignKey('employee.id'))
    id_skill = Column(Integer, ForeignKey('skill.id'))
    employee_rel = relationship("Employee", back_populates="skill_rel")
    skill_rel = relationship("Skill", back_populates="employee_rel")

def create_connection():
    try:
        engine = create_engine("postgresql://postgres@localhost:5432/postgres", echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session(bind=engine)
    except OperationalError as e:
        QMessageBox.critical(None, "Ошибка", f"Ошибка подключения к базе данных: {str(e)}")
        return None

class EmployeeDialog(QDialog):
    def __init__(self, parent=None, employee_id=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.setWindowTitle("Добавить/Редактировать сотрудника")
        
        layout = QFormLayout()
        
        self.first_name = QLineEdit()
        self.middle_name = QLineEdit()
        self.last_name = QLineEdit()
        self.department = QComboBox()
        self.duty = QComboBox()
        self.date_in = QDateEdit()
        self.date_in.setCalendarPopup(True)
        self.skills = QListWidget()
        self.skills.setSelectionMode(QAbstractItemView.MultiSelection)
        
        layout.addRow("Имя:", self.first_name)
        layout.addRow("Отчество:", self.middle_name)
        layout.addRow("Фамилия:", self.last_name)
        layout.addRow("Отдел:", self.department)
        layout.addRow("Должность:", self.duty)
        layout.addRow("Дата приема:", self.date_in)
        layout.addRow("Навыки:", self.skills)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_employee)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addRow(buttons)
        self.setLayout(layout)
        
        try:
            self.load_combo_data()
            if employee_id:
                self.load_employee_data()
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")
            self.reject()

    def load_combo_data(self):
        session = create_connection()
        if not session:
            raise SQLAlchemyError("Не удалось подключиться к базе данных")
        
        try:
            departments = session.query(Department).all()
            duties = session.query(Duty).all()
            skills = session.query(Skill).all()
            
            self.department.addItem("", 0)
            self.duty.addItem("", 0)
            for dept in departments:
                self.department.addItem(dept.department_name, dept.id)
            for duty in duties:
                self.duty.addItem(duty.duty_name, duty.id)
            for skill in skills:
                self.skills.addItem(skill.skill_name)
        finally:
            session.close()

    def load_employee_data(self):
        session = create_connection()
        if not session:
            raise SQLAlchemyError("Не удалось подключиться к базе данных")
        
        try:
            employee = session.query(Employee).filter(Employee.id == self.employee_id).first()
            if not employee:
                raise ValueError(f"Сотрудник с ID {self.employee_id} не найден")
            
            self.first_name.setText(employee.first_name)
            self.middle_name.setText(employee.middle_name)
            self.last_name.setText(employee.last_name)
            self.department.setCurrentIndex(self.department.findData(employee.id_department))
            self.duty.setCurrentIndex(self.duty.findData(employee.id_duty))
            self.date_in.setDate(employee.date_in)
            skills = session.query(EmployeeSkill).filter(EmployeeSkill.id_employee == self.employee_id).all()
            for skill in skills:
                items = self.skills.findItems(skill.skill_rel.skill_name, Qt.MatchExactly)
                for item in items:
                    item.setSelected(True)
        finally:
            session.close()

    def save_employee(self):
        # Валидация ввода
        if not self.first_name.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Имя' не может быть пустым")
            return
        if not self.last_name.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Фамилия' не может быть пустым")
            return
        if not self.department.currentData():
            QMessageBox.warning(self, "Ошибка", "Выберите отдел")
            return
        if not self.duty.currentData():
            QMessageBox.warning(self, "Ошибка", "Выберите должность")
            return

        session = create_connection()
        if not session:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных")
            return
        
        try:
            if self.employee_id:
                employee = session.query(Employee).filter(Employee.id == self.employee_id).first()
                if not employee:
                    raise ValueError(f"Сотрудник с ID {self.employee_id} не найден")
            else:
                employee = Employee()
            
            employee.first_name = self.first_name.text().strip()
            employee.middle_name = self.middle_name.text().strip()
            employee.last_name = self.last_name.text().strip()
            employee.id_department = self.department.currentData()
            employee.id_duty = self.duty.currentData()
            employee.date_in = self.date_in.date().toPython()
            
            if not self.employee_id:
                session.add(employee)
            
            session.commit()
            
            # Обновляем навыки
            session.query(EmployeeSkill).filter(EmployeeSkill.id_employee == employee.id).delete()
            selected_skills = [self.skills.item(i).text() for i in range(self.skills.count()) if self.skills.item(i).isSelected()]
            for skill_name in selected_skills:
                skill = session.query(Skill).filter(Skill.skill_name == skill_name).first()
                if skill:
                    employee_skill = EmployeeSkill(id_employee=employee.id, id_skill=skill.id)
                    session.add(employee_skill)
            
            session.commit()
            self.accept()
        except SQLAlchemyError as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения данных: {str(e)}")
        except ValueError as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            session.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 400)
        self.setWindowTitle("Учёт сотрудников")
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # Панель управления
        control_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить сотрудника")
        add_btn.clicked.connect(self.add_employee)
        edit_btn = QPushButton("Редактировать сотрудника")
        edit_btn.clicked.connect(self.edit_employee)
        delete_btn = QPushButton("Удалить сотрудника")
        delete_btn.clicked.connect(self.delete_employee)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по фамилии...")
        self.search_input.textChanged.connect(self.search_employees)
        self.filter_dept = QComboBox()
        self.filter_dept.currentIndexChanged.connect(self.filter_employees)
        
        control_layout.addWidget(add_btn)
        control_layout.addWidget(edit_btn)
        control_layout.addWidget(delete_btn)
        control_layout.addWidget(self.search_input)
        control_layout.addWidget(self.filter_dept)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Отчество", "Фамилия", "Отдел", "Должность", "Список навыков"])
        
        layout.addLayout(control_layout)
        layout.addWidget(self.table)
        
        try:
            self.load_filter_data()
            self.load_data()
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def load_filter_data(self):
        session = create_connection()
        if not session:
            raise SQLAlchemyError("Не удалось подключиться к базе данных")
        
        try:
            departments = session.query(Department).all()
            self.filter_dept.addItem("Все отделы", 0)
            for dept in departments:
                self.filter_dept.addItem(dept.department_name, dept.id)
        finally:
            session.close()

    def load_data(self, search_text="", dept_id=0):
        self.table.setRowCount(0)
        session = create_connection()
        if not session:
            raise SQLAlchemyError("Не удалось подключиться к базе данных")
        
        try:
            query = session.query(Employee)
            if search_text:
                query = query.filter(Employee.last_name.ilike(f"%{search_text}%"))
            if dept_id:
                query = query.filter(Employee.id_department == dept_id)
            
            employees = query.all()
            skill_query = session.query(EmployeeSkill)
            
            for row, employee in enumerate(employees):
                self.table.insertRow(row)
                skill_list = " ".join([skill.skill_rel.skill_name for skill in employee.skill_rel])
                
                self.table.setItem(row, 0, QTableWidgetItem(str(employee.id)))
                self.table.setItem(row, 1, QTableWidgetItem(employee.first_name))
                self.table.setItem(row, 2, QTableWidgetItem(employee.middle_name))
                self.table.setItem(row, 3, QTableWidgetItem(employee.last_name))
                self.table.setItem(row, 4, QTableWidgetItem(employee.dep_rel.department_name))
                self.table.setItem(row, 5, QTableWidgetItem(employee.duty_rel.duty_name))
                self.table.setItem(row, 6, QTableWidgetItem(skill_list))
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Ошибка загрузки данных: {str(e)}")
        finally:
            session.close()

    def add_employee(self):
        try:
            dialog = EmployeeDialog(self)
            if dialog.exec():
                self.load_data(self.search_input.text(), self.filter_dept.currentData())
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении сотрудника: {str(e)}")

    def edit_employee(self):
        try:
            selected = self.table.currentRow()
            if selected < 0:
                QMessageBox.warning(self, "Ошибка", "Выберите сотрудника для редактирования")
                return
            
            employee_id = int(self.table.item(selected, 0).text())
            dialog = EmployeeDialog(self, employee_id)
            if dialog.exec():
                self.load_data(self.search_input.text(), self.filter_dept.currentData())
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при редактировании сотрудника: {str(e)}")
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", "Некорректный ID сотрудника")

    def delete_employee(self):
        try:
            selected = self.table.currentRow()
            if selected < 0:
                QMessageBox.warning(self, "Ошибка", "Выберите сотрудника для удаления")
                return
            
            employee_id = int(self.table.item(selected, 0).text())
            session = create_connection()
            if not session:
                raise SQLAlchemyError("Не удалось подключиться к базе данных")
            
            try:
                session.query(EmployeeSkill).filter(EmployeeSkill.id_employee == employee_id).delete()
                session.query(Employee).filter(Employee.id == employee_id).delete()
                session.commit()
                self.load_data(self.search_input.text(), self.filter_dept.currentData())
            finally:
                session.close()
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении сотрудника: {str(e)}")
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", "Некорректный ID сотрудника")

    def search_employees(self, text):
        try:
            self.load_data(text, self.filter_dept.currentData())
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске сотрудников: {str(e)}")

    def filter_employees(self):
        try:
            self.load_data(self.search_input.text(), self.filter_dept.currentData())
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при фильтрации сотрудников: {str(e)}")


try:
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
except Exception as e:
    QMessageBox.critical(None, "Критическая ошибка", f"Приложение завершилось с ошибкой: {str(e)}")


     self.logo = QLabel(self)
        pixmap = QPixmap("logo.png")
        logo_pixmap = pixmap.scaled(80,200,Qt.KeepAspectRatio)
        self.logo.setPixmap(logo_pixmap)
        self.logo.setAlignment(Qt.AlignCenter)
