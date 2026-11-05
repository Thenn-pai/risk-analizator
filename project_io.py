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
        if not isinstance(item.get('description', ''), str):
            raise ValueError('Неверное описание объекта.')
        children = item.get('children')
        if level == 0:
            valid_tree(children, 1)
        elif children != []:
            raise ValueError('У объекта не может быть вложенных элементов.')


def valid_threats(threats):
    if not isinstance(threats, dict):
        raise ValueError('Неверный каталог угроз.')
    for name, item in threats.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(item, dict):
            raise ValueError('Неверная запись угрозы.')
        for key in ('object', 'vulnerabilities', 'measures'):
            if not isinstance(item.get(key), str):
                raise ValueError('Неверные данные угрозы.')
        if not item['object'].strip():
            raise ValueError('Не указан объект угрозы.')
        if 'loss' not in item:
            raise ValueError('Не указано поле ущерба.')
        if item.get('loss') is not None:
            item['loss'] = number(str(item['loss']), 'Ущерб')


def save_project_data(path, company, structure, records, description='', threats=None):
    data = {'version': 3 if threats is not None else 2, 'company': company,
            'structure': structure, 'records': records, 'description': description}
    if threats is not None:
        data['threats'] = threats
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
        description = ''
        threats = None
    elif isinstance(data, dict) and data.get('version') in (2, 3):
        records = data.get('records')
        structure = data.get('structure')
        company = data.get('company')
        description = data.get('description', '')
        threats = data.get('threats') if data['version'] == 3 else None
        if not isinstance(company, str) or not company.strip():
            raise ValueError('Не указано название организации.')
        if not isinstance(description, str):
            raise ValueError('Неверное описание предприятия.')
        valid_tree(structure)
        if data['version'] == 3:
            valid_threats(threats)
    else:
        raise ValueError('Неверный формат файла.')

    if not isinstance(records, list):
        raise ValueError('Неверный список оценок.')
    for record in records:
        if not isinstance(record, dict) or not all(isinstance(record.get(k), str) for k in ('object', 'threat', 'variant', 'measure')):
            raise ValueError('В проекте отсутствуют данные записи.')
        for key in ('loss', 'probability', 'after_loss', 'after_probability', 'cost'):
            record[key] = number(str(record[key]), key, 100 if 'probability' in key else None)
    return company, structure, records, description, threats
