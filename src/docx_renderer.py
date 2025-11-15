from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from .config import TEMPLATE, TMP_DOCX, IMG

def render_doc(context):
    doc = DocxTemplate(TEMPLATE)
    graph_image = InlineImage(doc, str(IMG), width=Mm(160))
    context['graph_1'] = graph_image
    doc.render(context)
    doc.save(TMP_DOCX)
    return TMP_DOCX
