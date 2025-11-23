# app/models.py
from app import db
from sqlalchemy.orm import validates
from sqlalchemy import CheckConstraint
from datetime import datetime

class User(db.Model):
    id = db.Column('User_ID', db.String(20), primary_key=True)
    key = db.Column('key', db.String(255))  # 增加字段长度存储完整哈希值
    name = db.Column('name', db.String(10))
    mail = db.Column('mail', db.String(50))
    tele_num = db.Column('tele_num', db.String(11))
    user_type = db.Column('user_type', db.Integer)
    teacher_courses = db.relationship('Course', back_populates='teacher', cascade='all, delete-orphan')
    student_courses = db.relationship('Student_Course', back_populates='student', cascade='all, delete-orphan')
    sent_emojis = db.relationship('Emoji', back_populates='student', cascade='all, delete-orphan')
    # user_type: 1 - admin, 2 - teacher, 3 - student
    __table_args__ = (
        CheckConstraint('user_type IN (1, 2, 3)', name='check_user_type'),
    )
    
    # 验证数据完整性
    @validates('tele_num')
    def validate_tele_num(self, key, tele_num):
        if tele_num is not None:
            if len(tele_num) != 11:
                raise ValueError("电话号码必须是11位数字")
        return tele_num
    @validates('user_type')
    def validate_user_type(self, key, user_type):
        if user_type not in (1, 2, 3):
            raise ValueError("用户类型必须是 1, 2, or 3")
        return user_type

    # 检查用户角色
    @property
    def is_admin(self):
        return self.user_type == 1
    @property
    def is_teacher(self):
        return self.user_type == 2
    @property
    def is_student(self):
        return self.user_type == 3

class Course(db.Model):
    id = db.Column('Course_ID', db.String(20), primary_key=True)
    teacher_id = db.Column('Teacher_ID', db.String(20), db.ForeignKey('user.User_ID'))
    name = db.Column('name', db.String(20))

    teacher = db.relationship('User', back_populates='teacher_courses')
    student_courses = db.relationship('Student_Course', back_populates='course', cascade='all, delete-orphan')
    emojis = db.relationship('Emoji', back_populates='course', cascade='all, delete-orphan')

class Student_Course(db.Model):
    student_id = db.Column('Student_ID', db.String(20), db.ForeignKey('user.User_ID'), primary_key=True)
    course_id = db.Column('Course_ID', db.String(20), db.ForeignKey('course.Course_ID'), primary_key=True)
    
    student = db.relationship('User', back_populates='student_courses')
    course = db.relationship('Course', back_populates='student_courses')

class Emoji(db.Model):
    id = db.Column('Emoji_ID', db.String(10), primary_key=True)
    student_id = db.Column('Student_ID', db.String(20), db.ForeignKey('user.User_ID'))
    course_id = db.Column('Course_ID', db.String(20), db.ForeignKey('course.Course_ID'))
    time = db.Column('time', db.DateTime)
    type = db.Column('type', db.Integer)
    
    # 关系定义
    student = db.relationship('User', back_populates='sent_emojis')
    course = db.relationship('Course', back_populates='emojis')
    
    __table_args__ = (
        CheckConstraint('type >= 1', name='check_emoji_type_positive'),
    )
    
    @validates('type')
    def validate_type(self, key, type_val):
        if type_val < 1:
            raise ValueError("Emoji类型必须是正整数")
        return type_val
    
    @validates('time')
    def validate_time(self, key, time_val):
        if time_val and time_val > datetime.now():
            raise ValueError("Emoji时间不能是未来的时间")
        return time_val