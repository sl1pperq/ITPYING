from flask import *
from functions import *

app = Flask(__name__)

@app.route('/api/v1/auth', methods=['POST'])
def post_auth():
    return auth(request.json)
@app.route('/api/v1/info/add_student', methods=['POST'])
def post_add_student():
    return add_user(request.json)


@app.route('/api/v1/info/class_stars', methods=['POST'])
def post_class_stars():
    return check_stars_class(request.json)


@app.route('/api/v1/info/users_tasks', methods=['POST'])
def post_users_tasks():
    return check_tasks_user(request.json)


@app.route('/api/v1/task/code_task', methods=['POST'])
def post_code_task():
    return code_task(request.json)


@app.route('/api/v1/task/done_task', methods=['POST'])
def post_done_task():
    return star_add(request.json)


@app.route('/api/v1/task/test_info', methods=['POST'])
def post_test_info():
    return check_test(request.json)

app.run()