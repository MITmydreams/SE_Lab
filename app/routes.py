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
        
        if len(new_password) > 20:
            flash('新密码长度不能超过20个字符', 'danger')
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