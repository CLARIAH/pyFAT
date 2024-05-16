import decimal
from dataclasses import dataclass
from typing import List


@dataclass
class TestResult:
    success: bool
    score: decimal
    testid: str
    testname: str
    testvalue: str
    log: str


@dataclass
class MetricResult:
    success: bool
    score: decimal
    metricid: str
    metricname: str
    metricdescription: str
    metrictestids: List[str]