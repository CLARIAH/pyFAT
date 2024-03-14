import os
from dataclasses import dataclass
from enum import unique, StrEnum, auto
from importlib import resources
from typing import List

from dynaconf import Dynaconf
from saxonche import PySaxonProcessor, PyXdmValue

from pyfip.fip.preprocessor import Preprocessor


@dataclass
class TestResult:
    success: bool
    score: int


@unique
class Modality(StrEnum):
    ANY = auto()
    ALL = auto()


def get_test_result(bool_list: PyXdmValue, modality: Modality, score: int) -> TestResult:
    if modality is Modality.ANY:
        for item in bool_list:
            if item.boolean_value:
                return TestResult(True, score)
        return TestResult(False, 0)
    elif modality is Modality.ALL:
        for item in bool_list:
            if not item.boolean_value:
                return TestResult(False, 0)
        return TestResult(True, score)
    else:
        return TestResult(False, 0)


def get_metric_result(tst_results: List[TestResult], modality: Modality, max_score: int) -> TestResult:

    blnSuccess = False
    score = 0

    if modality is Modality.ANY:
        for test in tst_results:
            if test.success: # Any, so metric passed here, however, we need the highest score from all to return.
                blnSuccess = True
                score = test.score if test.score > score else score
        return TestResult(blnSuccess, score if score<= max_score else max_score) #TODO: evaluate metric max_score v.s test with highest score.

    elif modality is Modality.ALL:
        for test in tst_results:
            if not test.success:
                return TestResult(False, 0)
        return TestResult(True, max_score) #TODO: Returns metric max_score, not max_test_score...
    else:
        return TestResult(False, 0)


def main():
    settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)
    print("ENV:", settings.DYNACONF_ENV)
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    print(f'Metrics: version: {Preprocessor.get_metrics_version()}; parsed metrics number: {Preprocessor.get_total_metrics()}')
    # print(f'Namespaces: {Preprocessor.get_nspace_map()}')

    with PySaxonProcessor(license=False) as proc:
        print("Saxon processor:", proc.version)
        xpproc = proc.new_xpath_processor()

        for k, v in Preprocessor.get_nspace_map().items():
            xpproc.declare_namespace(k, v)
        xpproc.set_cwd(os.getcwd())

        for cmdi in resources.files("tests.resources.cmdi").iterdir():
            print(f'FILE: {cmdi.name} ###')
            xpproc.set_context(file_name=str(cmdi))
            for metric in Preprocessor.get_metrics():
                print("\t", f'=> METRIC: {metric["metric_name"]} ({metric["metric_identifier"]}), modality: {metric["modality"]}, max_metric_score: {metric["max_score"]}')
                # test_results
                tst_results: List[TestResult] = []
                for test in metric["metric_tests"]:
                    str_eval = f"for-each({test['metric_test_requirements'][0]['values']}, function($value) {{ {test['metric_test_requirements'][0]['x-function']} }} )"
                    results = xpproc.evaluate(str_eval)
                    test_results = get_test_result(results, Modality[test['metric_test_requirements'][0]['modality'].upper()], test["metric_test_score"])
                    tst_results.append(test_results)
                    print("\t", f'TestID: {test["metric_test_identifier"]}, {test_results.success}, score earned: {test_results.score}')
                    # print("\tTEST STATUS:", get_test_result(results, test['metric_test_requirements'][0]['modality'], test["metric_test_score"]))
                m_results = get_metric_result(tst_results, Modality[metric['modality'].upper()], metric["max_score"])
                print("\t", m_results)

if __name__ == '__main__':
    main()
