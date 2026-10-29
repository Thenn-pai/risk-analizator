import json
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

THREATS = {
    'А1 — шифрование файлов': ('Файловый сервер S5', 58000, 'Резервное копирование; антивирусная защита'),
    'А2 — утечка данных': ('Данные абонентов S3–S4', 96000, 'Разграничение доступа; контроль передачи данных'),
    'А3 — подмена записей': ('База данных S4', 244000, 'Разграничение доступа; журналирование'),
    'А4 — остановка серверов': ('Серверы S1–S6', 344000, 'Резервное копирование; контроль действий администраторов'),
}
STRUCTURE = [
    ('Организация', 'ПАО «Ростелеком»'),
    ('Регион', 'г. Санкт-Петербург'),
    ('Локальная среда', 'Офисное подразделение'),
    ('Подсистема', 'Обработка обращений и абонентских данных: S3, S4'),
    ('Подсистема', 'Файловые ресурсы: S5'),
    ('Подсистема', 'Серверная инфраструктура: H1, H2, S1–S6, B1'),
]


def calculate(loss, probability, after_loss, after_probability):
    return loss * probability / 100, after_loss * after_probability / 100


def number(value, name, limit=None):
    try:
        result = float(value.strip().replace(',', '.'))
    except ValueError:
        raise ValueError(f'Введите число в поле «{name}».')
    if not math.isfinite(result) or result < 0 or (limit is not None and result > limit):
        raise ValueError(f'Проверьте поле «{name}»: от 0' + (f' до {limit}.' if limit is not None else '.'))
    return result


def fill_threat(event=None):
    obj, loss, protection = THREATS[threat.get()]
    obj_var.set(obj)
    loss_var.set(str(loss))
    after_loss_var.set(str(loss))
    prob_var.set('')
    after_prob_var.set('')
    measure_var.set(protection)


def add_record():
    try:
        loss = number(loss_var.get(), 'Ущерб')
        probability = number(prob_var.get(), 'Вероятность', 100)
        after_loss = number(after_loss_var.get(), 'Ущерб после мер')
        after_probability = number(after_prob_var.get(), 'Вероятность после мер', 100)
        cost = number(cost_var.get(), 'Стоимость мер')
        if not variant_var.get().strip() or not measure_var.get().strip():
            raise ValueError('Укажите название варианта и меры защиты.')
        before, after = calculate(loss, probability, after_loss, after_probability)
        if not math.isfinite(before) or not math.isfinite(after):
            raise ValueError('Слишком большое значение ущерба.')
        item = {'threat': threat.get(), 'object': obj_var.get(), 'loss': loss,
                'probability': probability, 'variant': variant_var.get().strip(),
                'measure': measure_var.get().strip(), 'after_loss': after_loss,
                'after_probability': after_probability, 'cost': cost}
        records.append(item)
        refresh()
    except ValueError as error:
        messagebox.showerror('Ошибка ввода', str(error))


def refresh():
    for table in (risk_table, comparison_table):
        table.delete(*table.get_children())
    for i, r in enumerate(records):
        before, after = calculate(r['loss'], r['probability'], r['after_loss'], r['after_probability'])
        risk_table.insert('', 'end', iid=str(i), values=(r['object'], r['threat'], r['loss'], r['probability'], f'{before:.2f}'))
        comparison_table.insert('', 'end', iid=str(i), values=(r['threat'], r['variant'], r['measure'], f'{before:.2f}', f'{after:.2f}', f'{before-after:.2f}', r['cost']))


def delete_record():
    selected = risk_table.selection() or comparison_table.selection()
    if not selected:
        messagebox.showinfo('Удаление', 'Выберите строку в таблице рисков или сравнения.')
        return
    for index in sorted((int(i) for i in selected), reverse=True):
        del records[index]
    refresh()


