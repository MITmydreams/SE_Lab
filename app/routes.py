# app/routes.py
from flask import render_template, redirect, url_for, flash, request, session, make_response
from app import app, db
from app.forms import UserRegistrationForm, UserLoginForm, UserProfileEditForm, CourseForm, StudentCourseForm, EmojiForm
from app.models import User, Course, Student_Course, Emoji
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64
import csv

# 首页(登录前)
@app.route('/')
def home():
    return render_template('home.html')

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegistrationForm()
    
    if form.validate_on_submit():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(id=form.user_id.data).first()
        if existing_user:
            flash('用户ID已存在，请选择其他ID', 'danger')
            return render_template('auth/register.html', form=form)
        
        # 检查邮箱是否已被使用
        existing_email = User.query.filter_by(mail=form.mail.data).first()
        if existing_email:
            flash('该邮箱已被注册，请使用其他邮箱', 'danger')
            return render_template('auth/register.html', form=form)
        
        # 检查电话号码是否已被使用
        existing_tele_num = User.query.filter_by(tele_num=form.tele_num.data).first()
        if existing_tele_num:
            flash('该电话号码已被注册，请使用其他号码', 'danger')
            return render_template('auth/register.html', form=form)
        
        try:
            # 创建新用户
            new_user = User(
                id=form.user_id.data,
                key=generate_password_hash(form.key.data),
                name=form.name.data,
                mail=form.mail.data,
                tele_num=form.tele_num.data,
                user_type=form.user_type.data
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败：{str(e)}', 'danger')
    
    return render_template('auth/register.html', form=form)

# 欢迎(登录后首页)
@app.route('/welcome')
def welcome():
    if 'user_id' not in session:
        flash('请先登录', 'danger')
        return redirect(url_for('login'))
    
    # 获取当前用户信息
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if user.is_admin:
        return redirect(url_for('welcome_admin'))
    elif user.is_teacher:
        return redirect(url_for('welcome_teacher'))
    elif user.is_student:
        return redirect(url_for('welcome_student'))
    else:
        flash('用户类型异常', 'danger')
        return redirect(url_for('login'))


@app.route('/welcome_admin')
def welcome_admin():
    return render_template('welcome_admin.html', user_name=session.get('user_name'))

@app.route('/welcome_teacher')
def welcome_teacher():
    return render_template('welcome_teacher.html', user_name=session.get('user_name'))

@app.route('/welcome_student')
def welcome_student():
    return render_template('welcome_student.html', user_name=session.get('user_name'))


# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user_id.data).first()
        
        if user and check_password_hash(user.key, form.key.data):
            # 登录成功，设置session
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_type'] = user.user_type
            
            flash(f'欢迎回来，{user.name}！', 'success')
            return redirect(url_for('welcome'))
        else:
            flash('用户ID或密码错误，请重试', 'danger')
    
    return render_template('auth/login.html', form=form)

# 个人信息查看页面
@app.route('/common/profile')
def profile():
    """显示用户个人信息（只读模式）"""
    # 检查登录状态
    if 'user_id' not in session:
        flash('请先登录', 'danger')
        return redirect(url_for('login'))
    
    # 获取当前用户信息
    user = User.query.get_or_404(session['user_id'])
    
    # 用户类型映射
    role_names = {1: '管理员', 2: '教师', 3: '学生'}
    role_name = role_names.get(user.user_type, '未知')
    
    return render_template('common/profile.html', 
                         user=user, 
                         role_name=role_name,
                         edit_mode=False)  # 查看模式

# 个人信息编辑页面
@app.route('/common/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # 检查登录状态
    if 'user_id' not in session:
        flash('请先登录', 'danger')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])
    
    form = UserProfileEditForm(obj=user)
    
    if form.validate_on_submit():
        try:
            # 检查邮箱是否被其他用户使用
            existing_email = User.query.filter(
                User.mail == form.mail.data,
                User.id != user.id  # 使用数据库查询到的用户ID，确保一致性
            ).first()
            if existing_email:
                flash('该邮箱已被其他用户使用', 'danger')
                return render_template('common/edit_profile.html', 
                                     form=form, 
                                     user=user)
            
            # 检查电话号码是否被其他用户使用
            existing_tele_num = User.query.filter(
                User.tele_num == form.tele_num.data,
                User.id != user.id  # 使用数据库查询到的用户ID
            ).first()
            if existing_tele_num:
                flash('该电话号码已被其他用户使用', 'danger')
                return render_template('common/edit_profile.html', 
                                     form=form, 
                                     user=user)
            
            # 更新用户信息（只更新允许修改的字段，绝对不修改ID和用户类型）
            user.name = form.name.data
            user.mail = form.mail.data
            user.tele_num = form.tele_num.data

            db.session.commit()
            
            # 更新session中的用户名
            session['user_name'] = user.name
            
            flash('个人信息更新成功！', 'success')
            # 重定向到查看页面，避免重复提交
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
    
    # 用户类型映射
    role_names = {1: '管理员', 2: '教师', 3: '学生'}
    role_name = role_names.get(user.user_type, '未知')
    
    return render_template('common/edit_profile.html', 
                         form=form, 
                         user=user, 
                         role_name=role_name)

