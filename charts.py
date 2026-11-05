"""Диаграммы по введённым оценкам и баллам матрицы рисков."""

from collections import Counter, defaultdict

from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from calculations import calculate
from risk_matrix import response


def money(value, _position=None):
    return f'{value:,.2f}'.rstrip('0').rstrip('.').replace(',', ' ').replace('.', ',')


def make_figures(records, points):
    """Вернуть названия и рисунки; номера совпадают со строками отчёта."""
    figures = []
    # Небольшие группы не превращают подписи в нечитаемый список.
    for start in range(0, len(records), 8):
        group = records[start:start + 8]
        numbers = [str(i) for i in range(start + 1, start + len(group) + 1)]
        values = [calculate(r['loss'], r['probability'], r['after_loss'],
                            r['after_probability']) for r in group]
        positions = list(range(len(group)))

        height = max(3.0, 1.8 + len(group) * 0.45)
        figure = Figure(figsize=(9, height), layout='tight')
        axis = figure.subplots()
        bars_before = axis.barh([n - 0.2 for n in positions], [v[0] for v in values], 0.4,
                                label='До мер', color='#4779a4')
        bars_after = axis.barh([n + 0.2 for n in positions], [v[1] for v in values], 0.4,
                               label='После мер', color='#4c9165')
        axis.bar_label(bars_before, labels=[money(v[0]) for v in values], padding=3, fontsize=8)
        axis.bar_label(bars_after, labels=[money(v[1]) for v in values], padding=3, fontsize=8)
        axis.margins(x=0.25)
        axis.set_yticks(positions, numbers)
        axis.set_ylim(max(2.2, len(group) - 0.35), -0.65)
        axis.set_xlabel('Ожидаемый ущерб за год, руб.')
        axis.set_ylabel('Номер оценки')
        axis.set_title('Ожидаемый ущерб до и после мер')
        axis.xaxis.set_major_formatter(FuncFormatter(money))
        axis.grid(axis='x', alpha=0.25)
        axis.legend()
        figures.append(('Ожидаемый ущерб до и после мер', figure))

        figure = Figure(figsize=(9, 4.7), layout='tight')
        axis = figure.subplots()
        bars_before = axis.bar([n - 0.2 for n in positions], [v[0] for v in values], 0.4,
                               label='До мер', color='#4779a4')
        bars_after = axis.bar([n + 0.2 for n in positions], [v[1] for v in values], 0.4,
                              label='После мер', color='#4c9165')
        axis.bar_label(bars_before, labels=[money(v[0]) for v in values], padding=3, fontsize=8, rotation=45)
        axis.bar_label(bars_after, labels=[money(v[1]) for v in values], padding=3, fontsize=8, rotation=45)
        axis.margins(y=0.25)
        axis.set_xticks(positions, numbers)
        axis.set_xlabel('Номер оценки')
        axis.set_ylabel('Ожидаемый ущерб за год, руб.')
        axis.set_title('Риск до и после мер')
        axis.yaxis.set_major_formatter(FuncFormatter(money))
        axis.grid(axis='y', alpha=0.25)
        axis.legend()
        figures.append(('Столбчатая диаграмма риска до и после мер', figure))

        figure = Figure(figsize=(9, 4.7), layout='tight')
        axis = figure.subplots()
        for number, (before, after) in zip(numbers, values):
            axis.plot([0, 1], [before, after], marker='o', label=f'Оценка № {number}')
        axis.set_xticks([0, 1], ['До мер', 'После мер'])
        axis.set_ylabel('Ожидаемый ущерб за год, руб.')
        axis.set_title('Риск до и после мер')
        axis.yaxis.set_major_formatter(FuncFormatter(money))
        axis.set_ylim(bottom=0)
        axis.grid(alpha=0.25)
        axis.legend()
        figures.append(('Линейный график риска до и после мер', figure))

        figure = Figure(figsize=(9, height), layout='tight')
        axis = figure.subplots()
        changes = [before - after for before, after in values]
        bars = axis.barh(positions, changes, height=0.55,
                         color=['#4c9165' if value >= 0 else '#bd655d' for value in changes])
        axis.bar_label(bars, labels=[money(value) for value in changes], padding=3, fontsize=8)
        axis.margins(x=0.25)
        axis.axvline(0, color='black', linewidth=0.8)
        axis.set_yticks(positions, numbers)
        axis.set_ylim(max(2.2, len(group) - 0.35), -0.65)
        axis.set_xlabel('Изменение ожидаемого ущерба за год, руб.')
        axis.set_ylabel('Номер оценки')
        axis.set_title('Снижение риска (отрицательное значение — рост)')
        axis.xaxis.set_major_formatter(FuncFormatter(money))
        axis.grid(axis='x', alpha=0.25)
        figures.append(('Изменение ожидаемого ущерба', figure))

        figure = Figure(figsize=(9, 4.7), layout='tight')
        axis = figure.subplots()
        for index, record in enumerate(group, start + 1):
            x = [record['probability'], record['after_probability']]
            y = [record['loss'], record['after_loss']]
            axis.plot(x, y, color='#a0a0a0', linewidth=0.8, zorder=1)
            axis.scatter(x[0], y[0], color='#4779a4', marker='o', zorder=2)
            axis.scatter(x[1], y[1], color='#4c9165', marker='s', zorder=3)
            axis.annotate(str(index), (x[0], y[0]), xytext=(5, 5),
                          textcoords='offset points', fontsize=8)
            if x[0] != x[1] or y[0] != y[1]:
                axis.annotate(str(index), (x[1], y[1]), xytext=(5, 5),
                              textcoords='offset points', fontsize=8)
        axis.scatter([], [], color='#4779a4', marker='o', label='До мер')
        axis.scatter([], [], color='#4c9165', marker='s', label='После мер')
        axis.set_xlim(-3, 103)
        axis.set_ylim(bottom=0)
        axis.set_xlabel('Годовая вероятность, %')
        axis.set_ylabel('Потери за инцидент, руб.')
        axis.yaxis.set_major_formatter(FuncFormatter(money))
        axis.set_title('Вероятность и потери за инцидент')
        axis.grid(alpha=0.25)
        axis.legend()
        figures.append(('Вероятность и потери за инцидент', figure))

    if points:
        figure = Figure(figsize=(9, 5.2), layout='tight')
        axis = figure.subplots()
        axis.set_xlim(0.5, 5.5)
        axis.set_ylim(0.5, 5.5)
        axis.set_xticks(range(1, 6))
        axis.set_yticks(range(1, 6))
        axis.grid(color='#d3d3d3')
        axis.axvline(2.5, color='black', linewidth=1.2)
        axis.axhline(2.5, color='black', linewidth=1.2)
        axis.text(0.6, 5.4, 'Планирование\nконтрмер', va='top', fontsize=8)
        axis.text(5.4, 5.4, 'Передача\nрисков', va='top', ha='right', fontsize=8)
        axis.text(0.6, 0.6, 'Принятие\nрисков', va='bottom', fontsize=8)
        axis.text(5.4, 0.6, 'Контроль и\nуправление', va='bottom', ha='right', fontsize=8)
        groups = defaultdict(list)
        for index, point in enumerate(points, 1):
            groups[(point['p'], point['i'])].append(str(index))
        for (p, impact), indices in groups.items():
            axis.scatter(p, impact, color='black', zorder=3)
            axis.annotate(', '.join(indices), (p, impact),
                          xytext=(-7 if p >= 4 else 7, -8 if impact == 5 else 7),
                          ha='right' if p >= 4 else 'left',
                          va='top' if impact == 5 else 'bottom',
                          textcoords='offset points', fontsize=8)
        axis.set_xlabel('Вероятность, балл P')
        axis.set_ylabel('Тяжесть последствий, балл I')
        axis.set_title('Матрица рисков')
        figures.append(('Матрица рисков по введённым баллам', figure))

        counts = Counter(response(p['p'], p['i']) for p in points)
        figure = Figure(figsize=(9, 4.7), layout='tight')
        axis = figure.subplots()
        wedges, _ = axis.pie(list(counts.values()), startangle=90,
                             colors=['#7fa6c7', '#95b99d', '#e1b77c', '#cd8f88'])
        labels = [f'{name}: {count}' for name, count in counts.items()]
        axis.legend(wedges, labels, title='Число точек', loc='center left',
                    bbox_to_anchor=(1, 0.5))
        axis.set_title('Распределение точек матрицы по областям')
        figures.append(('Распределение точек матрицы', figure))
    return figures
