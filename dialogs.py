"""Окна редактирования угроз и описаний."""

import tkinter as tk
from tkinter import messagebox, ttk

import math

from calculations import calculate, number


def insert_template(parent, target, fields):
    previous_grab = parent.grab_current()
    dialog = tk.Toplevel(parent)
    dialog.title('Вставить по шаблону')
    dialog.transient(parent)
    dialog.grab_set()
    frame = ttk.Frame(dialog, padding=10)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Названия полей и текст можно менять. Шаблон добавится в конец описания.').grid(
        row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
    ttk.Label(frame, text='Название поля').grid(row=1, column=0, sticky='w')
    ttk.Label(frame, text='Текст').grid(row=1, column=1, sticky='w')
    rows = []
    for i, (label, value) in enumerate(fields, 2):
        label_entry = ttk.Entry(frame, width=25)
        label_entry.insert(0, label)
        label_entry.grid(row=i, column=0, sticky='ew', padx=(0, 8), pady=3)
        value_entry = ttk.Entry(frame, width=55)
        value_entry.insert(0, value)
        value_entry.grid(row=i, column=1, sticky='ew', pady=3)
        rows.append((label_entry, value_entry))
    frame.columnconfigure(1, weight=1)

    def close():
        dialog.destroy()
        if previous_grab and previous_grab.winfo_exists():
            previous_grab.grab_set()

    def insert():
        lines = []
        for label_entry, value_entry in rows:
            label = label_entry.get().strip()
            value = value_entry.get().strip()
            if label:
                lines.append(label + ': ' + value)
            elif value:
                lines.append(value)
        if lines:
            old = target.get('1.0', 'end-1c')
            target.insert('end-1c', ('\n\n' if old.strip() else '') + '\n'.join(lines))
        close()

    buttons = ttk.Frame(frame)
    buttons.grid(row=len(fields) + 2, column=0, columnspan=2, sticky='w', pady=(10, 0))
    ttk.Button(buttons, text='Вставить', command=insert).pack(side='left', padx=(0, 5))
    ttk.Button(buttons, text='Отмена', command=close).pack(side='left')
    dialog.protocol('WM_DELETE_WINDOW', close)


