import json

users = [
    {
        "name": "Иван Иванов",
        "email": "ivan@ivanov.ru",
        "password": '123',
        "role": 'Ученик',
        'class': '10Т',
        'rating': 5,
        'stars': 10,
        'solved': [],
        'teacher': 'Моргуненко Е.Ю'
    },
    {
        "name": "Олег",
        "email": "oleg@mail.ru",
        'class': '7Т',
        "password": '321',
        "role": 'Ученик',
        'rating': 4,
        'stars': 3,
        'solved': [],
        'teacher': 'Моргуненко Е.Ю'
    },
    {
        "name": "Моргуненко Е.Ю",
        "email": "m@eu.ru",
        "password": '12345',
        "role": 'Учитель',
        'solved': [],
        'rating': 4,
        'stars': 3,
    }
]


try:
    with open('data/users.json', 'r') as file:
        users = json.loads(file.read())
except:
    pass


def save_data():
    with open('data/users.json', 'w') as file:
        file.write(json.dumps(users, ensure_ascii=False))