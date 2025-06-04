#here will be excel parsing
from typing import Optional
import pandas as pd

def parse_excel(content_type: Optional[str]="xlsx") -> dict:
    excel_file = pd.read_excel(f"handle.{content_type}")
    return excel_file.head().to_dict()
