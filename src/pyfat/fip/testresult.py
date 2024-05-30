import datetime
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
    score: float
    testid: str
    testname: str
    testvalue: str
    log: str
    metricid: str
    gentime: datetime.date


@dataclass
class MetricResult:
    success: bool
    score: float
    metricid: str
    metricname: str
    metricdescription: str
    metrictestids: List[str]
    max_score: float
    modality: Modality
    testresults: List[TestResult]
    lvl_completion: float
