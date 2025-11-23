# app/routes.py
from flask import render_template, redirect, url_for, flash, request, session
from app import app, db
from app.forms import UserRegistrationForm, UserLoginForm, UserProfileEditForm, CourseForm, StudentCourseForm, EmojiForm
from app.models import User, Course, Student_Course, Emoji
from werkzeug.security import generate_password_hash, check_password_hash

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
    return render_template('welcome.html', user_name=session.get('user_name'))

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
    form = UserRegistrationForm(obj=teacher)
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
    if form.validate_on_submit():
        try:
            teacher = User(
                id=form.id.data,
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
    form = UserRegistrationForm(obj=student)

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
    all_courses = Course.query.all()
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
    if form.validate_on_submit():
        try:
            student = User(
                id=form.id.data,
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
    if form.validate_on_submit():
        try:
            course = Course(
                id=form.id.data,
                name=form.name.data,
                teacher_id=form.teacher_id.data
            )
            db.session.add(course)
            db.session.commit()
            flash('成功添加课程！')
            return redirect(url_for('courses'))
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

#TODO: 课程统计信息
# course info
@app.route('/admin/course_info/<string:course_id>', methods=['GET'])
def course_info(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('admin/course_info.html', course=course)