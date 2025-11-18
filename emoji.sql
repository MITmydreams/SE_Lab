/*==============================================================*/
/* DBMS name:      MySQL 5.0                                    */
/* Created on:     2025/9/27 13:40:26                           */
/*==============================================================*/


alter table Course
   drop primary key;

drop table if exists Course;

alter table Emoji
   drop primary key;

drop table if exists Emoji;

alter table Student_Course
   drop primary key;

drop table if exists Student_Course;

alter table User
   drop primary key;

drop table if exists User;

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

/*==============================================================*/
/* Table: User                                                  */
/*==============================================================*/
create table User
(
   User_ID              char(20) not null,
   key                  char(20),
   name                 char(10),
   mail                 char(20),
   tele_num             integer(11),
   user_type            integer(2)
);

alter table User
   add primary key (User_ID);

alter table Course add constraint FK_Reference_1 foreign key (Teacher_ID)
      references User (User_ID) on delete restrict on update restrict;

alter table Emoji add constraint FK_Reference_4 foreign key (Course_ID)
      references Course (Course_ID) on delete restrict on update restrict;

alter table Emoji add constraint FK_Reference_5 foreign key (Student_ID)
      references User (User_ID) on delete restrict on update restrict;

alter table Student_Course add constraint FK_Reference_2 foreign key (Student_ID)
      references User (User_ID) on delete restrict on update restrict;

alter table Student_Course add constraint FK_Reference_3 foreign key (Course_ID)
      references Course (Course_ID) on delete restrict on update restrict;

