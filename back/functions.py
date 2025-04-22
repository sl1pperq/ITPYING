import sqlite3
import json
import subprocess
import tempfile
import os
from datetime import date


def check_all_class(data):
    try:
        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()

        cursor.execute("""SELECT DISTINCT class FROM users WHERE teacher = ? ORDER BY class""", (data['teacher'],))
        unique_classes = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {
            "http_code": 200,
            "classes": unique_classes,
        }
    except Exception as e:
        return {
            "http_code": 404,
            "message": "Произошла критическая ошибка",
            "details": str(e)
        }
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
    

def delete_user(data):
    try:
        email = data.get('email')
        print(email)

        if not email:
            return {"http_code": 400, "message": "Необходимо указать email пользователя."}

        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted_rows == 0:
            return {"http_code": 404, "message": "Пользователь не найден."}
        else:
            return {"http_code": 200, "message": "Пользователь успешно удалён."}

    except Exception as e:
        error_data = {
            "http_code": 404,
            "message": "Произошла ошибка при удалении пользователя",
            "details": str(e)
        }
        return error_data

def check_raiting_class(data):
    try:
        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        
        cursor.execute("""SELECT name, stars FROM users WHERE class = ? AND teacher = ? ORDER BY stars DESC""", (data['class'], data['teacher']))
        students = cursor.fetchall()
        conn.close()

        if not students:
            return {
                "http_code": 404,
                "message": "В этом классе нет учеников"
            }
        raiting = []
        prev_stars = None
        now_position = 0 
        
        for idx, (name, stars) in enumerate(students, start=1):
            if stars != prev_stars:
                now_position = idx
                prev_stars = stars
     
            raiting.append({
                "position": now_position,
                "name": name,
                "stars": stars
            })
            

        return {
            "http_code": 200,
            "raiting": raiting
        }

    except Exception as e:
        return {
            "http_code": 404,
            "message": "Произошла критическая ошибка",
            "details": str(e)
        }



def run_task(comp_data):
    temp_file_path = None
    try:
        binary_code = comp_data["code"]
        byte_chunks = [binary_code[i:i+8] for i in range(0, len(binary_code), 8)]
        try:
            byte_data = bytes([int(b, 2) for b in byte_chunks if b])
            python_code = byte_data.decode('utf-8')
            python_code = python_code.replace('\r\n', '\n').replace('\r', '\n')
            
        except ValueError as e:
            return {
                "http_code": 400,
                "message": "Ошибка преобразования бинарного кода",
                "details": str(e)
            }
        
        with open("tasks.json", 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)

        task = next((t for t in tasks_data['tasks'] if t['num'] == comp_data['task_num']), None)
        if not task:
            return {
                "http_code": 404,
                "message": f"Задача {comp_data['task_num']} не найдена"
            }
        
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.py', delete=False) as temp_file:
            temp_file.write(python_code)
            temp_file_path = temp_file.name
        print(python_code)

        passed_tests = 0
        failed_tests = 0
        passed_test_numbers = []

        for i, test in enumerate(task['io_data'], 1):
            input_data = test['input']
            expected_output = test['output'].strip()

            result = subprocess.run(
                ['python', temp_file_path],
                input=input_data,
                text=True,
                encoding='utf-8',
                capture_output=True,
                timeout=5
            )

            actual_output = result.stdout.strip()
            if actual_output == expected_output:
                passed_tests += 1
                passed_test_numbers.append(i)
            else:
                failed_tests += 1

        conn = sqlite3.connect('ItPying_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (comp_data['email'],))
        user= cursor.fetchone()
        if not user:
            return {
                "http_code": 404,
                "message": "Пользователь не найден"
            }
        user_id = user[0]
        today = date.today()
        test_result = f"{passed_tests}/{passed_tests + failed_tests}"
        cursor.execute("""INSERT INTO tests_status (student_id, id_task, result, date, bin_code) VALUES (?, ?, ?, ?, ?)""", (user_id, comp_data['task_num'], test_result, today.strftime("%d.%m.%Y"), comp_data['code']))
        cursor.execute("""SELECT id_test FROM tests_status WHERE student_id = ? ORDER BY id_test DESC LIMIT 1""", (user_id,))
        test_num = cursor.fetchone()[0]
        cursor.execute("""SELECT id_test FROM student_tasks WHERE id_student = ? AND id_task = ?""", (user_id, comp_data['task_num']))

        if not cursor.fetchone():
            cursor.execute("""INSERT INTO student_tasks (id_student, id_test, id_task, best_result) VALUES (?, ?, ?, ?)""", (user_id, test_num, comp_data['task_num'], test_result))
        else:
            cursor.execute("""SELECT best_result FROM student_tasks WHERE id_student = ? AND id_task = ?""", (user_id, comp_data['task_num']))
            best_result = cursor.fetchone()[0]
            current_best = int(best_result.split('/')[0])
            cursor.execute("SELECT id_test FROM student_tasks WHERE id_student = ? AND id_task = ?", (user_id, comp_data['task_num']))
            last_test = cursor.fetchone()
            last_test_num = ""
            for i in range(len(last_test)):
                last_test_num += last_test[i]
            now_test = f"{last_test_num}/{test_num}"
            
            if passed_tests > current_best:
                cursor.execute("""UPDATE student_tasks SET id_test = ?, best_result = ? WHERE id_student = ? AND id_task = ?""", (now_test, test_result, user_id, comp_data['task_num']))
            else:
                cursor.execute("UPDATE student_tasks SET id_test =  ? WHERE id_student = ? AND id_task = ?", (now_test, user_id, comp_data['task_num']))

        if passed_tests == (passed_tests + failed_tests):
            cursor.execute("UPDATE users SET stars = stars + ? WHERE email = ?", (comp_data['stars'], comp_data['email']))
        conn.commit()
        conn.close()

        return {
            "http_code": 200,
            "correct": passed_tests,
            "total": passed_tests + failed_tests,
            "passed_tests_numbers": passed_test_numbers
        }

    except subprocess.TimeoutExpired:
        return {
            "http_code": 400,
            "message": "Превышено время выполнения программы",
            "details": "Программа выполнялась более 5 секунд"
        }
    except Exception as e:
        return {
            "http_code": 404,
            "message": "Произошла критическая ошибка",
            "details": str(e)
        }
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

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
    