import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

THREATS = {
    'А1 — шифрование файлов': ('Файловый сервер S5', 58000, 'Резервное копирование; антивирусная защита'),
    'А2 — утечка данных': ('Данные абонентов S3–S4', 96000, 'Разграничение доступа; контроль передачи данных'),
    'А3 — подмена записей': ('База данных S4', 244000, 'Разграничение доступа; журналирование'),
    'А4 — остановка серверов': ('Серверы S1–S6', 344000, 'Резервное копирование; контроль действий администраторов'),
}


def choose_threat(event=None):
    obj, loss, protection = THREATS[threat.get()]
    object_value.set(obj)
    loss_value.set(str(loss))
    protection_value.set(protection)


def add_record():
    try:
        loss = float(loss_value.get().replace(',', '.'))
        probability = float(probability_value.get().replace(',', '.'))
        if not 0 <= probability <= 100 or not 0 <= loss < float('inf'):
            raise ValueError
    except ValueError:
        messagebox.showerror('Ошибка', 'Введите ущерб не меньше 0 и вероятность от 0 до 100%.')
        return
    expected = loss * probability / 100
    table.insert('', 'end', values=(object_value.get(), threat.get(), loss_value.get(), probability_value.get(), f'{expected:.2f}', protection_value.get()))


def show_chart():
    items = table.get_children()
    if not items:
        messagebox.showinfo('Диаграмма', 'Сначала добавьте угрозы в таблицу.')
        return
    values = [table.item(item, 'values') for item in items]
    chart_window = tk.Toplevel(window)
    chart_window.title('Ожидаемый ущерб по угрозам')
    canvas = tk.Canvas(chart_window, width=800, height=max(220, 75 * len(values) + 60), background='white')
    canvas.pack(fill='both', expand=True)
    maximum = max(float(row[4]) for row in values) or 1
    for i, row in enumerate(values):
        y = 30 + i * 75
        value = float(row[4])
        canvas.create_text(10, y, text=row[1], anchor='w')
        canvas.create_rectangle(10, y + 15, 10 + 550 * value / maximum, y + 35, fill='steelblue')
        canvas.create_text(570, y + 25, text=f'{value:.2f} руб.', anchor='w')


def delete_record():
    for item in table.selection():
        table.delete(item)


def save_report():
    if not table.get_children():
        messagebox.showinfo('Отчёт', 'Сначала добавьте хотя бы одну угрозу.')
        return
    path = filedialog.asksaveasfilename(title='Сохранить отчёт', defaultextension='.csv', filetypes=[('Таблица CSV', '*.csv')])
    if not path:
        return
    try:
        with open(path, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['Объект', 'Угроза', 'Ущерб, руб.', 'Вероятность, %', 'Ожидаемый ущерб, руб.', 'Меры защиты'])
            for item in table.get_children():
                writer.writerow(table.item(item, 'values'))
        messagebox.showinfo('Отчёт', 'Отчёт сохранён.')
    except OSError as error:
        messagebox.showerror('Ошибка сохранения', str(error))


window = tk.Tk()
window.title('Анализатор рисков — Ростелеком')
window.geometry('1100x570')

form = ttk.Frame(window, padding=10)
form.pack(fill='x')
form.columnconfigure(1, weight=1)
threat = tk.StringVar(value=next(iter(THREATS)))
object_value = tk.StringVar()
loss_value = tk.StringVar()
probability_value = tk.StringVar()
protection_value = tk.StringVar()

for row, (title, value) in enumerate([
    ('Угроза:', threat), ('Объект:', object_value), ('Ущерб, руб.:', loss_value),
    ('Вероятность, %:', probability_value), ('Меры защиты:', protection_value)
]):
    ttk.Label(form, text=title).grid(row=row, column=0, sticky='w', padx=(0, 10), pady=4)
    if row == 0:
        field = ttk.Combobox(form, textvariable=value, values=list(THREATS), state='readonly')
        field.bind('<<ComboboxSelected>>', choose_threat)
    else:
        field = ttk.Entry(form, textvariable=value)
    field.grid(row=row, column=1, sticky='ew', pady=4)

buttons = ttk.Frame(window, padding=(10, 0, 10, 5))
buttons.pack(fill='x')
ttk.Button(buttons, text='Добавить в таблицу', command=add_record).pack(side='left', padx=(0, 5))
ttk.Button(buttons, text='Показать диаграмму', command=show_chart).pack(side='left', padx=5)
ttk.Button(buttons, text='Удалить выбранное', command=delete_record).pack(side='left', padx=5)
ttk.Button(buttons, text='Сохранить отчёт', command=save_report).pack(side='left', padx=5)

frame = ttk.Frame(window, padding=10)
frame.pack(fill='both', expand=True)
columns = ('object', 'threat', 'loss', 'probability', 'risk', 'protection')
table = ttk.Treeview(frame, columns=columns, show='headings')
for column, title, width in zip(columns, ['Объект', 'Угроза', 'Ущерб, руб.', 'Вероятность, %', 'Ожидаемый ущерб, руб.', 'Меры защиты'], [150, 200, 90, 110, 145, 270]):
    table.heading(column, text=title)
    table.column(column, width=width, minwidth=70)
scroll = ttk.Scrollbar(frame, orient='vertical', command=table.yview)
table.configure(yscrollcommand=scroll.set)
table.pack(side='left', fill='both', expand=True)
scroll.pack(side='right', fill='y')
choose_threat()
window.mainloop()
