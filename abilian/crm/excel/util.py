""""""

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from six import text_type

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def sanitize(val):
    if not isinstance(val, str):
        return val

    return ILLEGAL_CHARACTERS_RE.sub("", val)
