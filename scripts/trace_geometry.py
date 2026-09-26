"""Observe the pinned parser's accepted rows without changing its decisions.

Only the definitions/configuration before the archive runner are loaded. An AST
observer is inserted when a new transaction has passed duplicate handling. The
original upstream file is never edited; returned rows are checked against CSVs.
"""
import ast
import copy
import os
import sys
from pathlib import Path

import fitz


def load_parser(root):
    source = root / "vendor/house-ptr-scraper/src/stage3_extract.py"
    text = source.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(source))
    end = next(n.end_lineno for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == "parse_pdf_geometry_v8")
    tree.body = [n for n in tree.body if n.lineno <= end]

    class Observe(ast.NodeTransformer):
        def visit_Assign(self, node):
            if any(isinstance(t, ast.Name) and t.id == "core_values" for t in node.targets):
                call = ast.parse("_observe(page, page_number, item, column_boxes)").body[0]
                return [ast.copy_location(call, node), node]
            return node

    tree = ast.fix_missing_locations(Observe().visit(tree))
    os.environ["HOUSE_PTR_ROOT"] = str(root / "data/work")
    os.environ["HOUSE_PTR_START_YEAR"] = "2025"
    os.environ["HOUSE_PTR_END_YEAR"] = "2025"
    sys.path.insert(0, str(source.parent))
    namespace = {"__file__": str(source), "__name__": "geometry_observer"}
    exec(compile(tree, str(source), "exec"), namespace)
    traces = []

    def observe(page, page_number, item, columns):
        bounds = list(item["core_bbox"])
        fields = []
        for name, (x0, x1) in columns.items():
            rect = [x0, bounds[1], x1, bounds[3]]
            fields.append({"name": name, "rect": rect,
                           "before": page.get_text("text", clip=fitz.Rect(rect)),
                           "after": item["core"][name]})
        traces.append({"page": page_number, "width": page.rect.width,
                       "height": page.rect.height, "row_rect": bounds,
                       "physical_rect": list(item["bbox"]), "method": item["method"],
                       "before": item["raw_full_text"], "after": item["full_text"],
                       "fields": fields})

    namespace["_observe"] = observe

    def trace(pdf):
        traces.clear()
        rows, metadata = namespace["parse_pdf_geometry_v8"](pdf)
        assert len(traces) == len(rows), "Observer must align with accepted transactions"
        return rows, metadata, copy.deepcopy(traces)

    return trace
