"""Basic cleanup kept inside the experiment, independent of application code.

The split_names and optional_int rules match the original import script.
"""

import pandas as pd


def clean_plot(value: str) -> str:
    return " ".join(value.split())


def split_names(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [name.strip() for name in value.split(",") if name.strip()]


def optional_int(value: object) -> int | None:
    if pd.isna(value):
        return None
    result = int(value)
    return result if result > 0 else None
