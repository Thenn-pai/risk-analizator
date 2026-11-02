"""Сохранение проекта и проверка загружаемых данных."""

import json

from calculations import number


def valid_tree(items, level=0):
    if not isinstance(items, list) or level > 1:
        raise ValueError('Неверная структура подразделений.')
    for item in items:
        kind = 'Подразделение' if level == 0 else 'Объект'
        if not isinstance(item, dict) or item.get('kind') != kind or not isinstance(item.get('name'), str) or not item['name'].strip():
            raise ValueError('Неверная запись структуры.')
        children = item.get('children')
        if level == 0:
            valid_tree(children, 1)
        elif children != []:
            raise ValueError('У объекта не может быть вложенных элементов.')


def save_project_data(path, company, structure, records):
    data = {'version': 2, 'company': company, 'structure': structure, 'records': records}
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def read_project_data(path):
    with open(path, encoding='utf-8') as file:
        data = json.load(file)

    if isinstance(data, list):
        # В старых проектах сохранялся только список оценок.
        records = data
        structure = None
        company = None
    elif isinstance(data, dict) and data.get('version') == 2:
        records = data.get('records')
        structure = data.get('structure')
        company = data.get('company')
        if not isinstance(company, str) or not company.strip():
            raise ValueError('Не указано название организации.')
        valid_tree(structure)
    else:
        raise ValueError('Неверный формат файла.')

    if not isinstance(records, list):
        raise ValueError('Неверный список оценок.')
    for record in records:
        if not isinstance(record, dict) or not all(isinstance(record.get(k), str) for k in ('object', 'threat', 'variant', 'measure')):
            raise ValueError('В проекте отсутствуют данные записи.')
        for key in ('loss', 'probability', 'after_loss', 'after_probability', 'cost'):
            record[key] = number(str(record[key]), key, 100 if 'probability' in key else None)
    return company, structure, records
