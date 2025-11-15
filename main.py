from kalk.calculations import compute_for_variant
from kalk.docx_tools import render_docx_with_images, replace_variables_in_docx
from kalk.constants import TEMPLATE, TMP_DOCX, FINAL_DOCX
import argparse
from pathlib import Path

def generate_report(variant_num:int, template:Path=TEMPLATE, tmp_docx:Path=TMP_DOCX, final_docx:Path=FINAL_DOCX):
    """Функция высокого уровня, которую удобно вызывать из GUI — она возвращает (final_docx_path, changed_flag)."""
    data = compute_for_variant(variant_num)
    context = data['context']
    xml_replacements = data['xml_replacements']
    img1 = data['img1']
    img2 = data['img2']

    # рендерим временный docx (вставляем картинки)
    render_docx_with_images(template, tmp_docx, context, img1, img2)

    # заменяем переменные в формулах
    changed = replace_variables_in_docx(tmp_docx, final_docx, xml_replacements)
    return final_docx, changed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генерация отчёта по варианту")
    parser.add_argument('-n','--num', type=int, required=True, help="Номер варианта (1..29)")
    parser.add_argument('-o','--out', type=str, default=str(FINAL_DOCX), help="Итоговый файл docx")
    args = parser.parse_args()
    final, changed = generate_report(args.num)
    print("Готово:", final, "Изменения:", changed)
