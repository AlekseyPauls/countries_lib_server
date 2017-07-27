# -*- coding: utf-8 -*-
import os, shelve, difflib
from flask import Flask, g, jsonify, request


app = Flask(__name__)


def connect_db():
    database = os.path.join(app.root_path, 'database', 'countries_db')
    return shelve.open(database)


def get_db():
    """ Если ещё нет соединения с базой данных, открыть новое - для
    текущего контекста приложения """
    
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


@app.teardown_appcontext
def close_db(error):
    """ Закрывает базу данных по окончанию запроса """

    if hasattr(g, 'db'):
        g.db.close()


@app.route('/', methods=['GET'])
def normalize_country_name():
    """ Нормализация (нахождение корректного) названия страны """

    if request.args.get('posname') == None or request.args.get('dif_acc') == None:
        return jsonify('This is the "countries_lib_server". Please use the "countries_lib_client" to access '
                       'the functionality of this service.')
    countries_db = get_db()
    posname = request.args.get('posname')
    dif_acc = float(request.args.get('dif_acc'))
    if type(posname) is not str or type(dif_acc) is not float or dif_acc <= 0.0 or dif_acc >= 1.0 or posname == "":
        return jsonify('Invalid arguments')
    try:
        posname = str(posname).lower()
        # Очищаем входную строку от знаков препинания, которые не встречаются в названиях стран
        # Данный способ безопаснее, чем регулярные выражения и применение некоторых стандартных функций,
        # всвязи с национальными символами в названиях стран. Если пользователь умудрится использовать
        # иные символы, то он либо опечатался, либо издевается. Опечатки исправляются далее.
        symbols = [',', '.', '/', '!', '?', '<', '>', '[', ']', '|', '(', ')', '+', '=', '_', '*', '&', '%',
                   ';', '№', '~', '@', '#', '$', '{', '}', '-']
        for symb in symbols:
            posname = posname.replace(symb, ' ')
        if posname == "":
            return 'Invalid arguments'


        # Сначала ищем совпадение всей строки и значения с приоритетом '1'
        # Проверка на длину - чтобы исключить варианты, когда совпало только начало или другая часть строки
        posname_tmp = difflib.get_close_matches(posname, countries_db.keys(), n=1, cutoff=dif_acc)
        if posname_tmp != [] and countries_db[posname_tmp[0]][0] == '1' and \
                abs(len(posname) - len(posname_tmp[0])) <= 1:
            return countries_db[posname_tmp[0]][1:]
        # Ищем совпадение всей строки и значения с приоритетом '2'
        posname_tmp = difflib.get_close_matches(posname, countries_db.keys(), n=1, cutoff=dif_acc)
        if posname_tmp != [] and countries_db[posname_tmp[0]][0] == '2' and \
                abs(len(posname) - len(posname_tmp[0])) <= 1:
            return countries_db[posname_tmp[0]][1:]
        # Ищем совпадение всей строки без пробелов и значения с приоритетом '1'
        posname_tmp = posname.replace(' ', '')
        posname_tmp = difflib.get_close_matches(posname_tmp, countries_db.keys(), n=1, cutoff=dif_acc)
        if posname_tmp != [] and countries_db[posname_tmp[0]][0] == '1' and \
                abs(len(posname.replace(' ', '')) - len(posname_tmp[0].replace(' ', ''))) <= 1:
            return countries_db[posname_tmp[0]][1:]
        # Ищем совпадение всей строки без пробелов и значения с приоритетом '2'
        posname_tmp = posname.replace(' ', '')
        posname_tmp = difflib.get_close_matches(posname_tmp, countries_db.keys(), n=1, cutoff=dif_acc)
        if posname_tmp != [] and countries_db[posname_tmp[0]][0] == '2' and \
                abs(len(posname.replace(' ', '')) - len(posname_tmp[0].replace(' ', ''))) <= 1:
            return countries_db[posname_tmp[0]][1:]

        # Делим входную строку на слова, разделитель - пробел
        parts = posname.split(" ")
        for part in parts:
            # Ищем равное по количеству букв совпадение части строки и значения с приоритетом '1'
            part_tmp = difflib.get_close_matches(part, countries_db.keys(), n=1, cutoff=dif_acc)
            if part_tmp != [] and countries_db[part_tmp[0]][0] == '1' and len(part) == len(part_tmp[0]):
                return countries_db[part_tmp[0]][1:]
        for part in parts:
            # Ищем неравное по количеству букв совпадение части строки и значения с приоритетом '1'
            part_tmp = difflib.get_close_matches(part, countries_db.keys(), n=1, cutoff=dif_acc)
            if part_tmp != [] and countries_db[part_tmp[0]][0] == '1':
                return countries_db[part_tmp[0]][1:]
        for part in parts:
            # Ищем равное по количеству букв совпадение части строки и значения с приоритетом '2'
            part_tmp = difflib.get_close_matches(part, countries_db.keys(), n=1, cutoff=dif_acc)
            if part_tmp != [] and countries_db[part_tmp[0]][0] == '2' and len(part) == len(part_tmp[0]):
                return countries_db[part_tmp[0]][1:]
        for part in parts:
            # Ищем неравное по количеству букв совпадение части строки и значения с приоритетом '2'
            part_tmp = difflib.get_close_matches(part, countries_db.keys(), n=1, cutoff=dif_acc)
            if part_tmp != [] and countries_db[part_tmp[0]][0] == '2':
                return countries_db[part_tmp[0]][1:]
        return jsonify('None')
    # На всякий случай перехватывается Exception. Не смотря на то,
    # что ошибка здесь может быть только в отсутствии корректной базы данных
    except Exception:
        return jsonify('DatabaseError')


@app.route('/', methods=['POST'])
def match_or_del_country_name():
    """ Добавление или удаление возможных названий """
    countries_db = get_db()
    key = str(request.form.get('key')).lower()
    value = str(request.form.get('value'))
    priority = int(request.form.get('priority'))
    if type(key) is str and type(value) is str and value != 'DELETE' and \
                    type(priority) is int and (priority == 1 or priority == 2):
        # Если условия выполняются, добавляем запись в б/д
        try:
            countries_db[key.lower()] = str(priority) + value
            return jsonify('Success')
        # На всякий случай перехватывается Exception. Не смотря на то,
        # что ошибка здесь может быть только в отсутствии корректной базы данных
        except Exception:
            return jsonify('DatabaseError')
    elif type(key) is str and value == 'DELETE' and priority == 1:
        try:
            if key.lower() in countries_db.keys():
                del countries_db[key.lower()]
            return jsonify('Success')
        except Exception:
            return jsonify('DatabaseError')
    return jsonify('Invalid arguments')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
