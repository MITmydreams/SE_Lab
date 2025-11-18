# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, DateTimeField, PasswordField
from wtforms.validators import DataRequired, Length, Email, NumberRange, ValidationError
from datetime import datetime
import re

# 注册表单
class UserRegistrationForm(FlaskForm):
    user_id = StringField('用户ID', validators=[
        DataRequired(message='用户ID不能为空'),
        Length(min=1, max=20, message='用户ID长度必须在1-20个字符之间')
    ])
    
    key = StringField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=1, max=20, message='密码长度必须在1-20个字符之间')
    ])
    
    name = StringField('姓名', validators=[
        DataRequired(message='姓名不能为空'),
        Length(min=1, max=10, message='姓名长度必须在1-10个字符之间')
    ])
    
    mail = StringField('邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Email(message='请输入有效的邮箱地址'),
        Length(min=1, max=20, message='邮箱长度必须在1-20个字符之间')
    ])
    
    tele_num = StringField('电话号码', validators=[
        DataRequired(message='电话号码不能为空'),
        Length(min=11, max=11, message='电话号码必须是11位数字')
    ])
    
    user_type = SelectField('用户类型', choices=[
        (1, '管理员'),
        (2, '教师'),
        (3, '学生')
    ], validators=[
        DataRequired(message='请选择用户类型')
    ])
    
    def validate_tele_num(self, field):
        if not field.data.isdigit():
            raise ValidationError('电话号码必须全部由数字组成')
        if len(field.data) != 11:
            raise ValidationError('电话号码必须是11位数字')
    
    def validate_user_type(self, field):
        if field.data not in ['1', '2', '3']:
            raise ValidationError('用户类型必须是1(管理员)、2(教师)或3(学生)')

#登录表单
class UserLoginForm(FlaskForm):
    user_id = StringField('用户ID', validators=[
        DataRequired(message='用户ID不能为空')
    ])
    
    key = StringField('密码', validators=[
        DataRequired(message='密码不能为空')
    ])

# 课程表单
class CourseForm(FlaskForm):
    course_id = StringField('课程ID', validators=[
        DataRequired(message='课程ID不能为空'),
        Length(min=1, max=20, message='课程ID长度必须在1-20个字符之间')
    ])
    
    teacher_id = StringField('教师ID', validators=[
        DataRequired(message='教师ID不能为空'),
        Length(min=1, max=20, message='教师ID长度必须在1-20个字符之间')
    ])
    
    name = StringField('课程名称', validators=[
        DataRequired(message='课程名称不能为空'),
        Length(min=1, max=20, message='课程名称长度必须在1-20个字符之间')
    ])
# 学生选课表单
class StudentCourseForm(FlaskForm):
    student_id = StringField('学生ID', validators=[
        DataRequired(message='学生ID不能为空'),
        Length(min=1, max=20, message='学生ID长度必须在1-20个字符之间')
    ])
    
    course_id = StringField('课程ID', validators=[
        DataRequired(message='课程ID不能为空'),
        Length(min=1, max=20, message='课程ID长度必须在1-20个字符之间')
    ])
# emoji表单
class EmojiForm(FlaskForm):
    emoji_id = StringField('表情ID', validators=[
        DataRequired(message='表情ID不能为空'),
        Length(min=1, max=10, message='表情ID长度必须在1-10个字符之间')
    ])
    
    student_id = StringField('学生ID', validators=[
        DataRequired(message='学生ID不能为空'),
        Length(min=1, max=20, message='学生ID长度必须在1-20个字符之间')
    ])
    
    course_id = StringField('课程ID', validators=[
        DataRequired(message='课程ID不能为空'),
        Length(min=1, max=20, message='课程ID长度必须在1-20个字符之间')
    ])
    
    time = DateTimeField('时间', format='%Y-%m-%d %H:%M:%S', validators=[
        DataRequired(message='请选择时间')
    ])
    
    emoji_type = IntegerField('表情类型', validators=[
        DataRequired(message='表情类型不能为空'),
        NumberRange(min=1, message='表情类型必须为正整数')
    ])
    
    def validate_time(self, field):
        if field.data and field.data > datetime.now():
            raise ValidationError('表情发送时间不能晚于当前时间')