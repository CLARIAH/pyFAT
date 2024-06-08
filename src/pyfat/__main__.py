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


def evaluate(cmdi_record_path: str, record: dict | str) -> FipAssessmentOutput:  # Make sure to start the solrproxy.py tool to bypass basicAuth.
    """
    Evaluate a CMDI record using the FIP metrics.
    The

    :param cmdi_record_path: The path to the CMDI record to evaluate which are harvested by OAI-PMH in daily harvesting.
    :param record: The corresponding record of the cmdi record got from the Solr indexer of VLO
    """

    # Load settings config:
    settings = commons.settings
    logger = setup_logging()

    # Raise error if json record is not dict or str and make sure record is dict.
    if not (isinstance(record, dict) or isinstance(record, str)):
        raise ValueError(f"Expected json record to be a dict or a str, but got {type(record)}")
    if isinstance(record, str):
        record = json.loads(record, encoding="UTF-8")

    # Process/parse Metrics definition
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    logger.debug(f"ENV: {settings.DYNACONF_ENV}")
    logger.debug(f'Metrics v{Preprocessor.get_metrics_version()}; number of metrics: {Preprocessor.get_total_metrics()}')

    pyproject_toml = toml.load(settings.PYPROJECT_TOML_PATH)

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
                    if metric_test_requirement["test"].startswith("xpath:"):  # In Xpath handler... TODO: implement logic for different handlers here (i.e: xpath, Python, etc. Factory)

                        xslt_result = None  # reset results...
                        log = f'Test modality = {metric_test_requirement["modality"]}'
                        xpath_tst = metric_test_requirement["test"].split("xpath:", 1)[1]
                        logger.debug(f'\t\t=> Test: {xpath_tst}, modality: {metric_test_requirement["modality"]}')

                        var_declare_list = []
                        var_declare_str = ''
                        if metric_test_requirement.get("variables", False):
                            for varia in metric_test_requirement.get("variables"):
                                var_name = varia.split("=", 1)[0]
                                var_val = varia.split("=", 1)[1]
                                logger.debug(f'\t\t=> Var name={var_name}, value={var_val}')
                                varproc = proc.new_xpath_processor()
                                # TODO: $RECORDPATH parameter must be known by the caller. Find a way to make this generic.
                                var_val = var_val.replace("$RECORDPATH", os.path.basename(cmdi_record_path))
                                # Or create an external parameter for it:
                                # if '$RECORDPATH' in var_val:
                                    # varproc.declare_variable('RECORDPATH')
                                    # varproc.set_parameter('RECORDPATH', proc.make_string_value(os.path.basename(cmdi_record_path), encoding="UTF-8"))
                                for k, v in record.items():
                                    #as literal text: var_val = var_val.replace(f"${k}", v)
                                    print(f"{k} => {v}")
                                    varproc.declare_variable(k)
                                    varproc.set_parameter(k, proc.make_string_value(json.dumps(v), encoding="UTF-8"))
                                try:
                                    json_result = varproc.evaluate(var_val)
                                except (RuntimeError, BaseException, PySaxonApiError) as err:
                                    logger.error(f"\t\tError executing Xpath test: {var_val}: {err}")
                                    exit()
                                xpproc.set_parameter(var_name, json_result)
                                var_declare_list.append(f"declare variable ${var_name} external")
                            var_declare_str = '; '.join(var_declare_list) + ";"
                            # Add declarations to the output Log:
                            if var_declare_str: log = log + ", " + var_declare_str

                        logger.info(f"\t\t=> Setting Xquery content on procc: {var_declare_str} {xpath_tst}")
                        xpproc.set_query_content(f"{var_declare_str} {xpath_tst}")

                        # Run Xpath query
                        try:  # Looks like the parser might still print a java.io.IOException, that cannot be caught: FODC0002  I/O error reported by XML parser processing https://curation.clarin.eu/download/profile/clarin_eu_cr1_p_1650879720846. Caused by java.io.IOException: Server returned HTTP response code: 500 for URL: (...)
                            xslt_result = xpproc.run_query_to_value(encoding="UTF-8")
                        except (RuntimeError, BaseException, PySaxonApiError) as err:
                            logger.error(f"\t\tError executing Xpath test: {xpath_tst}: {err}")
                        if xslt_result:  # Do not include None results in the metric => TODO: take account for None results (i.e: indeterminate) in the end/total assessment score. For now just skip them.Beware:
                            test_result = get_test_result(xslt_result, Modality[metric_test['metric_test_requirements'][0]['modality'].upper()], metric_test["metric_test_score"], metric_test["metric_test_identifier"],
                                                          metric_test["metric_test_name"], metric_test_requirement["test"], log, metric["metric_identifier"])
                            metric_tst_results_list.append(test_result)
                            logger.debug(f'\t\t=> Test Result: {test_result}')
                        else:
                            logger.warning(f"Test identifier '{metric_test['metric_test_identifier']}' did NOT yield results!")

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
