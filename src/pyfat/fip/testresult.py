import datetime
import decimal
from dataclasses import dataclass
from enum import unique, StrEnum, auto
from typing import List

@unique
class Modality(StrEnum):
    ANY = auto()
    ALL = auto()

@dataclass
class TestResult:
    success: bool
    score: decimal
    testid: str
    testname: str
    testvalue: str
    log: str
    metricid: str
    gentime: datetime.date



@dataclass
class MetricResult:
    success: bool
    score: decimal
    metricid: str
    metricname: str
    metricdescription: str
    metrictestids: List[str]
    max_score: decimal
    modality: Modality
    testresults: List[TestResult]