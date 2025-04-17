import os, sys
from io import StringIO
from flask import *
from sender import send_email_message
from uroki import lessons, video
from db import *
import requests

app = Flask(__name__)
app.secret_key = 'blablabla'

@app.route('/')
def home():
    return render_template('index.html')

# Логин учителя и ученика
@app.route('/form_login', methods=['POST'])
def check_login_form():
    email = request.form.get('email')
    password = request.form.get('password')
    data = {"email": email, "password": password}
    req = requests.post('http://127.0.0.1:5000/api/v1/auth', json=data)
    print(req.json())
    u = req.json()
    u['email'] = email
    u['password'] = password
    if u['email'] == email and u['password'] == password:
        if u['role'] == 'Ученик':
            session['student'] = u
            print(u)
            return redirect('/student')
        if u['role'] == 'Учитель':
            session['teacher'] = u
            return redirect('/teacher')

@app.route('/email', methods=['POST'])
def teacher_email():
    message = request.form.get('message')
    text = f'Новое сообщение от учителя {session["teacher"]["name"]}, {session["teacher"]["email"]}:<p>{message}</p>'
    send_email_message(
        'ponyatojkina.ks@mail.ru', text, 'Вопрос от учителя'
    )
    return redirect('/teacher')

# Страница ученика
@app.route('/student')
def student():
    auth = session['student']
    data = {"class": auth["class"], "teacher": "Моргуненко ЕЮ"}
    req = requests.post('http://127.0.0.1:5000/api/v1/info/class_stars', json=data)
    if req.status_code == 200:
        pass
    user = ''
    return render_template('student_cabinet.html', user=auth, users=req)


# Страница учителя
@app.route('/teacher')
def teacher():
    auth = session['teacher']
    filter = request.args.get('filter')
    return render_template('teacher_cabinet.html', user=auth, users=users, filter=filter)

# Список уроков для ученика
@app.route('/student_education')
def student_education():
    auth = session['student']
    if auth == None:
        return redirect('/')
    return render_template('student_education.html', user=auth, lessons=lessons)

@app.route('/student_video')
def student_video():
    auth = session['student']
    if auth == None:
        return redirect('/')
    return render_template('student_video.html', user=auth, videos=video)

# Урок (открывается по Id урока и шагу)
@app.route('/lessons/<id>/<step>')
def open_lesson(id, step):
    id = int(id)
    step = int(step)
    auth = session['student']
    code = ''
    if auth == None:
        return redirect('/')
    for l in lessons:
        if l['number'] == id:
            text_q = []
            quest_q = []
            code_q = []
            for j in l['lessons']:
                if j['type'] == 'text':
                    text_q.append(j)
                if j['type'] == 'question':
                    quest_q.append(j)
                if j['type'] == 'code':
                    code_q.append(j)
            return render_template('lesson.html', user=auth, l=l, step=step, text=text_q, quest=quest_q, code_q=code_q)
    return redirect('/student_education')

@app.route('/add_student', methods=['POST'])
def post_add_student():
    name = request.form['name']
    clas = request.form['class']
    email = request.form['email']
    password = request.form['password']
    data = {"name": name, "email": email, "password": password, "role": "Ученик", "class":clas, "stars": 0, "raiting": 0, "teacher": "Моргуненко ЕЮ"}
    req = requests.post('http://127.0.0.1:5000/api/v1/info/add_student', json=data)
    if req.status_code == 200:
        pass
    return redirect('/teacher')

@app.route('/del_student', methods=['POST'])
def post_del_student():
    email = request.form['email']
    data = {"email": email }
    req = requests.delete('http://127.0.0.1:5000/api/v1/info/del_student', json=data)
    if req.status_code == 200:
        pass
    return redirect('/teacher')

# Ответ на вопрос урока
@app.route('/answer/<id>/<step>', methods=['POST'])
def open_answer(id, step):
    id = int(id)
    step = int(step)
    auth = session['student']
    answer = request.form['answer']
    if auth == None:
        return redirect('/')
    if answer == 'True':
        data = {"user": auth, "id": id, "step": step, "answer": answer}
        req = requests.post('http://127.0.0.1:5000/api/v1/task/done_task', json=data)
        if req.status_code == 200:
            pass
    l, text_q, quest_q, code_q = get_lessons(id)
    return render_template('lesson.html', user=auth, l=l, step=step, is_true=answer, text=text_q, quest=quest_q, code_q=code_q)

# Ответ на вопрос урока (код)
@app.route('/code/<id>/<step>', methods=['POST'])
def open_code(id, step):
    id = int(id)
    step = int(step)
    auth = session['student']
    answer = request.form['answer']
    counter = 0
    kolvo = 0
    if auth == None:
        return redirect('/')
    user_output = []
    for l in lessons:
        if l['number'] == id:
            for s in l['lessons']:
                if s['num'] == step:
                    i_data = []
                    o_data = []
                    for j in s['io_data']:
                        i_data.append(j['input'])
                    for j in s['io_data']:
                        o_data.append(j['output'])
                    print(i_data, o_data)
                    counter = 0
                    kolvo = len(i_data)
                    for i in range(0, len(i_data)):
                        input_data = i_data[i]
                        output_data = o_data[i]
                        sys.stdin = StringIO(input_data)
                        old_stdout = sys.stdout
                        redirected_output = sys.stdout = StringIO()
                        try:
                            exec(answer)
                        except Exception as e:
                            print(e)
                        sys.stdout = old_stdout
                        result = redirected_output.getvalue()
                        user_output.append(result)
                        print(str(result.strip()), str(output_data.strip()))
                        if str(result.strip()) == str(output_data.strip()):
                            counter += 1
                        print(counter)
                        if counter == 0:
                            description = 'Не выполнено.'
                        elif counter != len(i_data) and counter != 0:
                            description = 'Частично пройдено. Результат не засчитан.'
                        elif counter == len(i_data):
                            description = 'Пройдено.'
                            data = {"user": auth, "id": id, "step": step, "code": answer, "input": i_data, "output": o_data}
                            req = requests.post('http://127.0.0.1:5000/api/v1/task/code_task', json=data)
                            if req.status_code == 200:
                                pass
                    text_q = []
                    quest_q = []
                    code_q = []
                    for j in l['lessons']:
                        if j['type'] == 'text':
                            text_q.append(j)
                        if j['type'] == 'question':
                            quest_q.append(j)
                        if j['type'] == 'code':
                            code_q.append(j)
                    return render_template('lesson.html', user=auth, l=l, step=step, counter=counter, kolvo=kolvo, text=text_q, quest=quest_q, code_q=code_q, d=description, code=answer, user_output=user_output)
    return redirect('/student_education')

def get_lessons(id):
    for l in lessons:
        if l['number'] == id:
            text_q = []
            quest_q = []
            code_q = []
            for j in l['lessons']:
                if j['type'] == 'text':
                    text_q.append(j)
                if j['type'] == 'question':
                    quest_q.append(j)
                if j['type'] == 'code':
                    code_q.append(j)
            return l, text_q, quest_q, code_q


if __name__ == '__main__':
    app.run(port=5002, debug=True)