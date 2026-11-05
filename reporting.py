"""Формирование отчёта Word или текстового отчёта по результатам анализа."""

from io import BytesIO
from pathlib import Path
from calculations import calculate
from risk_matrix import response


def write_report(path, company, structure_lines, threats, records, description='', matrix=None):
    if Path(path).suffix.lower() == '.txt':
        write_text_report(path, company, structure_lines, threats, records, description, matrix)
    else:
        write_word_report(path, company, structure_lines, threats, records, description, matrix or [])


def write_text_report(path, company, structure_lines, threats, records, description='', matrix=None):
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


def write_word_report(path, company, structure_lines, threats, records, description, matrix):
    # Библиотеки нужны для Word и графиков; саму программу можно открыть без них.
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt
    from charts import make_figures

    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin, section.right_margin = Cm(3), Cm(1.5)
    section.top_margin = section.bottom_margin = Cm(2)
    normal = document.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(14)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)

    def heading(text):
        p = document.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.add_run(text).bold = True

    def paragraph(text):
        p = document.add_paragraph(text)
        p.paragraph_format.first_line_indent = Cm(1.25)
        return p

    def table(title, headers, rows, widths):
        caption = document.add_paragraph(title)
        caption.paragraph_format.keep_with_next = True
        grid = document.add_table(rows=1, cols=len(headers))
        grid.style = 'Table Grid'
        grid.alignment = WD_TABLE_ALIGNMENT.CENTER
        grid.autofit = False
        layout = grid._tbl.tblPr.find(qn('w:tblLayout'))
        if layout is None:
            layout = OxmlElement('w:tblLayout')
            grid._tbl.tblPr.append(layout)
        layout.set(qn('w:type'), 'fixed')
        for column, width in zip(grid.columns, widths):
            column.width = Cm(width)
        header = grid.rows[0]
        repeat = OxmlElement('w:tblHeader')
        repeat.set(qn('w:val'), 'true')
        header._tr.get_or_add_trPr().append(repeat)
        for i, value in enumerate(headers):
            header.cells[i].text = str(value)
        for values in rows:
            cells = grid.add_row().cells
            for i, value in enumerate(values):
                cells[i].text = str(value)
        for row_index, row in enumerate(grid.rows):
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for index, cell in enumerate(row.cells):
                cell.width = Cm(widths[index])
                for p in cell.paragraphs:
                    p.paragraph_format.line_spacing = 1
                    p.paragraph_format.space_after = Pt(0)
                    for run in p.runs:
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(10)
                        if row_index == 0:
                            run.bold = True
        document.add_paragraph()

    def amount(value):
        return f'{value:,.2f}'.replace(',', '\u00a0').replace('.', ',')

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run('ОТЧЁТ ПО АНАЛИЗУ РИСКОВ').bold = True
    paragraph(company)

    heading('1. Описание предприятия')
    paragraph(description.strip() or 'Описание не указано.')
    heading('2. Структура предприятия')
    paragraph(company)
    if structure_lines:
        for line in structure_lines:
            p = document.add_paragraph(line.lstrip())
            p.paragraph_format.left_indent = Cm(min((len(line) - len(line.lstrip())) * 0.25, 2))
    else:
        paragraph('Структура не указана.')

    heading('3. Угрозы, уязвимости и меры защиты')
    threat_rows = []
    for name, item in threats.items():
        loss = 'Не указаны' if item['loss'] is None else amount(item['loss'])
        threat_rows.append([name, item['object'], loss,
                            item['vulnerabilities'] or 'Не указаны', item['measures'] or 'Не указаны'])
    if threat_rows:
        table('Таблица 1 – Каталог угроз',
              ['Угроза', 'Объект', 'Потери, руб.', 'Уязвимости', 'Меры защиты'],
              threat_rows, [3.1, 3.1, 2.3, 3.6, 4.2])
    else:
        paragraph('Угрозы не добавлены.')

    heading('4. Оценка рисков')
    paragraph('Ожидаемый ущерб за год рассчитывается как потери за один инцидент, '
              'умноженные на годовую вероятность и делённые на 100. Расчёт рассматривает '
              'не более одного инцидента за год. Стоимость мер указана отдельно и в '
              'изменение риска не включена. Варианты одной угрозы не суммируются.')
    if records:
        inputs, results = [], []
        for index, item in enumerate(records, 1):
            before, after = calculate(item['loss'], item['probability'],
                                      item['after_loss'], item['after_probability'])
            inputs.append([index, item['threat'] + '\n' + item['variant'], item['object'],
                           amount(item['loss']), amount(item['probability']),
                           amount(item['after_loss']), amount(item['after_probability'])])
            results.append([index, amount(before), amount(after), amount(before - after), amount(item['cost'])])
        table('Таблица 2 – Исходные данные оценок',
              ['№', 'Угроза и вариант', 'Объект', 'Потери до, руб.', 'P до, %',
               'Потери после, руб.', 'P после, %'],
              inputs, [0.9, 3.8, 3.0, 2.3, 1.5, 2.3, 1.5])
        table('Таблица 3 – Результаты расчёта',
              ['№', 'До мер, руб.', 'После мер, руб.', 'Снижение, руб.', 'Стоимость мер, руб.'],
              results, [0.9, 3.3, 3.3, 3.5, 4.5])
        paragraph('Отрицательное значение снижения означает рост ожидаемого ущерба.')
        heading('Меры защиты по оценкам')
        for index, item in enumerate(records, 1):
            paragraph(f"{index}. {item['measure']}")
    else:
        paragraph('Оценки не добавлены.')

    heading('5. Матрица рисков')
    paragraph('Баллы вероятности P и тяжести последствий I от 1 до 5 задаются '
              'пользователем. Граница областей проходит между баллами 2 и 3.')
    if matrix:
        rows = [[i, point['threat'], point['p'], point['i'], response(point['p'], point['i'])]
                for i, point in enumerate(matrix, 1)]
        table('Таблица 4 – Точки матрицы рисков',
              ['№', 'Угроза', 'P', 'I', 'Реагирование'], rows, [0.9, 6.0, 1.0, 1.0, 6.6])
    else:
        paragraph('Точки матрицы не добавлены.')

    heading('6. Диаграммы')
    figures = make_figures(records, matrix)
    if not figures:
        paragraph('Для построения диаграмм добавьте оценку или точку матрицы.')
    else:
        paragraph('Номера на диаграммах соответствуют номерам строк оценок и точек матрицы.')
        for number, (name, figure) in enumerate(figures, 1):
            image = BytesIO()
            figure.savefig(image, format='png', dpi=150, facecolor='white')
            image.seek(0)
            image_p = document.add_paragraph()
            image_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            image_p.paragraph_format.keep_with_next = True
            image_p.add_run().add_picture(image, width=Cm(15.3))
            caption = document.add_paragraph(f'Рисунок {number} – {name}')
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.save(path)
