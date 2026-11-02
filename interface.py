"""Окно приложения, вкладки и обработчики кнопок."""

import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from calculations import calculate, number
from project_io import read_project_data, save_project_data
from reporting import write_report


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
    selected = comparison_table.selection()
    if not selected:
        messagebox.showinfo('Удаление', 'Выберите строку в таблице сравнения.')
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


def selected_node():
    selected = structure_tree.selection()
    if not selected:
        messagebox.showinfo('Структура', 'Выберите организацию, подразделение или объект.')
        return None
    return selected[0]


def add_structure_node(kind):
    parent = selected_node()
    if parent is None:
        return
    if kind == 'Подразделение' and structure_tree.parent(parent):
        messagebox.showinfo('Структура', 'Для добавления подразделения выберите организацию.')
        return
    if kind == 'Объект' and (not structure_tree.parent(parent) or structure_tree.parent(parent) != root_node):
        messagebox.showinfo('Структура', 'Для добавления объекта выберите подразделение.')
        return
    name = simpledialog.askstring('Новый элемент', 'Название:', parent=window)
    if name and name.strip():
        structure_tree.insert(parent, 'end', text=name.strip(), values=(kind,), open=True)
        structure_tree.item(parent, open=True)


def rename_node():
    node = selected_node()
    if node is None:
        return
    name = simpledialog.askstring('Изменить название', 'Название:', initialvalue=structure_tree.item(node, 'text'), parent=window)
    if name and name.strip():
        structure_tree.item(node, text=name.strip())


def delete_node():
    node = selected_node()
    if node is None:
        return
    if node == root_node:
        messagebox.showinfo('Структура', 'Организацию удалить нельзя.')
        return
    if messagebox.askyesno('Удаление', 'Удалить выбранный элемент и вложенные объекты?'):
        structure_tree.delete(node)


def use_object():
    node = selected_node()
    if node is None:
        return
    if structure_tree.item(node, 'values')[0] != 'Объект':
        messagebox.showinfo('Структура', 'Выберите объект для анализа.')
        return
    chosen = structure_tree.item(node, 'text')
    obj_var.set(chosen)
    # Готовая сумма из работы № 4 относится только к исходному объекту угрозы.
    if chosen != THREATS[threat.get()][0]:
        loss_var.set('')
        after_loss_var.set('')
    notebook.select(risk_tab)


def export_tree(parent):
    result = []
    for item in structure_tree.get_children(parent):
        result.append({'name': structure_tree.item(item, 'text'),
                       'kind': structure_tree.item(item, 'values')[0],
                       'children': export_tree(item)})
    return result


def import_tree(parent, items):
    for item in items:
        node = structure_tree.insert(parent, 'end', text=item['name'], values=(item['kind'],), open=True)
        import_tree(node, item['children'])


def structure_lines(parent, level=0):
    lines = []
    for item in structure_tree.get_children(parent):
        lines.append('  ' * level + structure_tree.item(item, 'text'))
        lines.extend(structure_lines(item, level + 1))
    return lines


def save_project():
    path = filedialog.asksaveasfilename(title='Сохранить проект', defaultextension='.json', filetypes=[('Проект JSON', '*.json')])
    if not path:
        return
    try:
        save_project_data(path, structure_tree.item(root_node, 'text'), export_tree(root_node), records)
        messagebox.showinfo('Проект', 'Проект сохранён.')
    except OSError as error:
        messagebox.showerror('Ошибка', str(error))


def open_project():
    path = filedialog.askopenfilename(title='Открыть проект', filetypes=[('Проект JSON', '*.json')])
    if not path:
        return
    if records and not messagebox.askyesno('Открыть проект', 'Текущие несохранённые данные будут заменены. Продолжить?'):
        return
    try:
        company, structure, loaded_records = read_project_data(path)
        if structure is not None:
            structure_tree.delete(*structure_tree.get_children(root_node))
            structure_tree.item(root_node, text=company)
            import_tree(root_node, structure)
        records[:] = loaded_records
        refresh()
    except (OSError, ValueError, KeyError, TypeError) as error:
        messagebox.showerror('Ошибка открытия', str(error))


def save_report():
    path = filedialog.asksaveasfilename(title='Сохранить отчёт', defaultextension='.txt', filetypes=[('Текстовый документ', '*.txt')])
    if not path:
        return
    try:
        write_report(path, structure_tree.item(root_node, 'text'), structure_lines(root_node, 1), THREATS, records)
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


def start(threats, initial_structure):
    global THREATS, window, records, notebook, structure_tree, root_node
    global risk_tab, threat, obj_var, loss_var, prob_var, variant_var, measure_var
    global after_loss_var, after_prob_var, cost_var, risk_table, comparison_table
    THREATS = threats
    INITIAL_STRUCTURE = initial_structure
    window = tk.Tk()
    window.title('Анализатор рисков — ПАО «Ростелеком»')
    window.geometry('1150x700')
    window.minsize(850, 600)
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

    structure_bar = ttk.Frame(structure_tab, padding=8)
    structure_bar.pack(fill='x')
    for label, command in [('Добавить подразделение', lambda: add_structure_node('Подразделение')),
                           ('Добавить объект', lambda: add_structure_node('Объект')),
                           ('Переименовать', rename_node), ('Удалить', delete_node),
                           ('Оценить объект', use_object)]:
        ttk.Button(structure_bar, text=label, command=command).pack(side='left', padx=3)
    structure_frame = ttk.Frame(structure_tab, padding=8)
    structure_frame.pack(fill='both', expand=True)
    structure_tree = ttk.Treeview(structure_frame, columns=('kind',))
    structure_tree.heading('#0', text='Организация / подразделение / объект')
    structure_tree.heading('kind', text='Тип')
    structure_tree.column('#0', width=600)
    structure_tree.column('kind', width=160)
    structure_tree.pack(fill='both', expand=True)
    root_node = structure_tree.insert('', 'end', text='ПАО «Ростелеком» — офисное подразделение', values=('Организация',), open=True)
    for department, assets in INITIAL_STRUCTURE:
        parent = structure_tree.insert(root_node, 'end', text=department, values=('Подразделение',), open=False)
        for asset in assets:
            structure_tree.insert(parent, 'end', text=asset, values=('Объект',))
    structure_tree.selection_set(root_node)

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
    fields = [('Угроза', threat), ('Объект', obj_var), ('Потери за инцидент, руб.', loss_var),
              ('Вероятность за год, %', prob_var), ('Вариант мер', variant_var), ('Меры защиты', measure_var),
              ('Ущерб после мер, руб.', after_loss_var), ('Вероятность после мер за год, %', after_prob_var), ('Стоимость мер, руб.', cost_var)]
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