def edit_object_description(parent, name, description, save):
    dialog = tk.Toplevel(parent)
    dialog.title('Описание объекта')
    dialog.transient(parent)
    dialog.geometry('750x500')
    dialog.grab_set()
    frame = ttk.Frame(dialog, padding=8)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Объект: ' + name).pack(anchor='w')
    buttons = ttk.Frame(frame)
    buttons.pack(fill='x', pady=6)
    text = tk.Text(frame, wrap='word', undo=True)
    scroll = ttk.Scrollbar(frame, orient='vertical', command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    text.pack(fill='both', expand=True)
    text.insert('1.0', description)
    fields = [('Наименование', name), ('Назначение', ''), ('Расположение', ''),
              ('Обрабатываемая информация', ''), ('Доступ', '')]
    ttk.Button(buttons, text='Вставить по шаблону',
               command=lambda: insert_template(dialog, text, fields)).pack(side='left', padx=(0, 5))

    def finish():
        save(text.get('1.0', 'end-1c'))
        dialog.destroy()

    ttk.Button(buttons, text='Сохранить', command=finish).pack(side='left', padx=(0, 5))
    ttk.Button(buttons, text='Отмена', command=dialog.destroy).pack(side='left')


def edit_threat(parent, old_name, old_data, objects, save):
    dialog = tk.Toplevel(parent)
    dialog.title('Угроза и защита')
    dialog.transient(parent)
    dialog.grab_set()
    frame = ttk.Frame(dialog, padding=10)
    frame.pack(fill='both', expand=True)
    data = old_data or {'object': '', 'loss': None, 'vulnerabilities': '', 'measures': ''}
    fields = [('Угроза', old_name or ''), ('Объект', data['object']),
              ('Потери за инцидент, руб.', '' if data['loss'] is None else str(data['loss'])),
              ('Уязвимости (через точку с запятой)', data['vulnerabilities']),
              ('Меры защиты (через точку с запятой)', data['measures'])]
    entries = []
    for i, (label, value) in enumerate(fields):
        ttk.Label(frame, text=label + ':').grid(row=i, column=0, sticky='w', padx=(0, 8), pady=4)
        if i == 1:
            entry = ttk.Combobox(frame, values=objects, width=60)
        else:
            entry = ttk.Entry(frame, width=60)
        entry.insert(0, value)
        entry.grid(row=i, column=1, sticky='ew', pady=4)
        entries.append(entry)
    frame.columnconfigure(1, weight=1)
    ttk.Label(frame, text='Объект можно выбрать из структуры или ввести вручную. Потери можно оставить пустыми.').grid(
        row=5, column=0, columnspan=2, sticky='w', pady=(4, 8))

    def finish():
        name, obj, loss, vulnerabilities, measures = (entry.get().strip() for entry in entries)
        try:
            if not name or not obj:
                raise ValueError('Укажите название угрозы и объект.')
            item = {'object': obj, 'loss': number(loss, 'Потери') if loss else None,
                    'vulnerabilities': vulnerabilities, 'measures': measures}
            save(old_name, name, item)
        except ValueError as error:
            messagebox.showerror('Ошибка ввода', str(error), parent=dialog)
            return
        dialog.destroy()

    buttons = ttk.Frame(frame)
    buttons.grid(row=6, column=0, columnspan=2, sticky='w')
    ttk.Button(buttons, text='Сохранить', command=finish).pack(side='left', padx=(0, 5))
    ttk.Button(buttons, text='Отмена', command=dialog.destroy).pack(side='left')


def edit_record(parent, record, threat_names, save):
    dialog = tk.Toplevel(parent)
    dialog.title('Изменить оценку')
    dialog.transient(parent)
    dialog.grab_set()
    frame = ttk.Frame(dialog, padding=10)
    frame.pack(fill='both', expand=True)
    fields = [('Угроза', 'threat'), ('Объект', 'object'),
              ('Потери за инцидент, руб.', 'loss'), ('Вероятность за год, %', 'probability'),
              ('Вариант мер', 'variant'), ('Меры защиты', 'measure'),
              ('Ущерб после мер, руб.', 'after_loss'),
              ('Вероятность после мер, %', 'after_probability'), ('Стоимость мер, руб.', 'cost')]
    entries = {}
    names = list(threat_names)
    if record['threat'] not in names:
        names.append(record['threat'])
    for index, (label, key) in enumerate(fields):
        ttk.Label(frame, text=label + ':').grid(row=index, column=0, sticky='w', padx=(0, 8), pady=3)
        if key == 'threat':
            entry = ttk.Combobox(frame, values=names, state='readonly', width=55)
            entry.set(record[key])
        else:
            entry = ttk.Entry(frame, width=55)
            entry.insert(0, str(record[key]))
        entry.grid(row=index, column=1, sticky='ew', pady=3)
        entries[key] = entry
    frame.columnconfigure(1, weight=1)

    def finish():
        try:
            item = {key: entries[key].get().strip() for _, key in fields}
            if not all(item[key] for key in ('threat', 'object', 'variant', 'measure')):
                raise ValueError('Укажите угрозу, объект, вариант и меры защиты.')
            for key, label in [('loss', 'Ущерб'), ('probability', 'Вероятность'),
                               ('after_loss', 'Ущерб после мер'),
                               ('after_probability', 'Вероятность после мер'), ('cost', 'Стоимость мер')]:
                item[key] = number(item[key], label, 100 if 'probability' in key else None)
            before, after = calculate(item['loss'], item['probability'],
                                      item['after_loss'], item['after_probability'])
            if not math.isfinite(before) or not math.isfinite(after):
                raise ValueError('Слишком большое значение ущерба.')
            save(item)
        except ValueError as error:
            messagebox.showerror('Ошибка ввода', str(error), parent=dialog)
            return
        dialog.destroy()

    buttons = ttk.Frame(frame)
    buttons.grid(row=len(fields), column=0, columnspan=2, sticky='w', pady=(8, 0))
    ttk.Button(buttons, text='Сохранить', command=finish).pack(side='left', padx=(0, 5))
    ttk.Button(buttons, text='Отмена', command=dialog.destroy).pack(side='left')
