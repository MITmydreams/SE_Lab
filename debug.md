- 管理员界面中添加老师和学生时报错

  UserRegistrationForm()中的validate_on_submit()函数要求填充所有成分，而这两个页面的用户类型默认，并未让管理员选择，需在后端补充

  ```
  @app.route('/admin/add_teacher', methods=['GET', 'POST'])
  def add_teacher():
      form = UserRegistrationForm()
      form.user_type.data = 2  # 默认设置为教师类型
      if form.validate_on_submit():
          # 检查用户是否已存在
          existing_user = User.query.filter_by(id=form.user_id.data).first()
          if existing_user:
              flash('用户ID已存在，请选择其他ID', 'danger')
              return render_template('auth/register.html', form=form)
            
  ```

​		显示信息时出错，UserRegistrationForm()中没有id只有user_id

​		![image-20251205133111956](C:\Users\86137\AppData\Roaming\Typora\typora-user-images\image-20251205133111956.png)

与之类似，有

![image-20251205133249468](C:\Users\86137\AppData\Roaming\Typora\typora-user-images\image-20251205133249468.png)	

- 编辑老师/学生信息时报错

  类型错误，此处需要用UserProfileEditForm(obj=teacher)而不是UserRegistrationForm(obj=teacher)

  ![image-20251205133157389](C:\Users\86137\AppData\Roaming\Typora\typora-user-images\image-20251205133157389.png)

- 注册页面错误

  需用1，2，3来指代管理员，教师，学生

  ![image-20251205133343947](C:\Users\86137\AppData\Roaming\Typora\typora-user-images\image-20251205133343947.png)

- css模板显示错误

  文件需用绝对路径

  ![image-20251205133533471](C:\Users\86137\AppData\Roaming\Typora\typora-user-images\image-20251205133533471.png)

- 学生课程界面无法显示课程信息

  `routes_1.py` 中的 `student_courses` 函数返回 `Student_Course` 对象

  但模板期望的是 `Course` 对象来显示课程信息

  ```
  # 修改前
  courses = Student_Course.query.filter_by(student_id=student_id).all()
  
  # 修改后
  courses = Course.query.join(Student_Course)\
                        .filter(Student_Course.student_id == student_id)\
                        .all()
  ```