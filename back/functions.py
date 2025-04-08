import sqlite3
import json
import subprocess
from datetime import date


def auth(data):
    try:
        email = data['email']
        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        cursor.execute("SELECT role FROM users WHERE email = ?", (email,))
        role_result = cursor.fetchone()
        if role_result:
            role = role_result[0]
        else:
            return { "http_code": 401, "message": "Неправильный логин или пароль"}
        conn.close()

        if result and data['password'] == result[0]:
            if role == 'Ученик':
                conn = sqlite3.connect('ItPying_users.db')
                cursor = conn.cursor()
                cursor.execute("SELECT role, name, class, raiting, stars, teacher FROM users WHERE email = ?", (email,))
                user_data = cursor.fetchone()
                conn.close()
                if user_data:
                    role, name, class_, raiting, stars, teacher = user_data
                    user_info = {
                        "http_code": 200,
                        "name": name,
                        "role": role,
                        "class": class_,
                        "rating": raiting,
                        "stars": stars,
                        "teacher": teacher
                    }
                    return user_info
            elif role == 'Учитель':
                conn = sqlite3.connect('ItPying_users.db')
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM users WHERE email = ?", (email,))
                teacher_name = cursor.fetchone()[0]
                cursor.execute("SELECT name, stars, class FROM users WHERE teacher = ? AND role = 'Ученик'", (teacher_name,))
                students = cursor.fetchall()
                conn.close()
                student_list = [{"name": student[0], "stars": student[1], "class": student[2]} for student in students]
                user_info = {
                    "http_code": 200,
                    "name": teacher_name,
                    "role": role,
                    "students": student_list
                }
                return user_info
        else:
            return { "http_code": 401, "message": "Неправильный логин или пароль"}
    except Exception as e:
        error_data = {
            "http_code": 404,
            "message": f"Произошла критическая ошибка",
            "details": str(e)
        }
        return error_data


def star_add(data):
    try:
        email = data['email']
        stars_n = data['stars']
        task_num = data['task_num']

        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET stars = stars + ? WHERE email = ?", (stars_n, email))
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_id = cursor.fetchone()[0]
        today = date.today()
        cursor.execute("INSERT INTO tests_status (student_id, id_task, result, date) VALUES (?, ?, ?, ?)", (user_id, task_num, '1/1', today.strftime("%d.%m.%Y")))
        cursor.execute("SELECT id_test FROM tests_status WHERE student_id = ? ORDER BY id_test DESC LIMIT 1", (user_id,))
        test_num = cursor.fetchone()[0]
        cursor.execute("SELECT id_test FROM student_tasks WHERE id_student = ? AND id_task = ?", (user_id, task_num))

        if not cursor.fetchone():
            cursor.execute("INSERT INTO student_tasks (id_student, id_test, id_task, best_result) VALUES (?, ?, ?, ?)", (user_id, test_num, task_num, "1/1"))
        else:
            cursor.execute("SELECT id_test FROM student_tasks WHERE id_student = ? AND id_task = ?", (user_id, task_num))
            last_test = cursor.fetchone()[0]
            now_test = f"{last_test}/{test_num}"
            cursor.execute("UPDATE student_tasks SET id_test =  ? WHERE id_student = ? AND id_task = ?", (now_test, user_id, task_num))
        conn.commit()
        conn.close()

        return {"http_code": 200, "message": "Задание успешно добавлено."}

    except Exception as e:
        error_data = {
            "http_code": 404,
            "message": f"Произошла критическая ошибка",
            "details": str(e)
        }
        return error_data


def add_user(data):
    try:
        name = data['name']
        email = data['email']
        password = data['password']
        role = data['role']
        clas = data['class']
        teacher = data['teacher']

        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password, role, class, stars, raiting, teacher) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (name, email, password, role, clas, 0, 0, teacher))
        conn.commit()
        conn.close()

        return {"http_code": 200, "message": "Пользователь успешно добавлен."}

    except Exception as e:
        if str(e).startswith("UNIQUE constraint failed: users.email"):
            return {"http_code": 400, "message": "Пользователь с таким email уже существует."}
        error_data = {
            "http_code": 404,
            "message": f"Произошла критическая ошибка",
            "details": str(e)
        }
        return error_data

def check_stars_class(data):
    try:
        clas = data['class']
        teacher = data['teacher']

        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, stars FROM users WHERE class = ? AND teacher = ?", (clas, teacher))
        result = cursor.fetchall()
        conn.close()

        if result:
            user_info = {
                "http_code": 200,
                "students": [{"name": name, "stars": stars} for name, stars in result]
            }
            return user_info

    except Exception as e:
        error_data = {
            "http_code": 404,
            "message": f"Произошла критическая ошибка",
            "details": str(e)
        }
        return error_data

