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
