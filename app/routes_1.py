from flask import render_template, redirect, url_for, flash, request, session
from datetime import datetime
import uuid

from app import app, db
from app.models import User, Course, Student_Course, Emoji
from config import EMOJI_TYPE_MAP

# 查看学生端课程列表
@app.route('/student/courses')
def student_courses():
    if session.get('user_type') != 3:
        flash('无权限访问学生端功能', 'danger')
        return redirect(url_for('welcome'))

    student_id = session['user_id']
    courses = Course.query.join(Student_Course)\
                          .filter(Student_Course.student_id == student_id)\
                          .all()

    return render_template('student/courses.html', courses=courses, EMOJI_TYPE_MAP=EMOJI_TYPE_MAP)


# 发送 Emoji 功能
@app.route('/student/course/<course_id>/send_emoji', methods=['POST'])
def send_emoji(course_id):
    if session.get('user_type') != 3:
        flash('无权限访问学生端功能', 'danger')
        return redirect(url_for('welcome'))

    student_id = session['user_id']
    emoji_type = int(request.form.get('emoji_type'))

    new_emoji = Emoji(
        id=str(uuid.uuid4())[:8],
        student_id=student_id,
        course_id=course_id,
        time=datetime.now(),
        type=emoji_type
    )

    db.session.add(new_emoji)
    db.session.commit()

    flash('Emoji 发送成功！', 'success')
    return redirect(url_for('student_courses'))

# 撤回 Emoji 功能
@app.route('/student/emoji/<emoji_id>/delete')
def delete_emoji(emoji_id):
    if session.get('user_type') != 3:
        flash('无权限访问学生端功能', 'danger')
        return redirect(url_for('welcome'))

    emoji = Emoji.query.get_or_404(emoji_id)

    if emoji.student_id != session['user_id']:
        flash('你不能删除不是你发的 Emoji', 'danger')
        return redirect(url_for('welcome'))

    db.session.delete(emoji)
    db.session.commit()

    flash('Emoji 已删除', 'success')
    return redirect(url_for('student_emoji_history'))

# 查看学生端 Emoji 历史记录
@app.route('/student/emoji/history')
def student_emoji_history():
    if session.get('user_type') != 3:
        flash('无权限访问学生端功能', 'danger')
        return redirect(url_for('welcome'))

    student_id = session['user_id']
    history = Emoji.query.filter(
        Emoji.student_id == student_id,
        Emoji.type.between(1, 10)  # 只查询类型1-10
    ).order_by(Emoji.time.desc()).all()

    return render_template('student/history.html', history=history)


# 教师端

@app.route('/teacher/courses')
def teacher_courses():
    if session.get('user_type') != 2:
        flash('无权限访问教师端功能', 'danger')
        return redirect(url_for('welcome'))

    teacher_id = session['user_id']
    courses = Course.query.filter_by(teacher_id=teacher_id).all()

    return render_template('teacher/courses.html', courses=courses)

@app.route('/teacher/course/<course_id>/timeline')
def teacher_course_timeline(course_id):
    if session.get('user_type') != 2:
        flash('无权限访问教师端功能', 'danger')
        return redirect(url_for('welcome'))

    emojis = Emoji.query.filter(Emoji.course_id == course_id,
                              Emoji.type.between(1, 10))\
                        .options(db.joinedload(Emoji.student))\
                        .options(db.joinedload(Emoji.course))\
                        .order_by(Emoji.time.asc()).all()

    return render_template('teacher/timeline.html', emojis=emojis)

@app.route('/teacher/course/<course_id>/stats')
def teacher_course_stats(course_id):
    if session.get('user_type') != 2:
        flash('无权限访问教师端功能', 'danger')
        return redirect(url_for('welcome'))

    stats = db.session.query(
        Emoji.type,
        db.func.count(Emoji.type)
    ).filter(
        Emoji.course_id == course_id,
        Emoji.type.between(1, 10)  # 只选择1-10类型
    ).group_by(Emoji.type).all()

    return render_template('teacher/stats.html', stats=stats)

