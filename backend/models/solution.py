from pydantic import BaseModel, constr
from enum import Enum


class Language(str, Enum):
    CPP = "cpp"
    PYTHON = "python"


class Solution(BaseModel):
    problem_id: str
    language: Language
    file_name: constr(pattern=r".*\.(py|cpp)$")
