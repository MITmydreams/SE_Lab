"""Initial migration.

Revision ID: ea804c9d9721
Revises: 
Create Date: 2025-11-26 11:55:49.512160

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ea804c9d9721'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### 核心逻辑：解除所有依赖 → 修改主表 → 重建依赖 ###
    # 第一步：解除所有依赖 User.User_ID 的外键（关键！）
    # 1.1 解除 Course 表的外键（FK_Reference_1：依赖 User.User_ID）
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('FK_Reference_1'), type_='foreignkey')

    # 1.2 解除 Emoji 表的外键（FK_Reference_5：依赖 User.User_ID）
    with op.batch_alter_table('emoji', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('FK_Reference_5'), type_='foreignkey')
        # 顺带解除 Emoji 对 Course 的外键（避免后续修改 Course 时冲突）
        batch_op.drop_constraint(batch_op.f('FK_Reference_4'), type_='foreignkey')

    # 1.3 解除 Student_Course 表的外键（FK_Reference_2：依赖 User.User_ID）
    with op.batch_alter_table('student_course', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('FK_Reference_2'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('FK_Reference_3'), type_='foreignkey')

    # 第二步：安全修改 User 表（此时无任何外键依赖）
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('User_ID',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=20),
               existing_nullable=False)
        batch_op.alter_column('key',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=255),
               existing_nullable=True)
        batch_op.alter_column('name',
               existing_type=mysql.CHAR(length=10),
               type_=sa.String(length=10),
               existing_nullable=True)
        batch_op.alter_column('mail',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=True)
        batch_op.alter_column('tele_num',
               existing_type=mysql.INTEGER(),
               type_=sa.String(length=11),
               existing_nullable=True)

    # 第三步：修改 Course 表（依赖已修改完成的 User 表）
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.alter_column('Course_ID',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=20),
               existing_nullable=False)
        batch_op.alter_column('Teacher_ID',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=20),
               existing_nullable=True)
        batch_op.alter_column('name',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=20),
               existing_nullable=True)
        # 重建 Course 对 User 的外键（引用已修改的 User.User_ID）
        batch_op.create_foreign_key(
            batch_op.f('FK_Reference_1'),
            'user', ['Teacher_ID'], ['User_ID'],
            ondelete='RESTRICT', onupdate='RESTRICT'
        )

    # 第四步：修改 Emoji 表（依赖已修改完成的 User 和 Course 表）
    with op.batch_alter_table('emoji', schema=None) as batch_op:
        batch_op.alter_column('Emoji_ID',
               existing_type=mysql.CHAR(length=10),
               type_=sa.String(length=10),
               existing_nullable=False)
        batch_op.alter_column('Student_ID',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=20),
               existing_nullable=False)  # 主键列必须非空
        batch_op.alter_column('Course_ID',
               existing_type=mysql.CHAR(length=20),
               type_=sa.String(length=20),
               existing_nullable=False)  # 主键列必须非空
        # 重建 Emoji 的外键
        batch_op.create_foreign_key(
            batch_op.f('FK_Reference_4'),
            'course', ['Course_ID'], ['Course_ID'],
            ondelete='RESTRICT', onupdate='RESTRICT'
        )
        batch_op.create_foreign_key(
            batch_op.f('FK_Reference_5'),
            'user', ['Student_ID'], ['User_ID'],
            ondelete='RESTRICT', onupdate='RESTRICT'
        )

    # 第五步：处理 Student_Course → Student__Course 表名变更
    # 创建新表（依赖已修改完成的 User 和 Course 表）
    op.create_table('student__course',
    sa.Column('Student_ID', sa.String(length=20), nullable=False),
    sa.Column('Course_ID', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['Course_ID'], ['course.Course_ID'], ondelete='RESTRICT', onupdate='RESTRICT'),
    sa.ForeignKeyConstraint(['Student_ID'], ['user.User_ID'], ondelete='RESTRICT', onupdate='RESTRICT'),
    sa.PrimaryKeyConstraint('Student_ID', 'Course_ID')
    )
    # 删除旧表
    op.drop_table('student_course')

    # ### end Alembic commands ###


def downgrade():
    # ### 降级逻辑：完全反向执行升级步骤 ###
    # 1. 恢复 Student_Course 表
    op.create_table('student_course',
    sa.Column('Student_ID', mysql.CHAR(length=20), nullable=False),
    sa.Column('Course_ID', mysql.CHAR(length=20), nullable=False),
    sa.ForeignKeyConstraint(['Course_ID'], ['course.Course_ID'], name='FK_Reference_3', onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['Student_ID'], ['user.User_ID'], name='FK_Reference_2', onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('Student_ID', 'Course_ID'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.drop_table('student__course')

    # 2. 解除 Emoji 表的外键
    with op.batch_alter_table('emoji', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('FK_Reference_4'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('FK_Reference_5'), type_='foreignkey')
        # 降级 Emoji 字段
        batch_op.alter_column('Emoji_ID',
               existing_type=sa.String(length=10),
               type_=mysql.CHAR(length=10),
               existing_nullable=False)
        batch_op.alter_column('Student_ID',
               existing_type=sa.String(length=20),
               type_=mysql.CHAR(length=20),
               existing_nullable=False)
        batch_op.alter_column('Course_ID',
               existing_type=sa.String(length=20),
               type_=mysql.CHAR(length=20),
               existing_nullable=False)
        # 重建旧外键
        batch_op.create_foreign_key('FK_Reference_4', 'course', ['Course_ID'], ['Course_ID'], onupdate='RESTRICT', ondelete='RESTRICT')
        batch_op.create_foreign_key('FK_Reference_5', 'user', ['Student_ID'], ['User_ID'], onupdate='RESTRICT', ondelete='RESTRICT')

    # 3. 解除 Course 表的外键
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('FK_Reference_1'), type_='foreignkey')
        # 降级 Course 字段
        batch_op.alter_column('name',
               existing_type=sa.String(length=20),
               type_=mysql.CHAR(length=20),
               existing_nullable=True)
        batch_op.alter_column('Teacher_ID',
               existing_type=sa.String(length=20),
               type_=mysql.CHAR(length=20),
               existing_nullable=True)
        batch_op.alter_column('Course_ID',
               existing_type=sa.String(length=20),
               type_=mysql.CHAR(length=20),
               existing_nullable=False)
        # 重建旧外键
        batch_op.create_foreign_key('FK_Reference_1', 'user', ['Teacher_ID'], ['User_ID'], onupdate='RESTRICT', ondelete='RESTRICT')

    # 4. 降级 User 表
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('tele_num',
               existing_type=sa.String(length=11),
               type_=mysql.INTEGER(),
               existing_nullable=True)
        batch_op.alter_column('mail',
               existing_type=sa.String(length=50),
               type_=mysql.CHAR(length=20),
               existing_nullable=True)
        batch_op.alter_column('name',
               existing_type=sa.String(length=10),
               type_=mysql.CHAR(length=10),
               existing_nullable=True)
        batch_op.alter_column('key',
               existing_type=sa.String(length=255),
               type_=mysql.CHAR(length=20),
               existing_nullable=True)
        batch_op.alter_column('User_ID',
               existing_type=sa.String(length=20),
               type_=mysql.CHAR(length=20),
               existing_nullable=False)

    # ### end Alembic commands ###