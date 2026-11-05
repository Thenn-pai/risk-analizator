"""Диаграмма вероятности и тяжести последствий по баллам."""


def response(p, impact):
    if impact >= 3:
        return 'Передача рисков' if p >= 3 else 'Планирование контрмер'
    return 'Контроль и управление' if p >= 3 else 'Принятие рисков'


def draw(canvas, points):
    canvas.delete('all')
    width = max(canvas.winfo_width(), 260)
    height = max(canvas.winfo_height(), 230)
    left, right, top, bottom = 55, width - 15, 20, height - 45
    x = lambda value: left + (value - 0.5) * (right - left) / 5
    y = lambda value: bottom - (value - 0.5) * (bottom - top) / 5
    canvas.create_rectangle(left, top, right, bottom)
    for mark in range(1, 6):
        canvas.create_line(x(mark), top, x(mark), bottom, fill='#cccccc')
        canvas.create_line(left, y(mark), right, y(mark), fill='#cccccc')
        canvas.create_text(x(mark), bottom + 14, text=str(mark))
        canvas.create_text(left - 15, y(mark), text=str(mark))
    canvas.create_line(x(2.5), top, x(2.5), bottom, width=2)
    canvas.create_line(left, y(2.5), right, y(2.5), width=2)
    canvas.create_text(left + 6, top + 6, text='Планирование\nконтрмер', anchor='nw')
    canvas.create_text(right - 6, top + 6, text='Передача\nрисков', anchor='ne')
    canvas.create_text(left + 6, bottom - 6, text='Принятие\nрисков', anchor='sw')
    canvas.create_text(right - 6, bottom - 6, text='Контроль и\nуправление', anchor='se')
    canvas.create_text((left + right) / 2, height - 8, text='Вероятность, балл P')
    canvas.create_text(11, (top + bottom) / 2, text='I')
    grouped = {}
    for index, item in enumerate(points, 1):
        grouped.setdefault((item['p'], item['i']), []).append(str(index))
    for (p, impact), labels in grouped.items():
        px, py = x(p), y(impact)
        canvas.create_oval(px - 5, py - 5, px + 5, py + 5, fill='black')
        anchor = ('n' if impact == 5 else 's') + ('e' if p >= 4 else 'w')
        canvas.create_text(px - 8 if p >= 4 else px + 8, py + 8 if impact == 5 else py - 8,
                           text=', '.join(labels), anchor=anchor, width=150)
