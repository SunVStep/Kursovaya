from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from zipfile import ZipFile
from lxml import etree
from pathlib import Path
import tempfile, shutil, re
from .constants import NS

def render_docx_with_images(template_path: Path, tmp_docx: Path, context: dict, img1_path: Path, img2_path: Path):
    """Создаёт TMP DOCX — подставляет картинки как InlineImage (гарантируем, что docxtpl доступен)."""
    doc = DocxTemplate(str(template_path))
    # вставляем InlineImage прямо в контекст
    if img1_path is not None and img1_path.exists():
        context['graph_1'] = InlineImage(doc, str(img1_path), width=Mm(160))
    if img2_path is not None and img2_path.exists():
        context['graph_2'] = InlineImage(doc, str(img2_path), width=Mm(160))
    doc.render(context)
    doc.save(str(tmp_docx))
    return tmp_docx

def replace_variables_in_math_nodes(root, replacements: dict) -> bool:
    changed = False
    math_nodes = root.xpath('.//m:oMath | .//m:oMathPara', namespaces=NS)
    for math in math_nodes:
        text_nodes = math.xpath('.//m:t', namespaces=NS)
        for t_node in text_nodes:
            text = t_node.text or ''
            tokens = re.findall(r'\w+|[^\w\s]', text)
            new_tokens = []
            for tok in tokens:
                if tok in replacements:
                    new_tokens.append(f" {replacements[tok]} ")
                else:
                    new_tokens.append(tok)
            new_text = ''.join(new_tokens)
            if new_text != text:
                t_node.text = new_text
                changed = True
    return changed

def replace_variables_in_docx(src_docx: Path, dst_docx: Path, replacements: dict) -> bool:
    any_changed = False
    with tempfile.TemporaryDirectory() as td:
        tmp_zip = Path(td) / "tmp.docx"
        shutil.copy(src_docx, tmp_zip)
        with ZipFile(tmp_zip, 'r') as zin, ZipFile(dst_docx, 'w') as zout:
            targets = [name for name in zin.namelist() if name.startswith('word/') and name.endswith('.xml')]
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in targets:
                    try:
                        root = etree.fromstring(data)
                        changed = replace_variables_in_math_nodes(root, replacements)
                        if changed:
                            any_changed = True
                            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")
                    except Exception:
                        # если парсинг не удался — просто перепишем оригинал
                        pass
                zout.writestr(item, data)
    return any_changed