def binary_to_python(data):
    binary_code = data.get("code", "")
    byte_chunks = [binary_code[i:i + 8] for i in range(0, len(binary_code), 8)]
    ascii_string = ''.join([chr(int(b, 2)) for b in byte_chunks])

    return ascii_string

def run_task(comp_data, python_code):
    try:
        with open("tasks.json", 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        task_num = comp_data['task_num']
        task = next((task for task in tasks_data['tasks'] if task['num'] == task_num), None)
        email = comp_data['email']
        star_n = comp_data['stars']
        io_tests = task['io_data']
        passed_tests = 0
        failed_tests = 0
        passed_test_numbers = []

        for i, test in enumerate(io_tests):
            input_data = test['input']
            expected_output = test['output'].strip()
            result = subprocess.run(
                ['python', python_code],
                input=input_data,
                text=True,
                capture_output=True
            )
            actual_output = result.stdout.strip()
            if actual_output == expected_output:
                passed_tests += 1
                passed_test_numbers.append(i + 1)
            else:
                failed_tests += 1

        res = f"{passed_tests}/{passed_tests + failed_tests}"
        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_id = cursor.fetchone()[0]
        today = date.today()
        cursor.execute("INSERT INTO tests_status (student_id, id_task, result, date, bin_code) VALUES (?, ?, ?, ?, ?)", (user_id, task_num, res, today.strftime("%d.%m.%Y"), comp_data['code']))
        cursor.execute("SELECT id_test FROM tests_status WHERE student_id = ? ORDER BY id_test DESC LIMIT 1", (user_id,))
        test_num = cursor.fetchone()[0]
        cursor.execute("SELECT id_test FROM student_tasks WHERE id_student = ? AND id_task = ?", (user_id, task_num))

        if not cursor.fetchone():
            cursor.execute("INSERT INTO student_tasks (id_student, id_test, id_task, best_result) VALUES (?, ?, ?, ?)", (user_id, test_num, task_num, res))
        else:
            cursor.execute("SELECT id_test FROM student_tasks WHERE id_student = ? AND id_task = ?", (user_id, task_num))
            last_test = cursor.fetchone()
            last_test_num = ""
            for i in range(len(last_test)):
                last_test_num += last_test[i]
            now_test = f"{last_test_num}/{test_num}"
            cursor.execute("SELECT best_result FROM student_tasks WHERE id_student = ? AND id_task = ?", (user_id, task_num))
            max_result = cursor.fetchone()[0]
            al = max_result.split('/')[0]
            an = res.split('/')[0]
            if int(an) > int(al):
                cursor.execute("UPDATE student_tasks SET id_test =  ?, best_result = ? WHERE id_student = ? AND id_task = ?", (now_test, res, user_id, task_num))
            else:
                cursor.execute("UPDATE student_tasks SET id_test =  ? WHERE id_student = ? AND id_task = ?", (now_test, user_id, task_num))

        if passed_tests == passed_tests + failed_tests:
            cursor.execute("UPDATE users SET stars = stars + ? WHERE email = ?", (star_n, email))
        conn.commit()
        conn.close()

        result_data = {
            "http_code": 200,
            "correct": passed_tests,
            "total": passed_tests + failed_tests,
            "passed_tests_numbers": passed_test_numbers
        }
        return result_data

    except Exception as e:
        error_data = {
            "http_code": 404,
            "message": f"Произошла критическая ошибка",
            "details": str(e)
        }
        return error_data

def check_tasks_user(data):
    try:
        email = data['email']

        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT id_test, id_task, best_result FROM student_tasks WHERE id_student = ?", (user_id,))
        tests = cursor.fetchall()
        conn.close()
        test_data = []
        for test in tests:
            result_data = {
                "http_code": 200,
                "id_test": test[0].split('/'),
                "id_task": test[1],
                "best_result": test[2]
            }
            test_data.append(result_data)
        return test_data

    except Exception as e:
        error_data = {
            "http_code": 404,
            "message": f"Произошла критическая ошибка",
            "details": str(e)
        }
        return error_data

def check_test(data):
    try:
        id_test = data['id_test']
        id_task = data['id_task']
        email = data['email']

        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT result, date, bin_code FROM tests_status WHERE id_task = ? AND id_test = ? AND student_id = ?", (id_task, id_test, user_id))
        result = cursor.fetchone()
        conn.close()
        result_data = {
            "http_code": 200,
            "result": result[0],
            "date": result[1],
            "bin_code": result[2]
        }
        return result_data

    except Exception as e:
        error_data = {
            "http_code": 404,
            "message": f"Произошла критическая ошибка",
            "details": str(e)
        }
        return error_data

def code_task(data):
    run_task(data,binary_to_python(data))