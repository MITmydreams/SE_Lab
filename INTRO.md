# Emoji Feedback System 项目设计文档

[toc]

---

## 1. 项目简介（Introduction）

随着数字化教学的不断发展，课堂中实时了解学生情绪反馈成为改进教学质量的重要手段。然而传统课堂缺乏有效的工具来记录学生的即时情绪和对课堂内容的感受。

本项目开发一套 **表情符号检查器（Emoji Feedback System）**，通过Emoji互动方式记录课堂反馈，并提供对课程反馈的可视化展示与数据统计。

系统共包含三类用户：

* **学生端**：发送 emoji 表情，查看自己发送emoji的历史记录
* **教师端**：查看课程的时间线与统计数据
* **管理员端**：管理用户、课程，查看 emoji 数据，导出统计图表

系统由 **Flask + MySQL + HTML/Bootstrap** 实现，具备良好的安全性、匿名性和扩展性。

---

## 2. 系统功能需求分析（Analysis）

### 2.1 用户角色与需求

为了满足不同用户的需求，我们设计了三类主要用户角色及其对应功能，经分析，主要需求如下表所示：

| 用户             | 权限与功能需求                                                    |
| ---------------- | ----------------------------------------------------------------- |
| **学生**   | 查看选课列表、发送 emoji、撤回 emoji、查看历史记录                |
| **教师**   | 查看授课课程、查看 emoji 时间线、查看统计结果                     |
| **管理员** | 用户管理、课程管理、选课管理、查看 emoji 历史、统计图表、导出数据 |

### 2.2 功能结构（Functional Structure）

综合以上分析，我们将主要用户功能结构设计和功能模块如下：

```
系统功能
│
├── 用户认证模块
│   ├── 注册
│   ├── 登录
│   └── 修改密码
│
├── 学生模块
│   ├── 查看选课
│   ├── 发送 Emoji
│   ├── 撤回 Emoji
│   └── 历史记录
│
├── 教师模块
│   ├── 查看授课
│   ├── Emoji时间线（可视化版本）
│   └── 课程emoji统计
│
├── 管理员模块
│   ├── 教师信息管理
│   ├── 学生信息管理
│   ├── 课程信息管理
│   ├── Emoji 历史查看
│   ├── 多种统计图分析：时间线 / 柱状图 / 饼图
│   └── 导出 CSV / PNG
│
└── 安全与数据模块
    ├── 匿名保护（交互信息隐藏学生身份）
    ├── 密码哈希（保证登录安全）
    └── 数据校验
```

---

## 3. 非功能需求（Non-functional Requirements）

### 3.1 性能要求

* 系统需支持课堂场景下至少 **100 名学生同时发送 emoji**
* 图表生成需保证 **1 秒内渲染完成**
* 管理员查询需可在 **秒级响应时间** 内返回数据

## 3.2 安全性要求

* 密码必须哈希存储（bcrypt）
* 严格 session 验证，不得越权访问
* 管理员或教师无权看到学生身份（匿名化）

## 3.3 可维护性

* 模块化后端（routes.py / routes_1.py）
* ORM 屏蔽 SQL 细节，便于后期维护
* 图表生成采用统一函数

---

## 4. 系统数据库设计（Database Design）

### 4.1 ER 图（概念模型）

对于该系统，我们抽象出了对应的实体及其关系和约束，具体结论为：

1. 用户（User）与课程（Course）之间为多对多关系，通过选课表（Student_Course）实现关联。
2. 用户（User）分为三种类型：管理员、教师、学生，通过 user_type 字段区分。
3. 每个课程（Course）由一名教师（User）负责授课，通过 Teacher_ID 字段关联。
4. 学生（User）可以在选修的课程（Course）中发送多个 Emoji，通过 Emoji 表记录。
5. Emoji 表与学生（User）和课程（Course）之间均为多对一关系。
6. 每个 Emoji 记录包含类型（type）和时间戳（time）字段。

对应的 ER 图如下所示：

![ER 图](./PIC/ER1.png)
![关系图](./PIC/ER2.png)

### 4.2 数据表设计

### User 表

| 字段      | 类型         | 描述                  |
| --------- | ------------ | --------------------- |
| User_ID   | char(20)     | 主键                  |
| key       | varchar(255) | 密码哈希              |
| name      | varchar(10)  | 姓名                  |
| mail      | varchar(50)  | 邮箱                  |
| tele_num  | varchar(11)  | 电话                  |
| user_type | int          | 1管理员 /2教师 /3学生 |

---

### Course 表

| 字段       | 类型        | 描述         |
| ---------- | ----------- | ------------ |
| Course_ID  | char(20)    | 主键         |
| Teacher_ID | char(20)    | 外键 → User |
| name       | varchar(20) | 课程名       |