def show_chart():
    if not records:
        messagebox.showinfo('Диаграмма', 'Добавьте хотя бы один вариант.')
        return
    chart = tk.Toplevel(window)
    chart.title('Сравнение риска до и после мер')
    frame = ttk.Frame(chart)
    frame.pack(fill='both', expand=True)
    canvas = tk.Canvas(frame, width=780, height=500, bg='white')
    scroll = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side='left', fill='both', expand=True)
    scroll.pack(side='right', fill='y')
    canvas.configure(scrollregion=(0, 0, 780, max(500, 100 * len(records) + 40)))
    pairs = [calculate(r['loss'], r['probability'], r['after_loss'], r['after_probability']) for r in records]
    maximum = max(max(pair) for pair in pairs) or 1
    for i, (r, pair) in enumerate(zip(records, pairs)):
        y = 25 + i * 100
        canvas.create_text(10, y, anchor='w', text=r['threat'] + ' / ' + r['variant'])
        for j, (value, color, label) in enumerate(zip(pair, ('steelblue', 'seagreen'), ('До', 'После'))):
            top = y + 12 + j * 25
            canvas.create_rectangle(10, top, 10 + 500 * value / maximum, top + 16, fill=color)
            canvas.create_text(525, top + 8, anchor='w', text=f'{label}: {value:.2f} руб.')


def save_project():
    path = filedialog.asksaveasfilename(title='Сохранить проект', defaultextension='.json', filetypes=[('Проект JSON', '*.json')])
    if not path:
        return
    try:
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
        messagebox.showinfo('Проект', 'Проект сохранён.')
    except OSError as error:
        messagebox.showerror('Ошибка', str(error))


def open_project():
    path = filedialog.askopenfilename(title='Открыть проект', filetypes=[('Проект JSON', '*.json')])
    if not path:
        return
    try:
        with open(path, encoding='utf-8') as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError('Неверный формат файла.')
        for r in data:
            if not isinstance(r, dict) or not all(isinstance(r.get(k), str) for k in ('object', 'threat', 'variant', 'measure')):
                raise ValueError('В проекте отсутствуют данные записи.')
            for key in ('loss', 'probability', 'after_loss', 'after_probability', 'cost'):
                r[key] = number(str(r[key]), key, 100 if 'probability' in key else None)
        records[:] = data
        refresh()
    except (OSError, ValueError, KeyError, TypeError) as error:
        messagebox.showerror('Ошибка открытия', str(error))


def save_report():
    path = filedialog.asksaveasfilename(title='Сохранить отчёт', defaultextension='.txt', filetypes=[('Текстовый документ', '*.txt')])
    if not path:
        return
    try:
        with open(path, 'w', encoding='utf-8-sig') as file:
            file.write('ОТЧЁТ ПО АНАЛИЗУ РИСКОВ\nПАО «Ростелеком»\n\nСТРУКТУРА\n')
            for kind, name in STRUCTURE:
                file.write(f'{kind}: {name}\n')
            file.write('\nУГРОЗЫ И МЕРЫ ЗАЩИТЫ\n')
            for name, (obj, loss, protection) in THREATS.items():
                file.write(f'{name}; объект: {obj}; ущерб: {loss} руб.; меры: {protection}\n')
            file.write('\nОЦЕНКА РИСКОВ И СРАВНЕНИЕ ВАРИАНТОВ\n')
            if not records:
                file.write('Нет добавленных оценок.\n')
            for i, r in enumerate(records, 1):
                before, after = calculate(r['loss'], r['probability'], r['after_loss'], r['after_probability'])
                file.write(f"\n{i}. {r['threat']}; объект: {r['object']}\n")
                file.write(f"До мер: ущерб {r['loss']:.2f} руб.; вероятность {r['probability']:.2f}%; ожидаемый ущерб {before:.2f} руб.\n")
                file.write(f"Вариант: {r['variant']}; меры: {r['measure']}; стоимость: {r['cost']:.2f} руб.\n")
                file.write(f"После мер: ущерб {r['after_loss']:.2f} руб.; вероятность {r['after_probability']:.2f}%; остаточный риск {after:.2f} руб.; изменение {before-after:.2f} руб.\n")
            file.write('\nРасчёт: ущерб × вероятность / 100. Оценки вероятности, влияния и стоимости мер задаются пользователем.\n')
        messagebox.showinfo('Отчёт', 'Отчёт сохранён. Его можно открыть в Word.')
    except OSError as error:
        messagebox.showerror('Ошибка', str(error))


