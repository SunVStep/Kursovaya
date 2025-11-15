from zipfile import ZipFile
from lxml import etree
import tempfile
import shutil
import re
from pathlib import Path
from .config import NS

def replace_variables_in_math_nodes(root, replacements):
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
            targets = [name for name in zin.namelist()
                       if name.startswith('word/') and name.endswith('.xml')]
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in targets:
                    try:
                        root = etree.fromstring(data)
                        changed = replace_variables_in_math_nodes(root, replacements)
                        if changed:
                            any_changed = True
                            data = etree.tostring(root, xml_declaration=True,
                                                  encoding='UTF-8', standalone="yes")
                    except Exception:
                        pass
                zout.writestr(item, data)
    return any_changed
