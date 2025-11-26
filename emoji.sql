/*==============================================================*/
/* DBMS name:      MySQL 5.0                                    */
/* Created on:     2025/9/27 13:40:26                           */
/*==============================================================*/

-- 1. 创建数据库（不存在则创建）
drop database if exists emoji;
CREATE DATABASE IF NOT EXISTS emoji;
USE emoji;

-- 2. 删除表（若存在）：直接删除整个表，无需单独删主键
drop table if exists Student_Course; -- 依赖Course和User，先删
drop table if exists Emoji;          -- 依赖Course和User，先删
drop table if exists Course;         -- 依赖User，后删
drop table if exists `User`;           -- 无依赖，最后删

/*==============================================================*/
/* Table: User                                                  */
/*==============================================================*/
create table `User`
(
   User_ID              char(20) not null,
   `key`                char(20), -- 关键字key加反引号转义，避免语法冲突
   name                 char(10),
   mail                 char(20),
   tele_num             integer(11),
   user_type            integer(2)
);

alter table `User`
   add primary key (User_ID);

/*==============================================================*/
/* Table: Course                                                */
/*==============================================================*/
create table Course
(
   Course_ID            char(20) not null,
   Teacher_ID           char(20),
   name                 char(20)
);

alter table Course
   add primary key (Course_ID);

-- 3. 添加外键约束（Course依赖User）
alter table Course add constraint FK_Reference_1 foreign key (Teacher_ID)
      references User (User_ID) on delete restrict on update restrict;

/*==============================================================*/
/* Table: Emoji                                                 */
/*==============================================================*/
create table Emoji
(
   Emoji_ID             char(10) not null,
   Student_ID           char(20) not null,
   Course_ID            char(20) not null,
   time                 datetime,
   type                 int(2)
);

alter table Emoji
   add primary key (Emoji_ID, Student_ID, Course_ID);

-- 4. 添加外键约束（Emoji依赖User和Course）
alter table Emoji add constraint FK_Reference_4 foreign key (Course_ID)
      references Course (Course_ID) on delete restrict on update restrict;

alter table Emoji add constraint FK_Reference_5 foreign key (Student_ID)
      references User (User_ID) on delete restrict on update restrict;

/*==============================================================*/
/* Table: Student_Course                                        */
/*==============================================================*/
create table Student_Course
(
   Student_ID           char(20) not null,
   Course_ID            char(20) not null
);

alter table Student_Course
   add primary key (Student_ID, Course_ID);

-- 5. 添加外键约束（Student_Course依赖User和Course）
alter table Student_Course add constraint FK_Reference_2 foreign key (Student_ID)
      references User (User_ID) on delete restrict on update restrict;

alter table Student_Course add constraint FK_Reference_3 foreign key (Course_ID)
      references Course (Course_ID) on delete restrict on update restrict;