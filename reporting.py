"""Формирование текстового отчёта по результатам анализа."""

from calculations import calculate
from risk_matrix import response


def write_report(path, company, structure_lines, threats, records, description='', matrix=None):
    with open(path, 'w', encoding='utf-8-sig') as file:
        file.write('ОТЧЁТ ПО АНАЛИЗУ РИСКОВ\n\nОПИСАНИЕ МОДЕЛИ ПРЕДПРИЯТИЯ\n')
        file.write((description.rstrip() if description.strip() else 'Не указано.') + '\n')
        file.write('\nСТРУКТУРА\n')
        file.write(company + '\n')
        for line in structure_lines:
            file.write(line + '\n')
        file.write('\nУГРОЗЫ, УЯЗВИМОСТИ И МЕРЫ ЗАЩИТЫ\n')
        for name, item in threats.items():
            loss = 'не указан' if item['loss'] is None else f"{item['loss']} руб."
            vulnerabilities = item['vulnerabilities'] or 'не указаны'
            measures = item['measures'] or 'не указаны'
            file.write(f"{name}; объект: {item['object']}; ущерб: {loss}; "
                       f"уязвимости: {vulnerabilities}; меры: {measures}\n")
        file.write('\nОЦЕНКА РИСКОВ И СРАВНЕНИЕ ВАРИАНТОВ\n')
        if not records:
            file.write('Нет добавленных оценок.\n')
        for i, record in enumerate(records, 1):
            before, after = calculate(record['loss'], record['probability'], record['after_loss'], record['after_probability'])
            file.write(f"\n{i}. {record['threat']}; объект: {record['object']}\n")
            file.write(f"До мер: ущерб {record['loss']:.2f} руб.; вероятность {record['probability']:.2f}%; ожидаемый ущерб {before:.2f} руб.\n")
            file.write(f"Вариант: {record['variant']}; меры: {record['measure']}; стоимость: {record['cost']:.2f} руб.\n")
            file.write(f"После мер: ущерб {record['after_loss']:.2f} руб.; вероятность {record['after_probability']:.2f}%; остаточный риск {after:.2f} руб.; изменение {before-after:.2f} руб.\n")
        file.write('\nРасчёт: ущерб за инцидент × годовая вероятность / 100. Вероятность, последствия после мер и стоимость задаются пользователем. Изменение риска показано до учёта стоимости мер.\n')
        if matrix:
            file.write('\nМАТРИЦА РИСКОВ (БАЛЛЫ P И I)\n')
            for index, point in enumerate(matrix, 1):
                action = response(point['p'], point['i'])
                file.write(f"{index}. {point['threat']}; P: {point['p']}; I: {point['i']}; {action}\n")