---

### Student_Course 表（多对多）

| 字段       | 类型     |
| ---------- | -------- |
| Student_ID | char(20) |
| Course_ID  | char(20) |

---

### Emoji 表

| 字段       | 类型     |
| ---------- | -------- |
| Emoji_ID   | char(10) |
| Student_ID | char(20) |
| Course_ID  | char(20) |
| type       | int      |
| time       | datetime |

---

## 5. 系统架构设计（Architecture）

### 5.1 总体架构图

```
Android / Web 前端
         ↓
      Flask 后端
         ↓
       ORM 层
         ↓
      MySQL 数据库
```

### 5.2 后端模块结构

```
.
├── routes.py          # 管理员 + 通用功能
├── routes_1.py        # 学生 + 教师功能
├── models.py          # 数据模型（ORM）
├── templates/         # 前端页面
└── static/            # 静态资源
```

我们尽可能地将不同用户的逻辑分离，便于维护和扩展。

---

## 6. 核心后端涉及代码（Code Snippets）

### 6.1 学生发送 Emoji（核心业务）

```python
new_emoji = Emoji(
    id=str(uuid.uuid4())[:8],
    student_id=student_id,
    course_id=course_id,
    time=datetime.now(),
    type=emoji_type
)
```

基本实现：

* 使用 UUID 保证唯一性
* Emoji 与学生、课程关联
* 实现匿名但仍保持数据可查询性

---

### 6.2 教师查看时间线（Timeline）

```python
emojis = Emoji.query.filter(
    Emoji.course_id == course_id
).order_by(Emoji.time.asc()).all()
```

Timeline 页面展示课程中的课堂情绪走势。

---

## 6.3 管理员统计图（Bar/Pie/Timeline）

图表使用 matplotlib 动态生成：

```python
plt.savefig(buffer, format='png')
img_data = base64.b64encode(buffer.getvalue()).decode()
```

这允许：

* 不保存文件
* 可直接在 HTML 中显示
* 可导出为 PNG 文件

---

## 7. 系统部分核心功能流程图

### 7.1 学生发送 Emoji 流程

```
学生 → 选择 Emoji
     → POST /send_emoji
     → Flask 后端校验 session
     → 写入 Emoji 表
     → 返回课程列表
```

## 7.2 教师查看统计图流程

```
教师 → 选择课程
     → 请求 /timeline 或 /stats
     → 后端查询数据库
     → 生成图表
     → 返回图表页面
```

## 7.3 管理员导出 CSV

```
Admin 点击导出
         ↓
Backend 查询 Emoji
         ↓
生成 CSV 字符串
         ↓
浏览器下载
```

---

## 8. 部分核心页面设计

### 学生端

| 方法 | 路径                                | 描述       |
| ---- | ----------------------------------- | ---------- |
| GET  | `/student/courses`                | 查看选课   |
| POST | `/student/course/<id>/send_emoji` | 发送 Emoji |
| GET  | `/student/emoji/<id>/delete`      | 撤回       |
| GET  | `/student/emoji/history`          | 查看历史   |

---

### 教师端

| 方法 | 路径                              | 描述     |
| ---- | --------------------------------- | -------- |
| GET  | `/teacher/courses`              | 授课列表 |
| GET  | `/teacher/course/<id>/timeline` | 时间线   |
| GET  | `/teacher/course/<id>/stats`    | 统计图   |

---

### 管理员端

| 方法     | 路径                                     | 描述       |
| -------- | ---------------------------------------- | ---------- |
| GET      | `/admin/teacher`                       | 教师管理   |
| POST     | `/admin/add_teacher`                   | 增加教师   |
| GET      | `/admin/course`                        | 查询课程   |
| GET      | `/admin/course_emoji_history/<id>`     | Emoji 历史 |
| GET      | `/admin/export_emoji_history_csv/<id>` | 导出 CSV   |
| GET/POST | `/admin/course_emoji_bar/<id>`         | 柱状图     |
| GET      | `/admin/export_emoji_bar/<id>`         | 导出柱状图 |

---

## 9. 前端核心页面

* 登录 / 注册页面
  ![登录页面](./PIC/login.png)
* 随后会进入欢迎页面。
* 你可以选择查看自己的个人信息等。
  ![个人信息页面](./PIC/info.png)
  你可以修改个人信息，比如邮箱，电话号码等。（下图成功修改邮箱）
  ![修改个人信息页面](./PIC/info_modify.png)
* 如果你想要修改密码，可以点击修改密码页面
  ![修改密码页面](./PIC/change_pw.png)
* 修改成功后会返回个人信息页面。
  ![修改成功页面](./PIC/after_change.png)

