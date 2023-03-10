from operator import or_
from app import app, db
from datetime import datetime, date
from werkzeug.utils import secure_filename
import pdfkit
import os
from flask import Flask, render_template, redirect, g, url_for, request, flash, session, make_response
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Notification, Student,LeaveStudent, Subject, Teacher, LeaveTeacher, UploadLecture, StudentAttendance, Worker, LeaveWorker, Class



app.config['IMAGE_UPLOADS'] = os.path.join(app.root_path, 'static/image')
#app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]



@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('administrator'))

    if g.user:
        return redirect(url_for('teacher_index'))

    if g.std_user:
        return redirect(url_for('student_index'))
    return render_template('home.html')

#------------ Admin ---------------#


@app.route('/administrator', methods=['GET'])
@login_required
def administrator():
    if not current_user.is_authenticated:
        return redirect(url_for('admin_login'))
        
    students = Student.query.all()
    teachers = Teacher.query.all()
    workers = Worker.query.all()
    classes = Class.query.all()
    leave_std = LeaveStudent.query.all()
    leave_tech = LeaveTeacher.query.all()
    l_worker = LeaveWorker.query.all()
    subjects = Subject.query.all()
    return render_template('administrator/index.html', 
    title='Home',
    nofify=None,
    students=students, 
    teachers=teachers, 
    workers=workers, 
    classes=classes,
    leave_std=leave_std,
    leave_tech=leave_tech,
    l_worker=l_worker,
    subjects=subjects
    )



@app.route('/administrator', methods=['POST'])
@login_required
def post_notification():
    if not current_user.is_authenticated:
        return redirect(url_for('admin_login'))
        
    notification = request.form['notification']
    sender = request.form.get('sender')

    if sender is None:
        flash('Select one of the following option [Student/Teacher, Teacher, Student]')
        return redirect(url_for('administrator'))

    message = Notification(notification=notification, sender=sender)
    db.session.add(message)
    db.session.commit()
    flash('Notifiaction is send to the {}'.format(sender))
    return redirect(url_for('get_notification'))



@app.route('/administrator/get_notification')
@login_required
def get_notification():
    notifications = Notification.query.order_by(Notification.notify_date.desc()).all()
    return render_template('administrator/get_notification.html', title='Notification', notifications=notifications)



@app.route('/administrator/update_notification/<id>', methods=['GET', 'POST'])
@login_required
def update_notification(id):
    notify = Notification.query.filter_by(id=id).first()
    if request.method == 'POST':
        notify.notification = request.form['notification']
        notify.sender = request.form.get('sender')
        db.session.commit()
        flash('Notification is successfully updated!')
        return redirect(url_for('get_notification'))
    return render_template('administrator/index.html', title='Update Notification', notify=notify)



@app.route('/administrator/delete_notification/<id>', methods=['GET', 'POST'])
@login_required
def delete_notification(id):
    try:
        notify = Notification.query.filter_by(id=id).first()
        db.session.delete(notify)
        db.session.commit()
        flash('Notification is successfully deleted!')
        return redirect(url_for('get_notification'))
    except:
        return redirect(url_for('get_notification'))



