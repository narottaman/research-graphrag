from pydantic import BaseModel, Field
from typing import Literal
class Entity(BaseModel):
    name: str
    kind: Literal["Method", "Dataset", "Model", "Metric", "Task", "Concept"]
class Relation(BaseModel):
    source: str
    target: str
    predicate: Literal["IMPROVES", "USES", "EVALUATES_ON", "OUTPERFORMS", "RELATED_TO"]
    evidence: str
class Extraction(BaseModel):
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
class Paragraph(BaseModel):
    id: str
    section_id: str
    text: str
    page: int = 1
class Section(BaseModel):
    id: str
    title: str
    order: int
class Visual(BaseModel):
    id: str
    section_id: str
    kind: Literal["Figure", "Table"]
    path: str
    caption: str = ""
    page: int = 1
    csv_text: str = ""
class Paper(BaseModel):
    id: str
    title: str
    sha256: str
    source_name: str
    doi: str | None = None
    arxiv_id: str | None = None
    sections: list[Section] = Field(default_factory=list)
    paragraphs: list[Paragraph] = Field(default_factory=list)
    visuals: list[Visual] = Field(default_factory=list)
    references: list[dict] = Field(default_factory=list)
class Evidence(BaseModel):
    id: str
    paper_id: str
    text: str
    page: int = 1
    kind: str = "Paragraph"
    path: str | None = None
    score: float = 0
class Query(BaseModel):
    question: str = Field(min_length=3)
    mode: Literal["auto", "shallow", "deep"] = "auto"
class Answer(BaseModel):
    answer: str
    evidence: list[Evidence]
    mode: str
