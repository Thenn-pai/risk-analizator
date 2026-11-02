"""Формирование текстового отчёта по результатам анализа."""

from calculations import calculate


def write_report(path, company, structure_lines, threats, records):
    with open(path, 'w', encoding='utf-8-sig') as file:
        file.write('ОТЧЁТ ПО АНАЛИЗУ РИСКОВ\n\nСТРУКТУРА\n')
        file.write(company + '\n')
        for line in structure_lines:
            file.write(line + '\n')
        file.write('\nУГРОЗЫ И МЕРЫ ЗАЩИТЫ\n')
        for name, (obj, loss, protection) in threats.items():
            file.write(f'{name}; объект: {obj}; ущерб: {loss} руб.; меры: {protection}\n')
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