**如果你是学生**，可以查看自己的课程列表，选择课程后可以发送 Emoji 表情。

* 学生课程列表
  ![学生课程列表页面](./PIC/stu_mycourse.png)
* 点进某课程后，你可以发送 Emoji 表情。
  ![发送 Emoji 页面](./PIC/stu_emoji_add.png)

> 此处我们为了便于后端实现，每个表情由一个数字代替，前端再根据数字显示对应的表情图片。

* 发送成功后会返回课程页面，你可以查看自己发送的 Emoji 历史记录。
  ![学生 Emoji 历史页面](./PIC/stu_emoji_history_all.png)
  你可以在这个界面考虑是否要删除某个 Emoji 记录。
  
如果你是老师：，你可以查看自己教授的课程列表，选择课程后可以查看该课程的 Emoji 时间线和统计图。
* 教师课程列表
  ![教师课程列表页面](./PIC/tea_check_course.png)
* 可以查看某课程的 emoji 历史记录（带有时间戳）
  ![教师查看课程 Emoji 历史页面](./PIC/tea_emoji_history.png)
* 可以初步查看某课程的 Emoji 数量统计，初步了解课堂情绪分布。
  ![教师 Emoji 统计页面1](./PIC/tea_emoji_1.png)
  ![教师 Emoji 统计页面](./PIC/tea_check_emoji.png)
* 也可以查看课程 Emoji 时间线页面，可以观察课堂情绪的变化趋势。
* ![教师 Emoji 时间线页面](./PIC/tea_check_timeline.png)
* 管理员可以管理教师、学生和课程信息。
  管理员教师信息管理页面
  ![管理员教师信息管理页面](./PIC/admin_check_ta.png)
  管理员学生信息管理页面
  ![管理员学生信息管理页面](./PIC/admin_check_stu1.png)
  管理员课程信息管理页面
  ![管理员课程信息管理页面](./PIC/admin_check_course.png)

可以在此基础上，对教师进行添加和修改等操作，也可以对学生的选课信息进行查询和编辑：

* 管理员对教师信息的添加页面
  ![管理员添加教师页面](./PIC/admin_add_ta.png)
  对教师做信息编辑
    ![管理员编辑教师页面](./PIC/admin_modify_ta.png)
* 管理员对学生选课信息的编辑页面
    ![管理员编辑学生选课页面](./PIC/admin_check_stu.png)
    ![管理员编辑学生选课页面](./PIC/admin_add_course.png)
* 管理员选课信息管理页面
  ![管理员选课信息管理页面](./PIC/admin_check_sc.png)
管理员可以查看某课程的 Emoji 历史记录：
* 管理员查看课程 Emoji 历史页面
* ![管理员查看课程 Emoji 历史页面](./PIC/admin_course_history.png)
* 管理员可以查看某课程的 Emoji 统计信息，我们设置了多种统计图表，方便管理员进行分析：
* 饼状图
  * ![管理员查看课程 Emoji 统计页面](./PIC/admin_course_1.png)
* 时间线图
  * ![管理员查看课程 Emoji 统计页面](./PIC/admin_course_2.png)
* 条形统计图
  * ![管理员查看课程 Emoji 统计页面](./PIC/admin_course_5.png)
  * ![管理员查看课程 Emoji 统计页面](./PIC/admin_course_3.png)
  * ![管理员查看课程 Emoji 统计页面](./PIC/admin_course_5-1.png)
* 圆盘统计图
  * ![管理员查看课程 Emoji 统计页面](./PIC/admin_course_6.png)
  * ![管理员查看课程 Emoji 统计页面](./PIC/admin_course_7.png)
* 管理员数据可视化页面
* 支持数据导出为 CSV 或 PNG 文件。
  ![导出数据页面](./PIC/export.png)

---

## 10. 部分 Debug 记录

## 11. 项目分工

| 成员   | 负责内容                                   |
| ------ | ------------------------------------------ |
| 范晓珂 | 数据库设计、前端页面实现、后端功能实现     |
| 张子悦 | 用户认证模块、后端功能实现、图表生成功能   |
| 王文煜 | 前端页面实现、图表生成功能                 |
| 王珏   | 需求和功能分析、后端部分功能实现、项目文档 |

---

## 12. 项目进度记录

| 日期  | 进度                   |
| ----- | ---------------------- |
| 9/20  | 需求分析完成           |
| 9/22  | 数据库设计完成         |
| 10/15 | 登录/注册/权限模块完成 |
| 10/30 | 学生端功能完成         |
| 11/10 | 教师端统计图完成       |
| 11/30 | 管理员管理模块完成     |
| 12/01 | 项目测试与文档编写     |
