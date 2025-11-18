# SE_Lab
This is our project in "Software Engineer " course . 

## Project Structure
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
├── requirements.txt            # 项目依赖
├── config.py                   # 配置文件
├── main.py                     # 应用启动文件
└── README.md                   # 项目说明文件
```