# 修改密码
@app.route('/common/change_password', methods=['GET', 'POST'])
def change_password():
    # 检查登录状态
    if 'user_id' not in session:
        flash('请先登录', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(session['user_id'])
    
    if request.method == 'POST':
        # 获取表单数据
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证当前密码
        if not check_password_hash(user.key, current_password):
            flash('当前密码错误', 'danger')
            return render_template('common/change_password.html')
        
        # 验证新密码格式
        if not new_password or len(new_password) < 1:
            flash('新密码不能为空', 'danger')
            return render_template('common/change_password.html')
        
        if len(new_password) > 255:
            flash('新密码长度不能超过255个字符', 'danger')
            return render_template('common/change_password.html')
        
        # 验证新密码和确认密码是否一致
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return render_template('common/change_password.html')
        
        # 验证新密码不能与旧密码相同
        if check_password_hash(user.key, new_password):
            flash('新密码不能与当前密码相同', 'danger')
            return render_template('common/change_password.html')
        
        # 更新密码
        try:
            user.key = generate_password_hash(new_password)
            db.session.commit()
            flash('密码修改成功！', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'密码修改失败：{str(e)}', 'danger')
    
    # GET请求显示修改密码表单
    return render_template('common/change_password.html')

# 管理员查询教师
@app.route('/admin/teacher', methods=['GET'])
def teacher():
    # 获取搜索参数
    search_query = request.args.get('search', '').strip()
    
    # 基础查询
    query = User.query.filter_by(user_type=2)
    
    # 如果有搜索条件
    if search_query:
        query = query.filter(
            db.or_(
                User.id.ilike(f'%{search_query}%'),
                User.name.ilike(f'%{search_query}%')
            )
        )

    teachers = query.all()
    form = UserRegistrationForm()
    return render_template('admin/teacher.html', teachers=teachers, form=form)

# Edit Teacher
@app.route('/admin/edit_teacher/<string:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    form = UserProfileEditForm(obj=teacher)
    if form.validate_on_submit():
        try:
            teacher.name = form.name.data
            teacher.mail = form.mail.data
            teacher.tele_num = form.tele_num.data
            db.session.commit()
            flash('成功更新教师！')
        except Exception as e:
            db.session.rollback()
            flash(f'更新教师失败: {e}', 'danger')
        return redirect(url_for('edit_teacher', teacher_id=teacher.id))
    return render_template('admin/edit_teacher.html', form=form, teacher=teacher)

# Add Teacher
@app.route('/admin/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    form = UserRegistrationForm()
    form.user_type.data = 2  # 默认设置为教师类型
    if form.validate_on_submit():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(id=form.user_id.data).first()
        if existing_user:
            flash('用户ID已存在，请选择其他ID', 'danger')
            return render_template('admin/add_teacher.html', form=form)
        
        # 检查邮箱是否已被使用
        existing_email = User.query.filter_by(mail=form.mail.data).first()
        if existing_email:
            flash('该邮箱已被注册，请使用其他邮箱', 'danger')
            return render_template('admin/add_teacher.html', form=form)
        
        # 检查电话号码是否已被使用
        existing_tele_num = User.query.filter_by(tele_num=form.tele_num.data).first()
        if existing_tele_num:
            flash('该电话号码已被注册，请使用其他号码', 'danger')
            return render_template('admin/add_teacher.html', form=form)
        try:
            teacher = User(
                id=form.user_id.data,
                name=form.name.data,
                mail=form.mail.data,
                tele_num=form.tele_num.data,
                key=generate_password_hash(form.key.data),  # 使用哈希存储密码
                user_type=2  # 教师类型
            )
            db.session.add(teacher)
            db.session.commit()
            flash('成功添加教师！')
            return redirect(url_for('teacher'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加教师失败: {e}', 'danger')
    return render_template('admin/add_teacher.html', form=form)

# Delete Teacher
@app.route('/admin/delete_teacher/<string:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    try:
        teacher = User.query.get_or_404(teacher_id)
        # 添加用户类型验证，确保只有教师类型(2)才能被删除
        if teacher.user_type != 2:
            flash('只能删除教师类型的用户！', 'danger')
            return redirect(url_for('teacher'))
        
        db.session.delete(teacher)
        db.session.commit()
        flash('成功删除教师！')
    except Exception as e:
        db.session.rollback()
        flash(f'删除教师失败: {e}', 'danger')
    return redirect(url_for('teacher'))

# 管理员查询学生
@app.route('/admin/student', methods=['GET'])
def student():
    # 获取搜索参数
    search_query = request.args.get('search', '').strip()
    
    # 基础查询
    query = User.query.filter_by(user_type=3)
    
    # 如果有搜索条件
    if search_query:
        query = query.filter(
            db.or_(
                User.id.ilike(f'%{search_query}%'),
                User.name.ilike(f'%{search_query}%')
            )
        )

    students = query.all()
    form = UserRegistrationForm()
    return render_template('admin/student.html', students=students, form=form)

# Edit Student
@app.route('/admin/edit_student/<string:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = User.query.get_or_404(student_id)
    form = UserProfileEditForm(obj=student)
    # 获取已选的课程
    enrolled_courses = db.session.query(Course).join(Student_Course).filter(
        Student_Course.student_id == student_id
    ).all()
    # 搜索参数
    search_query = request.args.get('search', '').strip()
    if search_query:
        enrolled_courses = db.session.query(Course).join(Student_Course).filter(
            Student_Course.student_id == student_id,
            db.or_(
                Course.id.ilike(f'%{search_query}%'),
                Course.name.ilike(f'%{search_query}%')
            )
        ).all()
    if form.validate_on_submit():
        try:
            student.name = form.name.data
            student.mail = form.mail.data
            student.tele_num = form.tele_num.data
            db.session.commit()
            flash('成功更新学生！')
        except Exception as e:
            db.session.rollback()
            flash(f'更新学生失败: {e}', 'danger')
        return redirect(url_for('edit_student', student_id=student.id))
    return render_template('admin/edit_student.html', form=form, student=student, enrolled_courses=enrolled_courses, search_query=search_query)

# delete course from student
@app.route('/admin/delete_course_from_student/<string:course_id>/<string:student_id>', methods=['POST'])
def delete_course_from_student(course_id, student_id):
    try:
        student_course = Student_Course.query.filter_by(
            course_id=course_id, 
            student_id=student_id
        ).first_or_404()  
        db.session.delete(student_course)
        db.session.commit()
        flash('成功删除学生选课！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除学生选课失败: {e}', 'danger')
    return redirect(url_for('edit_student', student_id=student_id))

# add course to student
@app.route('/admin/add_course_to_student/<string:student_id>', methods=['GET', 'POST'])
def add_course_to_student(student_id):
    student = User.query.get_or_404(student_id)

    # 搜索参数
    search_query = request.args.get('search', '').strip()
    
    # 获取所有课程
    all_courses = Course.query
    # 已选课的课程ID
    enrolled_course_ids = [sc.course_id for sc in 
                          Student_Course.query.filter_by(student_id=student_id).all()]
    
    # 未选课的课程
    available_courses = all_courses.filter(Course.id.notin_(enrolled_course_ids))

    # 如果有搜索条件
    if search_query:
        available_courses = available_courses.filter(
            db.or_(
                Course.id.ilike(f'%{search_query}%'),
                Course.name.ilike(f'%{search_query}%')
            )
        )

    available_courses = available_courses.all()

    # 处理添加学生选课
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        if course_id:
            try:
                # 检查是否已经选课
                existing_enrollment = Student_Course.query.filter_by(
                    course_id=course_id, 
                    student_id=student_id
                ).first()
                
                if existing_enrollment:
                    flash('该学生已经选过此课程！', 'warning')
                else:
                    # 创建新的选课记录
                    new_enrollment = Student_Course(
                        course_id=course_id,
                        student_id=student_id
                    )
                    db.session.add(new_enrollment)
                    db.session.commit()
                    flash('成功添加学生选课！', 'success')
                    
                    # 重定向回添加页面，可以继续添加
                    return redirect(url_for('add_course_to_student', student_id=student_id))

            except Exception as e:
                db.session.rollback()
                flash(f'添加学生选课失败: {e}', 'danger')

    return render_template('admin/add_course_to_student.html',
                         student=student,
                         available_courses=available_courses,
                         search_query=search_query)

# Add Student
@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    form = UserRegistrationForm()
    form.user_type.data = 3  # 默认设置为学生类型
    if form.validate_on_submit():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(id=form.user_id.data).first()
        if existing_user:
            flash('用户ID已存在，请选择其他ID', 'danger')
            return render_template('admin/add_student.html', form=form)
        
        # 检查邮箱是否已被使用
        existing_email = User.query.filter_by(mail=form.mail.data).first()
        if existing_email:
            flash('该邮箱已被注册，请使用其他邮箱', 'danger')
            return render_template('admin/add_student.html', form=form)
        
        # 检查电话号码是否已被使用
        existing_tele_num = User.query.filter_by(tele_num=form.tele_num.data).first()
        if existing_tele_num:
            flash('该电话号码已被注册，请使用其他号码', 'danger')
            return render_template('admin/add_student.html', form=form)
        
        try:
            student = User(
                id=form.user_id.data,
                name=form.name.data,
                mail=form.mail.data,
                tele_num=form.tele_num.data,
                key=generate_password_hash(form.key.data),  # 使用哈希存储密码
                user_type=3  # 学生类型
            )
            db.session.add(student)
            db.session.commit()
            flash('成功添加学生！')
            return redirect(url_for('student'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加学生失败: {e}', 'danger')
    return render_template('admin/add_student.html', form=form)

# Delete Student
@app.route('/admin/delete_student/<string:student_id>', methods=['POST'])
def delete_student(student_id):
    try:
        student = User.query.get_or_404(student_id)
        # 添加用户类型验证，确保只有学生类型(3)才能被删除
        if student.user_type != 3:
            flash('只能删除学生类型的用户！', 'danger')
            return redirect(url_for('student'))
        db.session.delete(student)
        db.session.commit()
        flash('成功删除学生！')
    except Exception as e:
        db.session.rollback()
        flash(f'删除学生失败: {e}', 'danger')
    return redirect(url_for('student'))

# 管理员查询课程
@app.route('/admin/course', methods=['GET'])
def course():
    # 获取搜索参数
    search_query = request.args.get('search', '').strip()
    
    # 基础查询
    query = Course.query
    
    # 如果有搜索条件
    if search_query:
        query = query.filter(
            db.or_(
                Course.id.ilike(f'%{search_query}%'),
                Course.name.ilike(f'%{search_query}%')
            )
        )
    
    courses = query.all()
    form = CourseForm()
    return render_template('admin/course.html', courses=courses, form=form)

# Edit Course
@app.route('/admin/edit_course/<string:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    # 获取所有教师数据
    teachers = User.query.filter_by(user_type=2).all()  # user_type=2 代表教师
    # 构建下拉列表选项：[(教师ID, 教师姓名(教师ID)), ...]
    teacher_choices = [(teacher.id, f"{teacher.name} ({teacher.id})") for teacher in teachers]
    form.teacher_id.choices = teacher_choices
    
    # 获取已选课的学生
    enrolled_students = db.session.query(User).join(Student_Course).filter(
        Student_Course.course_id == course_id
    ).all()
    
    # 搜索参数
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        enrolled_students = db.session.query(User).join(Student_Course).filter(
            Student_Course.course_id == course_id,
            db.or_(
                User.id.ilike(f'%{search_query}%'),
                User.name.ilike(f'%{search_query}%')
            )
        ).all()
    
    if form.validate_on_submit():
        try:
            course.name = form.name.data
            course.teacher_id = form.teacher_id.data
            db.session.commit()
            flash('成功更新课程！', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'更新课程失败: {e}', 'danger')
        return redirect(url_for('edit_course', course_id=course.id))
    
    return render_template('admin/edit_course.html', 
                         form=form, 
                         course=course,
                         enrolled_students=enrolled_students,
                         search_query=search_query)

# delete student from course
@app.route('/admin/delete_student_from_course/<string:course_id>/<string:student_id>', methods=['POST'])
def delete_student_from_course(course_id, student_id):
    try:
        student_course = Student_Course.query.filter_by(
            course_id=course_id, 
            student_id=student_id
        ).first_or_404()  
        db.session.delete(student_course)
        db.session.commit()
        flash('成功删除学生选课！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除学生选课失败: {e}', 'danger')
    return redirect(url_for('edit_course', course_id=course_id))

# add student to course
@app.route('/admin/add_student_to_course/<string:course_id>', methods=['GET', 'POST'])
def add_student_to_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # 搜索参数
    search_query = request.args.get('search', '').strip()
    
    # 获取所有学生
    all_students = User.query.filter_by(user_type=3)
    
    # 已选课的学生ID
    enrolled_student_ids = [sc.student_id for sc in 
                          Student_Course.query.filter_by(course_id=course_id).all()]
    
    # 未选课的学生
    available_students = all_students.filter(User.id.notin_(enrolled_student_ids))
    
    # 如果有搜索条件
    if search_query:
        available_students = available_students.filter(
            db.or_(
                User.id.ilike(f'%{search_query}%'),
                User.name.ilike(f'%{search_query}%')
            )
        )
    
    available_students = available_students.all()
    
    # 处理添加学生选课
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        if student_id:
            try:
                # 检查是否已经选课
                existing_enrollment = Student_Course.query.filter_by(
                    course_id=course_id, 
                    student_id=student_id
                ).first()
                
                if existing_enrollment:
                    flash('该学生已经选过此课程！', 'warning')
                else:
                    # 创建新的选课记录
                    new_enrollment = Student_Course(
                        course_id=course_id,
                        student_id=student_id
                    )
                    db.session.add(new_enrollment)
                    db.session.commit()
                    flash('成功添加学生选课！', 'success')
                    
                    # 重定向回添加页面，可以继续添加
                    return redirect(url_for('add_student_to_course', course_id=course_id))
                    
            except Exception as e:
                db.session.rollback()
                flash(f'添加学生选课失败: {e}', 'danger')
    
    return render_template('admin/add_student_to_course.html',
                         course=course,
                         available_students=available_students,
                         search_query=search_query)

# Add Course
@app.route('/admin/add_course', methods=['GET', 'POST'])
def add_course():
    form = CourseForm()

    # 获取所有教师数据
    teachers = User.query.filter_by(user_type=2).all()  # user_type=2 代表教师
    # 构建下拉列表选项：[(教师ID, 教师姓名(教师ID)), ...]
    teacher_choices = [(teacher.id, f"{teacher.name} ({teacher.id})") for teacher in teachers]
    form.teacher_id.choices = teacher_choices

    if form.validate_on_submit():
        try:
            # 再次验证教师是否存在（双重保险）
            teacher = User.query.filter_by(id=form.teacher_id.data).first()
            if not teacher:
                flash('教师ID不存在，请检查后重新输入', 'danger')
                return render_template('admin/add_course.html', form=form)
            if teacher.user_type != 2:  # 2代表教师类型
                flash('该用户不是教师，请选择有效的教师ID', 'danger')
                return render_template('admin/add_course.html', form=form)
            
            # 检查课程ID是否已存在
            existing_course = Course.query.filter_by(id=form.course_id.data).first()
            if existing_course:
                flash('课程ID已存在，请使用不同的课程ID', 'danger')
                return render_template('admin/add_course.html', form=form)
            
            course = Course(
                id=form.course_id.data,
                name=form.name.data,
                teacher_id=form.teacher_id.data
            )
            db.session.add(course)
            db.session.commit()
            flash('成功添加课程！')
            return redirect(url_for('course'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加课程失败: {e}', 'danger')
    return render_template('admin/add_course.html', form=form)

# Delete Course
@app.route('/admin/delete_course/<string:course_id>', methods=['POST'])
def delete_course(course_id):
    try:
        course = Course.query.get_or_404(course_id)
        db.session.delete(course)
        db.session.commit()
        flash('成功删除课程！')
    except Exception as e:
        db.session.rollback()
        flash(f'删除课程失败: {e}', 'danger')
    return redirect(url_for('course'))

# 管理员查看课程emoji历史(不包含学生信息)
@app.route('/admin/course_emoji_history/<string:course_id>', methods=['GET'])
def course_emoji_history(course_id):
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    # 获取课程信息
    course = Course.query.get_or_404(course_id)
    
    # 获取emoji历史数据（只包含emoji基本信息，不包含学生信息）
    emoji_history = Emoji.query.filter_by(course_id=course_id)\
                              .with_entities(
                                  Emoji.id,
                                  Emoji.course_id,
                                  Emoji.type,
                                  Emoji.time
                              )\
                              .order_by(Emoji.time.desc())\
                              .all()
    
    return render_template('admin/course_emoji_history.html',
                         course=course,
                         emoji_history=emoji_history)

# 导出课程emoji历史为CSV（不包含学生信息）
@app.route('/admin/export_emoji_history_csv/<string:course_id>')
def export_emoji_history_csv(course_id):
    """
    导出课程emoji历史为CSV文件（不包含学生信息）
    """
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    # 获取课程信息
    course = Course.query.get_or_404(course_id)
    
    # 获取emoji历史数据（与查看函数相同的查询逻辑）
    emoji_history = Emoji.query.filter_by(course_id=course_id)\
                              .with_entities(
                                  Emoji.id,
                                  Emoji.course_id,
                                  Emoji.type,
                                  Emoji.time
                              )\
                              .order_by(Emoji.time.desc())\
                              .all()
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入CSV头部
    writer.writerow(['Emoji ID', '课程ID', '表情类型', '发送时间'])
    
    # 写入数据行
    for emoji in emoji_history:
        writer.writerow([
            emoji.id,
            emoji.course_id,
            f'表情 {emoji.type}',
            emoji.time.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # 准备响应
    filename = f"emoji历史_{course.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@app.route('/admin/course_info/<string:course_id>')
def course_info(course_id):
    # 从数据库加载课程
    course = Course.query.get_or_404(course_id)
    # 传给前端
    return render_template('admin/course_info.html', course=course)


# 管理员查看课程详细信息: 24小时emoji情绪变化曲线图
@app.route('/admin/course_emoji_timeline/<string:course_id>', methods=['GET'])
def course_emoji_timeline(course_id):
    """
    管理员查看课程详细信息: 24小时emoji情绪变化图表
    """
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    # 获取课程信息
    course = Course.query.get_or_404(course_id)
    
    # 获取教师信息
    teacher = User.query.get(course.teacher_id)
    
    # 获取选课学生数量
    student_count = Student_Course.query.filter_by(course_id=course_id).count()
    
    # 获取总emoji数量
    total_emojis = Emoji.query.filter_by(course_id=course_id).count()
    
    # 生成24小时情绪变化图表
    chart_image = generate_emoji_timeline_chart(course_id)
    
    # 获取emoji类型统计
    emoji_stats = db.session.query(
        Emoji.type,
        db.func.count(Emoji.type).label('count')
    ).filter_by(course_id=course_id).group_by(Emoji.type).all()

    return render_template('admin/course_emoji_timeline.html', 
                         course=course,
                         teacher=teacher,
                         student_count=student_count,
                         total_emojis=total_emojis,
                         chart_image=chart_image,
                         emoji_stats=emoji_stats)

def generate_emoji_timeline_chart(course_id, export=False):
    """
    生成课程24小时emoji情绪变化曲线图
    """
    # 获取当前时间及24小时前的时间
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    # 查询24小时内该课程的emoji数据
    emojis = Emoji.query.filter(
        Emoji.course_id == course_id,
        Emoji.time >= start_time,
        Emoji.time <= end_time
    ).order_by(Emoji.time.asc()).all()
    
    if not emojis:
        return None  # 没有数据时返回None
    
    # 按小时和表情类型分组统计
    hour_emoji_data = {}
    emoji_types = set()
    
    for emoji in emojis:
        # 获取小时信息
        hour = emoji.time.replace(minute=0, second=0, microsecond=0)
        emoji_type = emoji.type
        
        emoji_types.add(emoji_type)
        
        if hour not in hour_emoji_data:
            hour_emoji_data[hour] = {}
        
        if emoji_type not in hour_emoji_data[hour]:
            hour_emoji_data[hour][emoji_type] = 0
        
        hour_emoji_data[hour][emoji_type] += 1
    
    # 生成完整的时间序列（填充缺失的小时）
    all_hours = [start_time + timedelta(hours=i) for i in range(25)]
    complete_data = {}
    
    for emoji_type in emoji_types:
        complete_data[emoji_type] = []
        for hour in all_hours:
            if hour in hour_emoji_data and emoji_type in hour_emoji_data[hour]:
                complete_data[emoji_type].append(hour_emoji_data[hour][emoji_type])
            else:
                complete_data[emoji_type].append(0)
    
    # 生成图表
    plt.figure(figsize=(12, 6))
    
    # 为每种表情类型绘制曲线
    for emoji_type, counts in complete_data.items():
        hours_labels = [f"{h.hour:02d}:00" for h in all_hours]
        plt.plot(hours_labels, counts, marker='o', label=f'表情 {emoji_type}', linewidth=2)
    
    plt.title(f'课程 {course_id} - 24小时情绪变化趋势', fontsize=14, fontweight='bold')
    plt.xlabel('时间 (小时)', fontsize=12)
    plt.ylabel('表情发送数量', fontsize=12)
    plt.legend(title='表情类型', loc='best')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 将图表转换为base64编码的图片或返回文件流
    img_buffer = io.BytesIO()
    if export:
        # 导出时使用更高分辨率
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        return img_buffer  # 返回文件流
    else:
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        return f"data:image/png;base64,{img_data}"

# 管理员查看课程详细信息: 自定义时间范围表情数量统计
@app.route('/admin/course_emoji_bar/<string:course_id>', methods=['GET', 'POST'])
def course_emoji_bar(course_id):
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    # 获取课程信息
    course = Course.query.get_or_404(course_id)
    
    # 默认时间范围（最近7天）
    default_end = datetime.now()
    default_start = default_end - timedelta(days=7)
    
    # 初始化变量
    chart_image = None
    emoji_stats = []
    start_time = default_start
    end_time = default_end
    total_emojis = 0
    
    # 处理表单提交
    if request.method == 'POST':
        try:
            # 获取表单中的时间参数
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            if start_date_str and end_date_str:
                start_time = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_time = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # 验证时间范围
                if start_time > end_time:
                    flash('开始时间不能晚于结束时间', 'danger')
                    return redirect(url_for('course_emoji_bar', course_id=course_id))
                
                if start_time > datetime.now():
                    flash('开始时间不能晚于当前时间', 'danger')
                    return redirect(url_for('course_emoji_bar', course_id=course_id))

                # 生成柱状图
                chart_image = generate_emoji_bar_chart(course_id, start_time, end_time)
                
                # 获取统计详情
                emoji_stats = db.session.query(
                    Emoji.type,
                    db.func.count(Emoji.type).label('count')
                ).filter(
                    Emoji.course_id == course_id,
                    Emoji.time >= start_time,
                    Emoji.time <= end_time
                ).group_by(Emoji.type).order_by(db.func.count(Emoji.type).desc()).all()
                
                # 计算总数
                total_emojis = sum(stat.count for stat in emoji_stats)
                
                flash(f'成功生成 {start_time.strftime("%Y-%m-%d")} 至 {end_time.strftime("%Y-%m-%d")} 的统计图表', 'success')
                
        except ValueError:
            flash('日期格式错误，请使用 YYYY-MM-DD 格式', 'danger')
        except Exception as e:
            flash(f'生成图表时出错: {str(e)}', 'danger')

    return render_template('admin/course_emoji_bar.html', 
                         course=course,
                         chart_image=chart_image,
                         emoji_stats=emoji_stats,
                         total_emojis=total_emojis,
                         start_time=start_time,
                         end_time=end_time,
                         default_start=default_start.strftime('%Y-%m-%d'),
                         default_end=default_end.strftime('%Y-%m-%d'))

def generate_emoji_bar_chart(course_id, start_time, end_time, export=False):
    """
    生成课程表情数量统计柱状图
    """
    # 查询指定时间范围内的emoji数据
    emoji_stats = db.session.query(
        Emoji.type,
        db.func.count(Emoji.type).label('count')
    ).filter(
        Emoji.course_id == course_id,
        Emoji.time >= start_time,
        Emoji.time <= end_time
    ).group_by(Emoji.type).order_by(Emoji.type).all()
    
    if not emoji_stats:
        return None  # 没有数据时返回None
    
    # 准备图表数据
    emoji_types = [f'表情 {stat.type}' for stat in emoji_stats]
    counts = [stat.count for stat in emoji_stats]
    
    # 生成柱状图
    plt.figure(figsize=(10, 6))
    
    # 创建柱状图，使用不同颜色
    bars = plt.bar(emoji_types, counts, color=plt.cm.Set3(range(len(emoji_types))))
    
    # 在柱子上显示数值
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom', fontsize=10)
    
    # 设置图表样式
    plt.title(f'课程 {course_id} - 表情数量统计\n({start_time.strftime("%Y-%m-%d")} 至 {end_time.strftime("%Y-%m-%d")})', 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('表情类型', fontsize=12)
    plt.ylabel('发送数量', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    # 将图表转换为base64编码的图片或返回文件流
    img_buffer = io.BytesIO()
    if export:
        # 导出时使用更高分辨率
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        return img_buffer  # 返回文件流
    else:
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        return f"data:image/png;base64,{img_data}"

# 管理员查看课程表情分布饼图（自定义时间范围）
@app.route('/admin/course_emoji_pie/<string:course_id>', methods=['GET', 'POST'])
def course_emoji_pie(course_id):
    """
    管理员查看课程表情分布饼图：根据自定义时间范围生成饼图
    """
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    # 获取课程信息
    course = Course.query.get_or_404(course_id)
    
    # 默认时间范围（最近7天）
    default_end = datetime.now()
    default_start = default_end - timedelta(days=7)
    
    # 初始化变量
    chart_image = None
    emoji_stats = []
    start_time = default_start
    end_time = default_end
    total_emojis = 0
    
    # 处理表单提交
    if request.method == 'POST':
        try:
            # 获取表单中的时间参数
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            if start_date_str and end_date_str:
                start_time = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_time = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # 验证时间范围
                if start_time > end_time:
                    flash('开始时间不能晚于结束时间', 'danger')
                    return redirect(url_for('course_emoji_pie', course_id=course_id))
                
                if start_time > datetime.now():
                    flash('开始时间不能晚于当前时间', 'danger')
                    return redirect(url_for('course_emoji_pie', course_id=course_id))

                # 生成饼图
                chart_image = generate_emoji_pie_chart(course_id, start_time, end_time)
                
                # 获取统计详情
                emoji_stats = db.session.query(
                    Emoji.type,
                    db.func.count(Emoji.type).label('count')
                ).filter(
                    Emoji.course_id == course_id,
                    Emoji.time >= start_time,
                    Emoji.time <= end_time
                ).group_by(Emoji.type).order_by(db.func.count(Emoji.type).desc()).all()
                
                # 计算总数
                total_emojis = sum(stat.count for stat in emoji_stats)
                
                flash(f'成功生成 {start_time.strftime("%Y-%m-%d")} 至 {end_time.strftime("%Y-%m-%d")} 的分布饼图', 'success')
                
        except ValueError:
            flash('日期格式错误，请使用 YYYY-MM-DD 格式', 'danger')
        except Exception as e:
            flash(f'生成饼图时出错: {str(e)}', 'danger')
    
    return render_template('admin/course_emoji_pie.html', 
                         course=course,
                         chart_image=chart_image,
                         emoji_stats=emoji_stats,
                         total_emojis=total_emojis,
                         start_time=start_time,
                         end_time=end_time,
                         default_start=default_start.strftime('%Y-%m-%d'),
                         default_end=default_end.strftime('%Y-%m-%d'))

def generate_emoji_pie_chart(course_id, start_time, end_time, export=False):
    """
    生成课程表情分布饼图
    """
    # 查询指定时间范围内的emoji数据
    emoji_stats = db.session.query(
        Emoji.type,
        db.func.count(Emoji.type).label('count')
    ).filter(
        Emoji.course_id == course_id,
        Emoji.time >= start_time,
        Emoji.time <= end_time
    ).group_by(Emoji.type).order_by(db.func.count(Emoji.type).desc()).all()
    
    if not emoji_stats:
        return None  # 没有数据时返回None
    
    # 准备图表数据
    emoji_types = [f'表情 {stat.type}' for stat in emoji_stats]
    counts = [stat.count for stat in emoji_stats]
    total_count = sum(counts)
    
    # 计算百分比
    percentages = [count / total_count * 100 for count in counts]
    
    # 生成饼图
    plt.figure(figsize=(14, 8))
    
    # 设置颜色
    colors = plt.cm.Set3(range(len(emoji_types)))
    
    # 创建饼图
    wedges, texts, autotexts = plt.pie(
        counts, 
        labels=None,  # 不显示内置标签，使用图例和引出线
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        shadow=True,
        explode=[0.05] * len(emoji_types),  # 稍微分离每个扇形
        textprops={'fontsize': 10}
    )
    
    # 设置百分比文本样式
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
    
    # 添加引出线和标签
    plt.gca().axis('equal')  # 确保饼图是圆形
    
    # 创建自定义标签（包含表情名称和数量）
    legend_labels = [f'{emoji_type}\n({count}个, {percent:.1f}%)' 
                    for emoji_type, count, percent in zip(emoji_types, counts, percentages)]
    
    # 添加图例（放在右侧）
    plt.legend(wedges, legend_labels,
              title="表情类型",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=10,
              frameon=True,
              fancybox=True,
              shadow=True)
    
    # 设置标题
    plt.title(f'课程 {course_id} - 表情分布饼图\n({start_time.strftime("%Y-%m-%d")} 至 {end_time.strftime("%Y-%m-%d")})', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # 将图表转换为base64编码的图片或返回文件流
    img_buffer = io.BytesIO()
    if export:
        # 导出时使用更高分辨率
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        return img_buffer  # 返回文件流
    else:
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        return f"data:image/png;base64,{img_data}"
    
# 导出图表功能
# 导出24小时情绪变化图表
@app.route('/admin/export_emoji_timeline/<string:course_id>')
def export_emoji_timeline(course_id):
    """导出24小时情绪变化图表为PNG文件"""
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    course = Course.query.get_or_404(course_id)
    img_buffer = generate_emoji_timeline_chart(course_id, export=True)
    
    filename = f"情绪变化趋势_{course_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    response = make_response(img_buffer.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    plt.close()  # 确保清理matplotlib资源
    return response

# 导出柱状图
@app.route('/admin/export_emoji_bar/<string:course_id>')
def export_emoji_bar(course_id):
    """导出表情数量统计柱状图为PNG文件"""
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    course = Course.query.get_or_404(course_id)
    
    # 获取时间参数
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        flash('请提供时间范围参数', 'danger')
        return redirect(url_for('course_emoji_bar', course_id=course_id))
    
    try:
        start_time = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_time = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        img_buffer = generate_emoji_bar_chart(course_id, start_time, end_time, export=True)
        
        filename = f"表情数量统计_{course_id}_{start_time.strftime('%Y%m%d')}_至_{end_time.strftime('%Y%m%d')}.png"
        
        response = make_response(img_buffer.getvalue())
        response.headers['Content-Type'] = 'image/png'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        plt.close()  # 确保清理matplotlib资源
        return response
        
    except Exception as e:
        flash(f'导出图表时出错: {str(e)}', 'danger')
        return redirect(url_for('course_emoji_bar', course_id=course_id))

# 导出饼图
@app.route('/admin/export_emoji_pie/<string:course_id>')
def export_emoji_pie(course_id):
    """导出表情分布饼图为PNG文件"""
    if session.get('user_type') != 1:
        flash('无权限访问管理员功能', 'danger')
        return redirect(url_for('welcome'))
    
    course = Course.query.get_or_404(course_id)
    
    # 获取时间参数
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        flash('请提供时间范围参数', 'danger')
        return redirect(url_for('course_emoji_pie', course_id=course_id))
    
    try:
        start_time = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_time = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        img_buffer = generate_emoji_pie_chart(course_id, start_time, end_time, export=True)
        
        filename = f"表情分布饼图_{course_id}_{start_time.strftime('%Y%m%d')}_至_{end_time.strftime('%Y%m%d')}.png"
        
        response = make_response(img_buffer.getvalue())
        response.headers['Content-Type'] = 'image/png'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        plt.close()  # 确保清理matplotlib资源
        return response
        
    except Exception as e:
        flash(f'导出图表时出错: {str(e)}', 'danger')
        return redirect(url_for('course_emoji_pie', course_id=course_id))