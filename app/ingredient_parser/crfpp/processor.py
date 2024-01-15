from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from app.logger import logger

from . import utils
from .pre_processor import normalize_ingredient

CWD = Path(__file__).parent
MODEL_PATH = CWD / "model.crfmodel"


@dataclass()
class CRFConfidence:
    average: float = 0.0
    comment: float = 0.0
    name: str = ""
    unit: str = ""
    qty: float = 0.0


@dataclass()
class CRFIngredient:
    input: str = ""
    name: str = ""
    other: str = ""
    qty: str | float = ""
    comment: str = ""
    unit: str = ""
    confidence: CRFConfidence | None = None

    def __post_init__(self):  # sourcery skip: merge-nested-ifs
        self.confidence = CRFConfidence()

        if self.qty:
            self.qty = convert_to_float(self.qty)

        if self.qty is None or self.qty == "":
            # Check if other contains a fraction
            try:
                if self.other is not None and self.other.find("/") != -1:
                    self.qty = round(float(Fraction(self.other)), 3)
                else:
                    self.qty = 1
            except Exception:
                pass


def convert_to_float(frac_str: str | float):
    if frac_str is None:
        return 1.0

    if isinstance(frac_str, float):
        return frac_str
    if isinstance(frac_str, int):
        return float(frac_str)
    if isinstance(frac_str, str): 
        # some format as 1-1/2 cups water
        frac_str = frac_str.replace("-", " ")

        try:
            return float(sum(Fraction(s) for s in frac_str.split()))
        except ValueError:
            return 1.0


def _exec_crf_test(input_text):
    with tempfile.NamedTemporaryFile(mode="w") as input_file:
        input_file.write(utils.export_data(input_text))
        input_file.flush()
        return subprocess.check_output(["crf_test", "--verbose=1", "--model", MODEL_PATH, input_file.name]).decode(
            "utf-8"
        )


def convert_list_to_crf_model(list_of_ingrdeint_text: list[str]):
    try:
        crf_output = _exec_crf_test([normalize_ingredient(x) for x in list_of_ingrdeint_text])
    except Exception as e:
        logger().exception("failed to run crf_test with error: %s", e)
        return []

    out = []
    for raw, normalized in zip(list_of_ingrdeint_text, utils.import_data(crf_output.split("\n"))):
        if normalized == "":
            continue

        out.append(
            CRFIngredient(
                input=raw,
                name=normalized.get("name", ""),
                other=normalized.get("other", ""),
                qty=normalized.get("qty", ""),
                comment=normalized.get("comment", ""),
                unit=normalized.get("unit", ""),
            )
        )

    return out
