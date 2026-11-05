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


def valid_matrix(matrix):
    if not isinstance(matrix, list):
        raise ValueError('Неверная матрица рисков.')
    for item in matrix:
        if not isinstance(item, dict) or not isinstance(item.get('threat'), str) or not item['threat'].strip():
            raise ValueError('Неверная угроза в матрице.')
        for key in ('p', 'i'):
            if type(item.get(key)) is not int or not 1 <= item[key] <= 5:
                raise ValueError('Балл в матрице должен быть от 1 до 5.')


def valid_draft(draft):
    keys = ('threat', 'object', 'loss', 'probability', 'variant', 'measure',
            'after_loss', 'after_probability', 'cost')
    if not isinstance(draft, dict) or not all(isinstance(draft.get(key), str) for key in keys):
        raise ValueError('Неверные данные формы оценки.')


def save_project_data(path, company, structure, records, description='', threats=None, matrix=None, draft=None):
    version = 4 if matrix is not None or draft is not None else (3 if threats is not None else 2)
    if version == 4 and (threats is None or matrix is None or draft is None):
        raise ValueError('Для сохранения нужны каталог угроз, матрица и данные формы.')
    data = {'version': version, 'company': company,
            'structure': structure, 'records': records, 'description': description}
    if threats is not None:
        data['threats'] = threats
    if version == 4:
        data['matrix'] = matrix
        data['draft'] = draft
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
        matrix = []
        draft = None
    elif isinstance(data, dict) and data.get('version') in (2, 3, 4):
        records = data.get('records')
        structure = data.get('structure')
        company = data.get('company')
        description = data.get('description', '')
        threats = data.get('threats') if data['version'] in (3, 4) else None
        matrix = data.get('matrix') if data['version'] == 4 else []
        draft = data.get('draft') if data['version'] == 4 else None
        if not isinstance(company, str) or not company.strip():
            raise ValueError('Не указано название организации.')
        if not isinstance(description, str):
            raise ValueError('Неверное описание предприятия.')
        valid_tree(structure)
        if data['version'] in (3, 4):
            valid_threats(threats)
        if data['version'] == 4:
            valid_matrix(matrix)
            valid_draft(draft)
            if draft['threat'] and draft['threat'] not in threats:
                raise ValueError('Угроза в форме отсутствует в каталоге.')
    else:
        raise ValueError('Неверный формат файла.')

    if not isinstance(records, list):
        raise ValueError('Неверный список оценок.')
    for record in records:
        if not isinstance(record, dict) or not all(isinstance(record.get(k), str) for k in ('object', 'threat', 'variant', 'measure')):
            raise ValueError('В проекте отсутствуют данные записи.')
        for key in ('loss', 'probability', 'after_loss', 'after_probability', 'cost'):
            record[key] = number(str(record[key]), key, 100 if 'probability' in key else None)
    return company, structure, records, description, threats, matrix, draft
