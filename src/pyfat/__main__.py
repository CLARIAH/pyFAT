import json
import os
from datetime import datetime
from importlib import resources
from typing import List

import toml
from saxonche import PySaxonProcessor, PyXdmValue, PySaxonApiError

from pyfat import commons
from pyfat.commons import setup_logging
from pyfat.fip.fipassessmentoutput import FipAssessmentOutput
from pyfat.fip.preprocessor import Preprocessor
from pyfat.fip.testresult import TestResult, MetricResult, Modality


def get_metric_result(tst_results: List[TestResult], modality: Modality, max_score: float, metric_id: str, metric_name: str, metric_description: str) -> MetricResult:
    test_ids = [test.testid for test in tst_results]

    if modality is Modality.ANY:  # Metric passes if any test passes. Score is the highest score of passing tests, capped at max_score.
        score = max((test.score for test in tst_results if test.success), default=0)
        success = score > 0
        return MetricResult(success, min(score, max_score), metric_id, metric_name, metric_description, test_ids, max_score, modality, tst_results, 1 if success else min(score, max_score) / max_score)

    elif modality is Modality.ALL:  # Metric passes only if all tests pass. Score is the sum of all test scores, capped at max_score.
        success = all(test.success for test in tst_results)
        score = sum(test.score for test in tst_results if test.success)
        return MetricResult(success, min(score, max_score), metric_id, metric_name, metric_description, test_ids, max_score, modality, tst_results, 1 if success else min(score, max_score) / max_score)

    else:  # Handle unexpected modality.
        raise ValueError(f"Unexpected modality: {modality}")


def get_test_result(result_list: List[PyXdmValue], testmodality: Modality, max_tst_score: float, test_id: str, testname: str, testvalue: str, log: str, metricid: str) -> TestResult:
    if not result_list:
        return TestResult(False, 0, test_id, testname, testvalue, log, metricid, datetime.now())  # Fail with 0 score

    if all(isinstance(item, PyXdmValue) and item.string_value in ["true", "false"] for item in result_list):
        if testmodality is Modality.ANY:
            success = any(res.boolean_value for res in result_list)
            score = max_tst_score if success else 0
        elif testmodality is Modality.ALL:
            success = all(res.boolean_value for res in result_list)
            score = max_tst_score if success else 0
        else:  # TODO: Do we allow for a test to return a double value? This probably is a measurement or a benchmark result... How to interpret this? OSTrails test output: Pass, Fail or indeterminate.
            item = result_list[0]
            success = 0 <= item.double_value <= 1
            score = round(item.double_value * max_tst_score, 1) if success else 0
    return TestResult(success, score, test_id, testname, testvalue, log, metricid, datetime.now())


def evaluate(cmdi_record_path: str, variables_dict: dict = {}) -> FipAssessmentOutput:  # Make sure to start the solrproxy.py tool to bypass basicAuth.
    """
    Evaluate a CMDI record using the FIP metrics.
    The

    :param cmdi_record_path: The path to the CMDI record to evaluate which are harvested by OAI-PMH in daily harvesting.
    :param variables_dict: The corresponding record of the cmdi record got from the Solr indexer of VLO
    """

    # Load settings config:
    settings = commons.settings
    logger = setup_logging()

    # Process/parse Metrics definition
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    logger.debug(f"ENV: {settings.DYNACONF_ENV}")
    logger.debug(f'Metrics v{Preprocessor.get_metrics_version()}; number of metrics: {Preprocessor.get_total_metrics()}')

    pyproject_toml = toml.load(os.path.join(commons.module_path, settings.PYPROJECT_TOML_PATH))

    with PySaxonProcessor(license=False) as proc:
        logger.debug(f"Processor: {proc.version}")
        xpproc = proc.new_xquery_processor()

        # Load our namespaces into the XSLT processor:
        for k, v in Preprocessor.get_nspace_map().items():
            xpproc.declare_namespace(k, v)

        xpproc.set_cwd(os.getcwd())

        logger.debug(f'CMDI FILE: {str(cmdi_record_path)}, {os.path.basename(cmdi_record_path)}')

        assessment_output = FipAssessmentOutput(pyproject_toml['tool']['poetry']['name'], pyproject_toml['tool']['poetry']['version'], pyproject_toml['project']['urls']['Repository'])
        assessment_output.set_assessedresource(str(cmdi_record_path))
        assessment_output.start_execution_activity(settings.PROV_AGENT_NAME, settings.PROV_AGENT_IDENTIFIER)

        xpproc.set_context(file_name=str(cmdi_record_path))
        metricresults_list: List[MetricResult] = []  # List of MetricResult per assessment
        for metric in Preprocessor.get_metrics():
            metric_tst_results_list: List[TestResult] = []  # List of Test results per metric
            logger.debug(f'METRIC: {metric["metric_identifier"]} => {metric["metric_name"]}, modality: {metric["modality"]}, max_metric_score: {metric["max_score"]}')

            for metric_test in metric["metric_tests"]:
                logger.debug(f'\t=> Test: {metric_test["metric_test_name"]}')
                for metric_test_requirement in metric_test["metric_test_requirements"]:
                     response = requests.post(f'https://localhost:5000/test/{metric_test}', cmdi=cmdi_record_path)

                     metric_tst_results_list.append(test_result)
                     logger.debug(f'\t\t=> Test Result: {test_result}')
                     #   else:
                     #      logger.warning(f"Test identifier '{metric_test['metric_test_identifier']}' did NOT yield results!")

                    # tot hier vervangen ???

            # All tests for this metric have completed: add the result nodes and generate metric TestResultSet node:
            metric_result = get_metric_result(metric_tst_results_list, Modality[metric["modality"].upper()], metric["max_score"], metric["metric_identifier"], metric["metric_name"], metric["metric_description"])
            metricresults_list.append(metric_result)
            assessment_output.create_test_results_and_set(metric_result)
            logger.debug(f'\t=> Metric Result: {metric_result}')
        # All metrics have completed here: generate AssessmentRubricResultSet (total score, metric testsets, etc.):
        assessment_output.create_assessment_rubric(metricresults_list, Preprocessor.get_metrics_version(), Preprocessor.get_metrics_created_by())

        logger.info(assessment_output)
        return assessment_output


def main():
    for cmdi in resources.files("tests.resources.cmdi").iterdir():
        evaluate(cmdi)


if __name__ == '__main__':
    main()
