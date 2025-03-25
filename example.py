from PySide6.QtWidgets import (QApplication, QMainWindow, QFormLayout, QHBoxLayout,
                               QVBoxLayout, QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QWidget, QDialog, QComboBox, QLabel)
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    number = Column(String)
    students = relationship("Student", back_populates="group_rel")
    students_in_group = relationship("StudentsInGroup", back_populates="group")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    surname = Column(String)
    name = Column(String)
    study_period = Column(String)
    group_rel = relationship("Group", back_populates="students")
    students_in_group = relationship("StudentsInGroup", back_populates="student")

class StudentsInGroup(Base):
    __tablename__ = "students_in_group"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    student = relationship("Student", back_populates="students_in_group")
    group = relationship("Group", back_populates="students_in_group")

def create_connection():
    engine = create_engine("postgresql://admin:root@localhost:5432/examen", echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(bind=engine)

class StudentDialog(QDialog):
    def __init__(self, parent=None, student=None):
        super().__init__(parent)
        self.setWindowTitle("Говно говна")
        
        layout = QFormLayout()
        
        self.group_combo = QComboBox()
        self.load_groups()
        self.name = QLineEdit()
        self.surname = QLineEdit()
        self.study_period = QLineEdit()
        
        if student:
            index = self.group_combo.findData(student.group_id)
            if index >= 0:
                self.group_combo.setCurrentIndex(index)
            self.name.setText(student.name)
            self.surname.setText(student.surname)
            self.study_period.setText(student.study_period)
            
        layout.addRow("Группа", self.group_combo)
        layout.addRow("Имя", self.name)
        layout.addRow("Фамилия", self.surname)
        layout.addRow("Период", self.study_period)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
    
    def load_groups(self):
        session = create_connection()
        groups = session.query(Group).all()
        for group in groups:
            self.group_combo.addItem(group.name, group.id)
        session.close()
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("АААААА")
        self.setGeometry(100, 100, 400, 300)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Панель фильтрации
        filter_layout = QHBoxLayout()
        self.search_surname = QLineEdit()
        self.search_surname.setPlaceholderText("Поиск по фамилии")
        self.group_filter = QComboBox()
        self.load_group_filter()
        filter_btn = QPushButton("Применить")
        filter_btn.clicked.connect(self.load_data)
        
        filter_layout.addWidget(QLabel("Фильтр:"))
        filter_layout.addWidget(self.search_surname)
        filter_layout.addWidget(QLabel("Группа:"))
        filter_layout.addWidget(self.group_filter)
        filter_layout.addWidget(filter_btn)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Фамилия", "Группа", "Период"])
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        add_btn.clicked.connect(self.add_student)
        edit_btn.clicked.connect(self.edit_student)
        delete_btn.clicked.connect(self.delete_student)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        
        self.load_data()
    
    def load_group_filter(self):
        session = create_connection()
        groups = session.query(Group).all()
        self.group_filter.addItem("Все группы", -1)
        for group in groups:
            self.group_filter.addItem(group.name, group.id)
        session.close()

    def load_data(self):
        session = create_connection()
        query = session.query(Student)
        
        # Фильтр по фамилии
        surname_search = self.search_surname.text().strip()
        if surname_search:
            query = query.filter(Student.surname.ilike(f"%{surname_search}%"))
        
        # Фильтр по группе
        group_id = self.group_filter.currentData()
        if group_id != -1:
            query = query.filter(Student.group_id == group_id)
        
        students = query.all()
        
        self.table.setRowCount(0)
        for row, student in enumerate(students):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(student.id)))
            self.table.setItem(row, 1, QTableWidgetItem(student.name))
            self.table.setItem(row, 2, QTableWidgetItem(student.surname))
            self.table.setItem(row, 3, QTableWidgetItem(student.group_rel.name if student.group_rel else "Нет группы"))
            self.table.setItem(row, 4, QTableWidgetItem(student.study_period))
        
        session.close()

    def add_student(self):
        dialog = StudentDialog(self)
        if dialog.exec():
            session = create_connection()
            group_id = dialog.group_combo.currentData()
            new_student = Student(
                group_id=group_id,
                surname=dialog.surname.text(),
                name=dialog.name.text(),
                study_period=dialog.study_period.text()
            )
            # Добавляем запись в StudentsInGroup
            students_in_group = StudentsInGroup(
                student=new_student,
                group_id=group_id
            )
            session.add(new_student)
            session.add(students_in_group)
            session.commit()
            session.close()
            self.load_data()

    def edit_student(self):
        selected = self.table.currentRow()
        if selected >= 0:
            student_id = int(self.table.item(selected, 0).text())
            session = create_connection()
            student = session.query(Student).get(student_id)
            dialog = StudentDialog(self, student)
            if dialog.exec():
                student.group_id = dialog.group_combo.currentData()
                student.name = dialog.name.text()
                student.surname = dialog.surname.text()
                student.study_period = dialog.study_period.text()
                # Обновляем запись в StudentsInGroup
                students_in_group = session.query(StudentsInGroup).filter_by(student_id=student_id).first()
                if students_in_group:
                    students_in_group.group_id = student.group_id
                else:
                    students_in_group = StudentsInGroup(student=student, group_id=student.group_id)
                    session.add(students_in_group)
                session.commit()
            session.close()
            self.load_data()

    def delete_student(self):
        selected = self.table.currentRow()
        if selected >= 0:
            student_id = int(self.table.item(selected, 0).text())
            session = create_connection()
            student = session.query(Student).get(student_id)
            # Удаляем связанные записи из StudentsInGroup
            session.query(StudentsInGroup).filter_by(student_id=student_id).delete()
            session.delete(student)
            session.commit()
            session.close()
            self.load_data()

# Запуск приложения
app = QApplication([])
window = MainWindow()
window.show()
app.exec()