@app.route('/admin_login', methods=['POST', 'GET'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('administrator'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = True if request.form.get('remember_me') else False 


        admin = User.query.filter_by(username=username).first()
        if admin is None or not admin.check_password(password):
            flash('Invild password or username!')
            return redirect(url_for('admin_login'))

        
        login_user(admin, remember=remember_me)
        flash('Logged in successfully.')
        return redirect('administrator')     

    return render_template('administrator/login.html', title='Login')


@app.route('/admin_logout')
def admin_logout():
    logout_user()
    flash('Successfully logout.')
    return redirect(url_for('home'))


@app.route('/admin_registration', methods=['POST', 'GET'])
def admin_registration():
    if current_user.is_authenticated:
        return redirect(url_for('administrator'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        repeatpassword = request.form['repeatpassword']

        if len(password) < 8:
            flash('Password must be 8 or greater!')
            return redirect(url_for('admin_registration'))

        if password != repeatpassword:
            flash('Your password is not match!')
            return redirect(url_for('admin_registration'))
        
        user = User.query.filter_by(username=username).first()
        if user is not None:
            flash('Please use a different username!')
            return redirect(url_for('admin_registration'))

        user = User.query.filter_by(email=email).first()
        if user is not None:
            flash('Please use a different email!')
            return redirect(url_for('admin_registration'))

        admin = User(username=username, email=email)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        flash("Successfully register")
        return redirect(url_for('admin_login'))
    return render_template('administrator/register.html', title='Registration')


@app.route('/administrator/add_class', methods=['GET', 'POST'])
@login_required
def add_class():
    if request.method == 'POST':
        cls_name = request.form['cls_name']
        cls_fee = request.form['cls_fee']
        admin_id = current_user.id
        db.session.add(Class(cls_name=cls_name, cls_fee=cls_fee, admin_id=admin_id))
        db.session.commit()
        flash('{} is successfully added'.format(cls_name))
        return redirect(url_for('list_of_class'))
    return render_template('administrator/add_class.html', title='Add New Class', u_class=None)


@app.route('/administrator/list_of_class')
@login_required
def list_of_class():
    classes = Class.query.all()
    return render_template('administrator/list_of_class.html', classes=classes)


@app.route('/administrator/update_class/<id>', methods=["GET", "POST"])
@login_required
def update_class(id):
    u_class = Class.query.filter_by(id=id).first()
    if request.method == "POST":
        cls_name = request.form['cls_name']
        u_class.cls_name = cls_name
        db.session.commit()
        flash('{} is successfully update!'.format(u_class.cls_name))
        return redirect(url_for('list_of_class'))
    return render_template('administrator/add_class.html', title='Update Class', u_class=u_class)



@app.route('/administrator/delete_class/<id>')
@login_required
def delete_class(id):
    try:
        d_class = Class.query.filter_by(id=id).first()
        db.session.delete(d_class)
        db.session.commit()
        flash('{} is successfully delete!'.format(d_class.cls_name))
        return redirect(url_for('list_of_class'))
    except:
        pass



@app.route('/administrator/class_wise_student/<std_class>')
@login_required
def class_wise_student(std_class):
    query = request.args.get('query')
    if query:
        students = Student.query.filter(Student.std_name.contains(query)|
                                        Student.f_name.contains(query))
        return render_template('administrator/class_wise_student.html', title='Class Wise Student', query=query, students=students)

    page = request.args.get('page', 1, type=int)
    class_name = Class.query.filter_by(id=std_class).first()
    students = Student.query.filter_by(std_class=std_class).order_by(Student.id.asc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('class_wise_student', std_class=std_class, page=students.next_num) \
        if students.has_next else None
    prev_url = url_for('class_wise_student', std_class=std_class, page=students.prev_num) \
        if students.has_prev else None
    return render_template('administrator/class_wise_student.html', title='Class Wise Student', class_name=class_name, students=students.items, next_url=next_url, prev_url=prev_url)




@app.route('/administrator/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    classes = Class.query.all()
    if request.method == 'POST':
        std_name = request.form['std_name']
        f_name = request.form['f_name']
        std_address = request.form['std_address']
        std_contact = request.form['std_contact']
        gender = request.form['gender']
        stdclass = request.form['stdclass']

        if stdclass == 'Open this select class':
            flash('Please etner class!')
            return redirect(url_for('add_student'))

        classes = Class.query.filter_by(id=stdclass).first()
        student = Student(
            std_name=std_name,
            f_name=f_name,
            std_address=std_address,
            std_contact=std_contact,
            gender=gender,
            stdclass=classes,
            admin=current_user
                        )
        db.session.add(student)
        db.session.commit()
        flash('{} is successfully added'.format(std_name))
        return redirect(url_for('add_student'))

    return render_template('administrator/add_student.html', title='Add Student', classes=classes, student=None)


@app.route('/administrator/student_Detials', methods=['GET', 'POST'])
@login_required
def student_Detials():
    query = request.args.get('query')
    if query:
        students = Student.query.filter(Student.std_name.contains(query)|
                                        Student.f_name.contains(query))
        return render_template('administrator/student_Detials.html', title='Student Detials', students=students, query=query)
        
    page = request.args.get('page', 1, type=int)
    students = Student.query.order_by(Student.id.asc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('student_Detials', page=students.next_num) \
        if students.has_next else None
    prev_url = url_for('student_Detials', page=students.prev_num) \
        if students.has_prev else None
    return render_template('administrator/student_Detials.html', title='Student Detials', students=students.items, next_url=next_url, prev_url=prev_url)


@app.route('/administrator/student_detials_pdf')
@login_required
def student_detials_pdf():
    students = Teacher.query.all()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/student_detials_pdf.html", students=students)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response


@app.route('/administrator/student_profile/<id>')
@login_required
def student_profile(id):
    student = Student.query.filter_by(id=id).first()
    return render_template('administrator/student_profile.html', title='Student Profile', student=student)


@app.route('/administrator/student_profile_pdf/<id>')
@login_required
def student_profile_pdf(id):
    students = Teacher.query.filter_by(id=id).first()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/student_profile_pdf.html", student=students)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response


@app.route('/administrator/update_student/<id>', methods=['POST', 'GET'])
@login_required
def update_student(id):
    classes = Class.query.all()
    student = Student.query.filter_by(id=id).first()
    if request.method == 'POST':
        student.std_name = request.form['std_name']
        student.f_name = request.form['f_name']
        student.std_address = request.form['std_address']
        student.std_contact = request.form['std_contact']
        student.gender = request.form['gender']

        std_class = request.form['stdclass']
        if std_class == 'Open this select class':
            flash('Please etner class!')
            return redirect(url_for('update_student', id=student.id))

        student.std_class = std_class
        
        student.admin_id = current_user.id
        db.session.commit()
        flash('{} is successfully update!'.format(student.std_name))
        return redirect(url_for('student_profile', id=student.id))
    return render_template('administrator/add_student.html', title='Update Student', student=student, classes=classes)


@app.route('/administrator/leave_student/<id>')
@login_required
def leave_student(id):
    student = Student.query.filter_by(id=id).first()
    std_name = student.std_name
    f_name = student.f_name
    std_address = student.std_address
    std_contact = student.std_contact
    gender = student.gender
    leave_date = student.join_date
    std_class = student.stdclass.id
    admin_id = current_user.id
    l_student = LeaveStudent(
        std_name=std_name,
        f_name=f_name,
        std_address=std_address,
        std_contact=std_contact,
        gender=gender,
        leave_date=leave_date,
        std_class=std_class,
        admin_id=admin_id
    )
    db.session.add(l_student)
    db.session.delete(student)
    db.session.commit()
    flash('{} is successfully leave!'.format(std_name))
    return redirect(url_for('student_Detials'))


@app.route('/administrator/leave_student_detials')
@login_required
def leave_student_detials():
    query = request.args.get('query')
    if query:
        students = LeaveStudent.query.filter(LeaveStudent.std_name.contains(query)|
                                        LeaveStudent.f_name.contains(query))
        return render_template('administrator/leave_student_detials.html', title='Leave Students Detials', students=students, query=query)
    page = request.args.get('page', 1, type=int)
    students = LeaveStudent.query.order_by(LeaveStudent.id.asc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('leave_student_detials', page=students.next_num) \
        if students.has_next else None
    prev_url = url_for('leave_student_detials', page=students.prev_num) \
        if students.has_prev else None
    return render_template('administrator/leave_student_detials.html', title='Leave Students Detials', students=students.items, next_url=next_url, prev_url=prev_url)


@app.route('/administrator/leave_student_pdf')
@login_required
def leave_student_pdf():
    students = Teacher.query.all()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/leave_student_pdf.html", students=students)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response


@app.route('/administrator/leave_student_delete/<id>')
@login_required
def leave_student_delete(id):
    try:
        student = LeaveStudent.query.filter_by(id=id).first()
        db.session.delete(student)
        db.session.commit()
        flash('{} is successfully delete!'.format(student.std_name))
        return redirect(url_for('leave_student_detials'))
    except:
        pass


@app.route('/administrator/add_subject', methods=['POST', 'GET'])
@login_required
def add_subject():
    if request.method == 'POST':
        sub_name = request.form['sub_name']
        admin_id = current_user.id
        subject = Subject(sub_name=sub_name, admin_id=admin_id)
        db.session.add(subject)
        db.session.commit()
        flash('{} subject is successfully added!'.format(sub_name))
        return redirect(url_for('list_of_subject'))
    return render_template('administrator/add_subject.html', title='Add Subject', subjects=None)


@app.route('/administrator/list_of_subject/')
@login_required
def list_of_subject():
    subjects = Subject.query.all()
    return render_template('administrator/list_of_subject.html', title='Subject', subjects=subjects)


@app.route('/administrator/update_subject/<id>', methods=['GET', 'POST'])
@login_required
def update_subject(id):
    subjects = Subject.query.filter_by(id=id).first()
    if request.method == 'POST':
        subjects.sub_name = request.form['sub_name']
        subjects.admin_id = current_user.id
        db.session.commit()
        flash('{} subject is successfully added!'.format(subjects.sub_name))
        return redirect(url_for('list_of_subject'))
    return render_template('administrator/add_subject.html', title='Add Subject', subjects=subjects)



@app.route('/administrator/delete_subject/<id>')
@login_required
def delete_subject(id):
    subject = Subject.query.filter_by(id=id).first()
    if subject:
        db.session.delete(subject)
        db.session.commit()
        flash('{} subject is successfully added!'.format(subject.sub_name))
        return redirect(url_for('list_of_subject'))


@app.route('/administrator/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    classes = Class.query.all()
    subjects = Subject.query.all()
    if request.method == 'POST':
        tech_name = request.form['tech_name']
        email = request.form['email']
        tech_address = request.form['tech_address']
        tech_contact = request.form['tech_contact']
        gender = request.form['gender']
        admin_id = current_user.id
        tech_subject = request.form['tech_subject']
        salary = request.form['salary']
        tech_class = request.form['stdclass']

        if tech_subject == 'Open this select subject':
            flash('Please etner subject!')
            return redirect(url_for('add_teacher')) 

        if tech_class == 'Open this select class':
            tech_class = 'None'


        #tech_subject = Subject.query.filter_by(id=tech_subject.id).first()
        teacher = Teacher(
            tech_name=tech_name, 
            email=email, 
            tech_address=tech_address,
            tech_contact=tech_contact,
            gender=gender,
            salary=salary,
            admin_id=admin_id,
            tech_subject=tech_subject,
            tech_class=tech_class
            )
        db.session.add(teacher)
        db.session.commit()
        flash('{} teacher is successfully added!'.format(tech_name))
        return redirect(url_for('teacher_detials'))

    return render_template('administrator/add_teacher.html', title='Add Teacher', subjects=subjects, classes=classes, teacher=None)


@app.route('/administrator/teacher_detials')
@login_required
def teacher_detials():
    query = request.args.get('query')
    if query:
        teachers = Teacher.query.filter(Teacher.tech_name.contains(query))
        return render_template('administrator/teacher_detials.html', title='Teachers', teachers=teachers, query=query)
    
    page = request.args.get('page', 1, type=int)  
    teachers = Teacher.query.order_by(Teacher.id.asc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('teacher_detials', page=teachers.next_num) \
        if teachers.has_next else None
    prev_url = url_for('teacher_detials', page=teachers.prev_num) \
        if teachers.has_prev else None
    return render_template('administrator/teacher_detials.html', title='Teachers', teachers=teachers.items, next_url=next_url, prev_url=prev_url,)


@app.route('/administrator/teacher_detials_pdf')
@login_required
def teacher_detials_pdf():
    teachers = Teacher.query.all()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/teacher_detials_pdf.html", teachers=teachers)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response


@app.route('/administrator/teacher_profile/<id>')
@login_required
def teacher_profile(id):
    teacher = Teacher.query.filter_by(id=id).first()
    return render_template('administrator/teacher_profile.html', title='Teacher Profile', teacher=teacher)


@app.route('/administrator/teacher_profile_pdf/<id>')
@login_required
def teacher_profile_pdf(id):
    teachers = Teacher.query.filter_by(id=id).first()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/teacher_profile_pdf.html", teacher=teachers)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response




@app.route('/administrator/update_teacher/<id>', methods=['GET', 'POST'])
@login_required
def update_teacher(id):
    subjects = Subject.query.all()
    teacher = Teacher.query.filter_by(id=id).first()
    if request.method == 'POST':
        teacher.tech_name = request.form['tech_name']
        teacher.email = request.form['email']
        teacher.tech_address = request.form['tech_address']
        teacher.tech_contact = request.form['tech_contact']
        teacher.gender = request.form['gender']
        teacher.salary = request.form['salary']
        teacher.admin_id = current_user.id
        tech_subject =  request.form['tech_subject']

        if tech_subject == 'Open this select subject':
            flash('Please etner subject!')
            return redirect(url_for('update_teacher', id=teacher.id))


        teacher.tech_subject = tech_subject
        db.session.commit()
        flash('Teacher {} successfully update!'.format(teacher.tech_name))
        return redirect(url_for('teacher_profile', id=teacher.id))
    return render_template('administrator/add_teacher.html', title='Update Teacher', teacher=teacher, subjects=subjects)


@app.route('/administrator/leave_teacher/<id>')
@login_required
def leave_teacher(id):
    teacher = Teacher.query.filter_by(id=id).first()
    if teacher:
        tech_name = teacher.tech_name
        email = teacher.email
        tech_address = teacher.tech_address
        tech_contact = teacher.tech_contact
        gender = teacher.gender
        salary = teacher.salary
        admin_id = current_user.id
        tech_subject = teacher.tech_subject
        l_teacher = LeaveTeacher(
            tech_name=tech_name,
            email=email,
            tech_address=tech_address,
            tech_contact=tech_contact,
            gender=gender,
            salary=salary,
            admin_id=admin_id,
            tech_subject=tech_subject
            )
        db.session.add(l_teacher)
        db.session.delete(teacher)
        db.session.commit()
        flash('Teacher {} successfully leave!'.format(tech_name))
        return redirect(url_for('teacher_detials'))
    

@app.route('/administrator/leave_teacher_detials')
@login_required
def leave_teacher_detials():
    query = request.args.get('query')
    if query:
        teachers = LeaveTeacher.query.filter(LeaveTeacher.tech_name.contains(query))
        return render_template('administrator/leave_teacher_detials.html', title='Leave Teachers', teachers=teachers, query=query)
    
    page = request.args.get('page', 1, type=int)
       
    teachers = LeaveTeacher.query.order_by(LeaveTeacher.id.asc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('leave_teacher_detials', page=teachers.next_num) \
        if teachers.has_next else None
    prev_url = url_for('leave_teacher_detials', page=teachers.prev_num) \
        if teachers.has_prev else None
    return render_template('administrator/leave_teacher_detials.html', title='Leave Teachers', teachers=teachers.items, next_url=next_url, prev_url=prev_url,)


@app.route('/administrator/leave_teacher_pdf')
@login_required
def leave_teacher_pdf():
    teachers = LeaveTeacher.query.all()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/leave_teacher_pdf.html", teachers=teachers)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response


@app.route('/administrator/leave_teacher_delete/<id>')
@login_required
def leave_teacher_delete(id):
    teacher = LeaveTeacher.query.filter_by(id=id).first()
    if teacher:
        db.session.delete(teacher)
        db.session.commit()
        flash('Teacher {} is successfully delete!'.format(teacher.tech_name))
        return redirect(url_for('leave_teacher_detials'))


@app.route('/administrator/add_worker', methods=['GET', 'POST'])
@login_required
def add_worker():
    if request.method == 'POST':
        worker_name = request.form['worker_name']
        worker_address = request.form['worker_address']
        worker_contact = request.form['worker_contact']
        worker = Worker(worker_name=worker_name, worker_address=worker_address, worker_contact=worker_contact, admin=current_user)
        db.session.add(worker)
        db.session.commit()
        flash('{} is successfully added'.format(worker_name))
        return redirect(url_for('worker_detials'))

    return render_template('administrator/worker.html', title='Worker', worker=None)



@app.route('/administrator/worker_detials')
@login_required
def worker_detials():
    query = request.args.get('query')
    if query:
        workers = Worker.query.filter(Worker.worker_name.contains(query))
        return render_template('administrator/worker_detials.html', title='Search Worker', workers=workers, query=query)
    
    page = request.args.get('page', 1, type=int)   
    workers = Worker.query.order_by(Worker.id.asc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('worker_detials', page=workers.next_num) \
        if workers.has_next else None
    prev_url = url_for('worker_detials', page=workers.prev_num) \
        if workers.has_prev else None
    return render_template('administrator/worker_detials.html', title='Worker Detials', workers=workers.items, next_url=next_url, prev_url=prev_url, page=page)


@app.route('/administrator/worker_detials_pdf')
@login_required
def worker_detials_pdf():
    workers = Worker.query.all()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/worker_detials_pdf.html", workers=workers)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response


@app.route('/administrator/update_worker/<id>', methods=['GET', 'POST'])
@login_required
def update_worker(id):
    worker = Worker.query.filter_by(id=id).first()
    if request.method == 'POST':
        worker.worker_name = request.form['worker_name']
        worker.worker_address = request.form['worker_address']
        worker.worker_contact = request.form['worker_contact']
        worker.admin_id = current_user.id
        worker.join_date = datetime.utcnow()
        db.session.commit()
        flash('{} is successfully update'.format(worker.worker_name))
        return redirect(url_for('worker_detials'))

    return render_template('administrator/worker.html', title='Worker', worker=worker)



@app.route('/administrator/leave_worker/<id>')
@login_required
def leave_worker(id):
    worker = Worker.query.filter_by(id=id).first()
    try:
        if worker:
            leave_worker_name = worker.worker_name
            leave_worker_address = worker.worker_address
            leave_worker_contact = worker.worker_contact
            admin_id = current_user.id
            l_worker = LeaveWorker(
                            leave_worker_name=leave_worker_name,
                            leave_worker_address=leave_worker_address, 
                            leave_worker_contact=leave_worker_contact,
                            admin_id=admin_id)
            db.session.add(l_worker)
            db.session.commit()
            
            db.session.delete(worker)
            db.session.commit()
            flash('{} is successfully leave'.format(worker.worker_name))
            return redirect(url_for('worker_detials'))
    except:
        return redirect(url_for('worker_detials'))


@app.route('/administrator/leave_worker_detials')
@login_required
def leave_worker_detials():
    query = request.args.get('query')
    if query:
        leave_worker = LeaveWorker.query.filter(LeaveWorker.leave_worker_name.contains(query))
        return render_template('administrator/leave_worker.html', title='Leave Worker', leave_worker=leave_worker, query=query)
        
    page = request.args.get('page', 1, type=int)
    leave_worker = LeaveWorker.query.order_by(LeaveWorker.id.asc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('leave_worker_detials', page=leave_worker.next_num) \
        if leave_worker.has_next else None
    prev_url = url_for('leave_worker_detials', page=leave_worker.prev_num) \
        if leave_worker.has_prev else None
    return render_template('administrator/leave_worker.html', title='Leave Worker', leave_worker=leave_worker.items, next_url=next_url, prev_url=prev_url)


@app.route('/administrator/leave_worker_pdf', methods=['POST'])
@login_required
def leave_worker_pdf():
    leave_worker = LeaveWorker.query.all()
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    html = render_template("administrator/leave_worker_pdf.html", leave_worker=leave_worker)
    pdf = pdfkit.from_string(html, False, configuration=config)
    response = make_response(pdf)
    response.headers["content-Type"] = "application/pdf"
    response.headers["content-Disposition"] = "inline: filename=output.pdf"
    return response



@app.route('/administrator/leave_worker_delete/<id>')
@login_required
def leave_worker_delete(id):
    leave_worker = LeaveWorker.query.filter_by(id=id).first()
    try:
        if leave_worker:
            db.session.delete(leave_worker)
            db.session.commit()
            flash('Worker {} is premenent delete!'.format(leave_worker.leave_worker_name))
            return redirect(url_for('leave_worker_detials'))
    except:
        return redirect(url_for('leave_worker_detials'))


#------------- End Admin ---------------#






#------------- Teacher -----------------#

@app.before_request
def before_request():
    g.user = None
    if 'teacher_id' in session:
        user = Teacher.query.filter_by(id=session['teacher_id']).first()
        g.user = user
    

@app.route('/teacher/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if g.user:
        return redirect(url_for('teacher_index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Teacher.query.filter_by(tech_name=username).first()
        if user and user.tech_contact == password:
            session['teacher_id'] = user.id
            flash('Successfully loggin!')
            return redirect(url_for('teacher_index'))

        flash('Invilde username or password')
        return redirect(url_for('teacher_login'))
    return render_template('teacher/teacher_login.html', title='Teacher Login')



@app.route('/teacher/teacher_logout')
def teacher_logout():
    session.pop('teacher_id', None)
    return redirect(url_for('home'))



@app.route('/teacher/teacher_index', methods=['GET', 'POST'])
def teacher_index():
    if not g.user:
        return redirect(url_for('teacher_login'))

    subjects = Subject.query.all()
    classes = Class.query.all()
    if request.method == 'POST':
        tech_subject = request.form.get('tech_subject')
        tech_class = request.form.get('stdclass')
        teacher = g.user.id

        if tech_subject == 'Open this select subject':
            flash('Please select subject!')
            return redirect(url_for('teacher_index'))

        if tech_class == 'Open this select class':
            flash('Please select class')
            return redirect(url_for('teacher_index'))

        return redirect(url_for('lectures_view', tech_subject=tech_subject, tech_class=tech_class, teacher=teacher))
    
    return render_template('teacher/index.html', title='Home', subjects=subjects, classes=classes)




def allowed_image(filename):

    if not "." in filename:
        flash('Image must be [jpeg, jpg, png, gif]')
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        flash('Image must be [jpeg, jpg, png, gif]')
        return False



@app.route('/teacher/upload_lecture', methods=['GET', 'POST'])
def upload_lecture():
    if not g.user:
        return redirect(url_for('teacher_login'))

    subjects = Subject.query.all()
    classes = Class.query.all()
    if request.method == 'POST':
        title = request.form['title']
        lecture = request.form['lecture']
        teacher = g.user.id
        tech_subject = request.form['tech_subject']
        tech_class = request.form['stdclass']

        if tech_subject == 'Open this select subject':
            flash('Please select subject!')
            return redirect(url_for('upload_lecture'))

        if tech_class == 'Open this select class':
            flash('Please select class')
            return redirect(url_for('upload_lecture'))



        img = request.files['image']
        if img.filename == '':
            flash('Please upload image!')

        if allowed_image(img.filename):
            filename = secure_filename(img.filename)
            img.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
            new_lecture = UploadLecture(
                title=title, 
                lecture=lecture, 
                teacher=teacher, 
                img=img.read(), 
                img_name=filename,
                tech_subject=tech_subject,
                tech_class=tech_class
                )
            db.session.add(new_lecture)
            db.session.commit()
            flash('Successfully upload!')
            return redirect(url_for('lectures_view', tech_subject=tech_subject, tech_class=tech_class, teacher=teacher))
          
    return render_template('teacher/add_lecture.html', subjects=subjects, classes=classes, lecture=None)





@app.route('/teacher/lectures_view/<tech_subject>/<tech_class>/<teacher>', methods=['GET', 'POST'])
def lectures_view(tech_subject, tech_class, teacher):
    if not g.user:
        return redirect(url_for('teacher_login'))

    lectures = UploadLecture.query.filter_by(
        tech_subject=tech_subject, 
        tech_class=tech_class, 
        teacher=teacher).order_by(UploadLecture.upload_date.desc()).all()
    return render_template('teacher/preview_lecture.html', lectures=lectures)





@app.route('/teacher/lecture_detial_view/<id>')
def lecture_detial_view(id):
    if not g.user:
        return redirect(url_for('teacher_login'))
        
    lecture = UploadLecture.query.filter_by(id=id).first()
    return render_template('teacher/lecture_detial_view.html', lecture=lecture)



@app.route('/teacher/update_lecture/<id>', methods=['GET', 'POST'])
def update_lecture(id=id):
    if not g.user:
        return redirect(url_for('teacher_login'))

    subjects = Subject.query.all()
    classes = Class.query.all()
    lecture = UploadLecture.query.filter_by(id=id).first()
    if request.method == 'POST':
        lecture.title = request.form['title']
        lecture.lecture = request.form['lecture']
        tech_subject = request.form['tech_subject']
        tech_class = request.form['stdclass']
        lecture.teacher = g.user.id

        if tech_subject == 'Open this select subject':
            flash('Please select subject!')
            return redirect(url_for('upload_lecture'))

        if tech_class == 'Open this select class':
            flash('Please select class')
            return redirect(url_for('upload_lecture'))

        lecture.tech_subject = tech_subject
        lecture.tech_class = tech_class

        image = request.files['image']
        
        if image.filename == '':
            flash('Please upload image!')
            return redirect(url_for('update_lecture', id=id))

        if allowed_image(image.filename):
            filename = secure_filename(image.filename)
            lecture.img_name = filename
            image.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))

            db.session.commit()
            return redirect(url_for('preview_lecture', teacher=g.user.id))
            
    return render_template('teacher/add_lecture.html', lecture=lecture, subjects=subjects, classes=classes)




@app.route('/teacher/take_student_attendance/<class_id>', methods=['GET', 'POST'])
def take_student_attendance(class_id):
    if not g.user:
        return redirect(url_for('teacher_login'))

    students = Student.query.filter_by(std_class=class_id).all()

    if request.method == 'POST':
        attendance = request.form.get('attendance')
        if attendance == None:
            flash('Please select one of these [Present, Absent, Leave]')
            return redirect(url_for('take_student_attendance', class_id=g.user.stdclass.id))
                
        std_id = request.form.get('std_id')
        clas_id = class_id
        teacher_id = g.user.id

        std = StudentAttendance.query.filter_by(std_id=std_id).order_by(StudentAttendance.date.desc()).first()
        today = datetime.utcnow()
        if std is not None and std.date.strftime("%d/%m/%Y") == today.strftime("%d/%m/%Y"):
            flash('You already take attendance of student {}'.format(std.std.std_name))
            return redirect(url_for('take_student_attendance', class_id=g.user.stdclass.id))

        take_attendance = StudentAttendance(std_id=std_id, class_id=clas_id, teacher_id=teacher_id, attendance=attendance)
        db.session.add(take_attendance)
        db.session.commit()
        flash('Successfull take attendance!')
        return redirect(url_for('take_student_attendance', class_id=g.user.stdclass.id))

            
    return render_template('teacher/take_student_attendance.html', students=students)



@app.route('/teacher/show_student_attendance/<teacher_id>/<class_id>')
def show_student_attendance(teacher_id, class_id):
    if not g.user:
        return redirect(url_for('teacher_login'))
    
    page = request.args.get('page', 1, type=int)
    query = StudentAttendance.query.filter_by(teacher_id=teacher_id, class_id=class_id).order_by(StudentAttendance.date.desc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('show_student_attendance', teacher_id=teacher_id, class_id=class_id, page=query.next_num) \
        if query.has_next else None
    prev_url = url_for('show_student_attendance', teacher_id=teacher_id, class_id=class_id, page=query.prev_num) \
        if query.has_prev else None
    return render_template('teacher/show_student_attendance.html', query=query.items, next_url=next_url, prev_url=prev_url)



@app.route('/teacher/teacher_notification')
def teacher_notification():
    notifications = Notification.query.filter(Notification.sender != 'Student').order_by(Notification.notify_date.desc()).all()
    return render_template('teacher/teacher_notification.html', notifications=notifications)


#------------- End Teacher -------------#






#------------- Student -----------------#


@app.before_request
def std_before_request():
    g.std_user = None
    if 'student_id' in session:
        std_user = Student.query.filter_by(id=session['student_id']).first()
        g.std_user = std_user



@app.route('/student/student_login', methods=['GET', 'POST'])
def student_login():
    if g.std_user:
        return redirect(url_for('student_index')) 

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        std_user = Student.query.filter_by(std_name=username).first()
        if std_user and std_user.std_contact == password:
            session['student_id'] = std_user.id
            flash('Successfully login!')
            return redirect(url_for('student_index'))

        flash('Invild username or password!')
        return redirect(url_for('student_login'))
    return render_template('student/student_login.html', title='Student Login')



@app.route('/student/student_logout')
def student_logout():
    session.pop('student_id', None)
    return redirect(url_for('home'))




@app.route('/student/student_index', methods=['GET', 'POST'])
def student_index():
    if not g.std_user:
        return redirect(url_for('student_login'))
    
    teachers = Teacher.query.all()
    subjects = Subject.query.all()
    #classes = Class.query.all()
    if request.method == 'POST':
        tech_subject = request.form.get('tech_subject')
        #tech_class = request.form.get('stdclass')
        teacher = request.form.get('teacher')

        if tech_subject == 'Open this select Teacher':
            flash('Please select subject!')
            return redirect(url_for('student_index'))

        if tech_subject == 'Open this select subject':
            flash('Please select subject!')
            return redirect(url_for('student_index'))

        #if tech_class == 'Open this select class':
            #flash('Please select class')
            #return redirect(url_for('student_index'))

        return redirect(url_for('std_lectures_view', tech_subject=tech_subject, tech_class=g.std_user.stdclass.id, teacher=teacher))
    
    return render_template('student/index.html', teachers=teachers, subjects=subjects)#, classes=classes)


@app.route('/student/std_lectures_view/<tech_subject>/<tech_class>/<teacher>', methods=['GET', 'POST'])
def std_lectures_view(tech_subject, tech_class, teacher):
    if not g.std_user:
        return redirect(url_for('student_login'))

    lectures = UploadLecture.query.filter_by(
        tech_subject=tech_subject, 
        tech_class=tech_class, 
        teacher=teacher).order_by(UploadLecture.upload_date.desc()).all()
    return render_template('student/std_lectures_view.html', lectures=lectures)


@app.route('/student/std_lecture_detial_view/<id>')
def std_lecture_detial_view(id):
    if not g.std_user:
        return redirect(url_for('student_login'))
        
    lecture = UploadLecture.query.filter_by(id=id).first()
    return render_template('student/std_lecture_detial_view.html', lecture=lecture)



@app.route('/student/student_attendance_view/<std_id>/<class_id>')
def student_attendance_view(std_id, class_id):
    if not g.std_user:
        return redirect(url_for('student_login'))
    
    page = request.args.get('page', 1, type=int)  
    query = StudentAttendance.query.filter_by(std_id=std_id, class_id=class_id).order_by(StudentAttendance.date.desc()).paginate(
        page, app.config['ENTRY_PER_PAGE'], False)
    next_url = url_for('student_attendance_view', std_id=std_id, class_id=class_id, page=query.next_num) \
        if query.has_next else None
    prev_url = url_for('student_attendance_view', std_id=std_id, class_id=class_id, page=query.prev_num) \
        if query.has_prev else None
    return render_template('student/student_attendance_view.html', query=query.items, next_url=next_url, prev_url=prev_url)


@app.route('/student/student_notification')
def student_notification():
    notifications = Notification.query.filter(Notification.sender != 'Teacher').order_by(Notification.notify_date.desc()).all()
    return render_template('student/student_notification.html', notifications=notifications)


#------------- End Student -------------#





