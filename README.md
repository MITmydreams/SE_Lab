# SE_Lab
This is our project in "Software Engineer " course . 

## 使用说明
1. 克隆代码库到本地：
   ```bash
   git clone git@github.com:MITmydreams/SE_Lab.git
   cd SE_Lab
   ```
2. 创建并激活虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. 安装依赖：
   ```bash
    pip install Flask SQLAlchemy Flask-Migrate WTForms
    ```
4. 配置数据库连接（在`config.py`中修改数据库信息）
    ```python
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/database'
    # 将 user,password,database 替换为你的数据库用户名，密码，数据库名
    ```
5. 初始化数据库：
   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```
6. 运行代码：
   ```python
    python main.py
    ```
## 目录结构
```
SE_Lab/
├── app/
│   ├── init.py                 # Flask应用初始化
│   ├── models.py               # 数据模型定义
│   ├── routes.py               # 路由和视图函数
│   ├── forms.py                # 表单验证
│   └── templates/              # 前端模板
│       ├── base.html           # 基础布局模板
│       ├── auth/               # 认证相关页面
│       │   ├── login.html      # 登录页面
│       │   └── register.html   # 注册页面
│       ├── admin/              # 管理员功能页面
│       ├── teacher/            # 教师功能页面
│       ├── student/            # 学生功能页面
│       └── common/             # 通用页面
│           ├── change_password.html # 修改密码
│           ├── edit_profile.html # 修改个人信息
│           └── profile.html    # 个人信息
├── config.py                   # 配置文件
├── main.py                     # 应用启动文件
└── README.md                   # 项目说明文件
```