def make_table(parent, columns):
    frame = ttk.Frame(parent, padding=8)
    frame.pack(fill='both', expand=True)
    table = ttk.Treeview(frame, columns=list(range(len(columns))), show='headings')
    for i, (name, width) in enumerate(columns):
        table.heading(i, text=name)
        table.column(i, width=width, minwidth=90, stretch=True)
    v = ttk.Scrollbar(frame, orient='vertical', command=table.yview)
    h = ttk.Scrollbar(frame, orient='horizontal', command=table.xview)
    table.configure(yscrollcommand=v.set, xscrollcommand=h.set)
    table.grid(row=0, column=0, sticky='nsew')
    v.grid(row=0, column=1, sticky='ns')
    h.grid(row=1, column=0, sticky='ew')
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return table


window = tk.Tk()
window.title('Анализатор рисков — ПАО «Ростелеком»')
window.geometry('1150x700')
records = []

buttons = ttk.Frame(window, padding=6)
buttons.pack(fill='x')
for label, command in [('Сохранить проект', save_project), ('Открыть проект', open_project), ('Сформировать отчёт', save_report)]:
    ttk.Button(buttons, text=label, command=command).pack(side='left', padx=3)

notebook = ttk.Notebook(window)
notebook.pack(fill='both', expand=True, padx=6, pady=6)
structure_tab = ttk.Frame(notebook)
threat_tab = ttk.Frame(notebook)
risk_tab = ttk.Frame(notebook)
comparison_tab = ttk.Frame(notebook)
for tab, title in [(structure_tab, 'Структура'), (threat_tab, 'Угрозы и защита'), (risk_tab, 'Оценка рисков'), (comparison_tab, 'Сравнение мер')]:
    notebook.add(tab, text=title)

structure_table = make_table(structure_tab, [('Уровень', 180), ('Наименование', 700)])
for row in STRUCTURE:
    structure_table.insert('', 'end', values=row)
threat_table = make_table(threat_tab, [('Угроза', 250), ('Объект', 240), ('Ущерб, руб.', 140), ('Меры защиты', 450)])
for name, (obj, loss, protection) in THREATS.items():
    threat_table.insert('', 'end', values=(name, obj, loss, protection))

threat = tk.StringVar(value=next(iter(THREATS)))
obj_var = tk.StringVar()
loss_var = tk.StringVar()
prob_var = tk.StringVar()
variant_var = tk.StringVar(value='Вариант 1')
measure_var = tk.StringVar()
after_loss_var = tk.StringVar()
after_prob_var = tk.StringVar()
cost_var = tk.StringVar(value='0')
form = ttk.Frame(risk_tab, padding=8)
form.pack(fill='x')
form.columnconfigure(1, weight=1)
fields = [('Угроза', threat), ('Объект', obj_var), ('Ущерб до мер, руб.', loss_var),
          ('Вероятность до мер, %', prob_var), ('Вариант мер', variant_var), ('Меры защиты', measure_var),
          ('Ущерб после мер, руб.', after_loss_var), ('Вероятность после мер, %', after_prob_var), ('Стоимость мер, руб.', cost_var)]
for i, (label, var) in enumerate(fields):
    ttk.Label(form, text=label + ':').grid(row=i, column=0, sticky='w', padx=(0, 8), pady=2)
    if i == 0:
        field = ttk.Combobox(form, textvariable=var, values=list(THREATS), state='readonly')
        field.bind('<<ComboboxSelected>>', fill_threat)
    else:
        field = ttk.Entry(form, textvariable=var)
    field.grid(row=i, column=1, sticky='ew', pady=2)
ttk.Button(form, text='Добавить оценку', command=add_record).grid(row=len(fields), column=1, sticky='w', pady=5)
risk_table = make_table(risk_tab, [('Объект', 180), ('Угроза', 230), ('Ущерб, руб.', 130), ('Вероятность, %', 140), ('Ожидаемый ущерб, руб.', 180)])

bar = ttk.Frame(comparison_tab, padding=6)
bar.pack(fill='x')
ttk.Button(bar, text='Показать диаграмму', command=show_chart).pack(side='left', padx=3)
ttk.Button(bar, text='Удалить выбранную строку', command=delete_record).pack(side='left', padx=3)
comparison_table = make_table(comparison_tab, [('Угроза', 210), ('Вариант', 130), ('Меры', 260), ('До, руб.', 110), ('После, руб.', 110), ('Снижение, руб.', 120), ('Стоимость, руб.', 120)])
fill_threat()
window.mainloop()
