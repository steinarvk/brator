from pydantic import BaseModel

from typing import Optional

class NumericFact(BaseModel):
    question_text: str
    correct_answer_unit: str
    correct_answer: str

class BooleanFact(BaseModel):
    question_text: str
    correct_answer: bool

class Fact(BaseModel):
    key: str
    category: Optional[str]
    numeric: Optional[NumericFact] = None
    boolean: Optional[BooleanFact] = None
    source: Optional[str] = None
    source_link: Optional[str] = None
    fine_print: Optional[str] = None

class FactCategory(BaseModel):
    name: str
    weight: float
