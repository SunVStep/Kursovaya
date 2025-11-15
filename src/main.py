import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from calculations import calculate_all
from intersections import find_intersections
from plotting import plot_with_intersections
from docx_renderer import render_doc
from omml_replace import replace_variables_in_docx
from config import TMP_DOCX, FINAL_DOCX, IMG
from context_builder import build_context


def main():
    # 1. Выполняем все расчеты
    results = calculate_all(variant_num=2)  # Используем вариант 2

    # 2. Строим график
    plot_with_intersections(
        list(range(1, 31)),  # N от 1 до 30
        results['QG_numbers'],
        results['QTN_numbers'],
        results['intersections']
    )
    print(f"График сохранен: {IMG.resolve()}")

    # 3. Формируем контекст для документа
    context = build_context(results)

    # 4. Рендерим документ с графиком
    tmp_doc = render_doc(context)
    print(f"Временный документ сохранен: {tmp_doc.resolve()}")

    # 5. Заменяем переменные в формулах
    changed = replace_variables_in_docx(tmp_doc, FINAL_DOCX, context)
    print("Файл готов. Изменения внесены:", changed)
    print("Сохранено в:", FINAL_DOCX.resolve())


if __name__ == "__main__":
    main()