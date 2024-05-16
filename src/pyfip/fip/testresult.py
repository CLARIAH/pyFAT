import decimal
from dataclasses import dataclass


@dataclass
class TestResult:
    success: bool
    score: decimal
    testid: str
    testname: str
    testvalue: str
    log: str