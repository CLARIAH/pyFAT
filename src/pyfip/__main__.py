import logging
import os
import sys
from enum import unique, StrEnum, auto
from importlib import resources
from typing import List

import toml
from dynaconf import Dynaconf
from saxonche import PySaxonProcessor, PyXdmValue, PySaxonApiError

from pyfip.fip.fipassessmentoutput import FipAssessmentOutput
from pyfip.fip.preprocessor import Preprocessor
from pyfip.fip.testresult import TestResult, MetricResult


@unique
class Modality(StrEnum):
    ANY = auto()
    ALL = auto()


def get_test_result(result_list: PyXdmValue, testmodality: Modality, max_tst_score: int, test_id: str, testname: str, testvalue: str, log: str) -> TestResult:
    if result_list:
        for item in result_list:
            if item.string_value in ["true", "false"]:  # No method to determine the Python native type: You must cast/ask for a type...
                if testmodality is Modality.ANY:
                    for res in result_list:
                        if res.boolean_value:
                            return TestResult(True, max_tst_score, test_id, testname, testvalue, log) # mod = any, result = True: Pass with test score
                    return TestResult(False, 0, test_id, testname, testvalue, log)
                elif testmodality is Modality.ALL:
                    for res in result_list:
                        if not res.boolean_value:
                            return TestResult(False, 0, test_id, testname, testvalue, log) # mod = All, result = False: Fail with 0 score
                    return TestResult(True, max_tst_score, test_id, testname, testvalue, log) # mod = All, result = all True: Pass with test score

            else:  # Alternative is a SINGLE number: Value should be between 0 and 1. Calculate the test score percentage, accordingly. #TODO: Do we allow for a test to return a value? This probably is a measurement or a benchmark result...
                return TestResult(True, round(item.double_value * max_tst_score, 1), test_id, testname, testvalue, log)
    return TestResult(True, 0, test_id, testname, testvalue, log) # Else: Fail with 0 score


def get_metric_result(tst_results: List[TestResult], modality: Modality, max_score: int, metric_id: str, metric_name: str, metric_description: str) -> MetricResult:

    blnSuccess = False
    score = 0

    if modality is Modality.ANY:
        for test in tst_results:
            if test.success:  # Any, so metric has passed, and we need the highest score from all to return, however not higher than the maximum metric score
                blnSuccess = True
                score = test.score if test.score > score else score

        return MetricResult(blnSuccess, score if score <= max_score else max_score, metric_id, metric_name, metric_description, [test.testid for test in tst_results])

    elif modality is Modality.ALL:
        for test in tst_results:
            score = test.score if test.score > score else score
            if not test.success:
                return MetricResult(False, 0, metric_id, metric_name, metric_description, [test.testid for test in tst_results])

        return MetricResult(True, score if score <= max_score else max_score, metric_id, metric_name, metric_description, [test.testid for test in tst_results])
    else: # No modality found...
        return MetricResult(False, 0, metric_id, metric_name, metric_description, [test.testid for test in tst_results])


def main():
    # Make sure to start the solrproxy.py tool to bypass basicAuth.
    # Load settings config:
    settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)

    # Get logging in place:
    logfile_handler = logging.FileHandler(filename=settings.LOG_FILE )
    logfile_handler.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(settings.log_format))
    handlers = [logfile_handler, stdout_handler]
    logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT, handlers=handlers, datefmt=settings.LOG_DATE_FORMAT)
    logger = logging.getLogger('pyfat')

    # Process/parse Metrics definition
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    logger.debug(f"ENV: {settings.DYNACONF_ENV}")
    logger.debug(f'Metrics v{Preprocessor.get_metrics_version()}; number of metrics: {Preprocessor.get_total_metrics()}')

    with PySaxonProcessor(license=False) as proc:
        logger.debug(f"Processor: {proc.version}")
        xpproc = proc.new_xquery_processor()

        # Load our namespaces into the XSLT processor:
        for k, v in Preprocessor.get_nspace_map().items(): # namespaces are difined in a seperate namespaces.json. Could be included in the Metrics file as well
            xpproc.declare_namespace(k, v)
        xpproc.set_cwd(os.getcwd())

        pyproject_toml = toml.load(str("../../pyproject.toml"))

        # Iterate over our test records:
        for cmdi in resources.files("tests.resources.cmdi").iterdir():

            logger.debug(f'CMDI FILE: {str(cmdi)}')
            assessment_output = FipAssessmentOutput(pyproject_toml['tool']['poetry']['name'], pyproject_toml['tool']['poetry']['version'], pyproject_toml['project']['urls']['Repository'])
            assessment_output.set_assessedresource(str(cmdi))
            assessment_output.start_execution_activity("VLO-Harvester", "0000-0002-5228-1970")

            xpproc.set_context(file_name=str(cmdi))
            for metric in Preprocessor.get_metrics():
                bln_metric_hasresult = False
                metric_tst_results_list: List[TestResult] = []  # List of Test results per metric
                logger.debug(f'METRIC: {metric["metric_identifier"]} => {metric["metric_name"]}, modality: {metric["modality"]}, max_metric_score: {metric["max_score"]}')

                for metric_test in metric["metric_tests"]:
                    logger.debug(f'\t=> Test: {metric_test["metric_test_name"]}')
                    for metric_test_requirement in metric_test["metric_test_requirements"]:
                        if metric_test_requirement["test"].startswith("xpath:"):  # 4: In Xpath handler... TODO: implement logic for different handlers (i.e: xpath, Python, etc.)

                            xslt_result = None # reset results...
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
                                    if '$RECORDPATH' in var_val:  # TODO: RECORDPATH variable must be known by the caller. Find a way to make this generic.
                                        varproc.declare_variable('RECORDPATH')
                                        varproc.set_parameter('RECORDPATH', proc.make_string_value(cmdi.name, encoding="UTF-8"))
                                    json_result = varproc.evaluate(var_val)
                                    xpproc.set_parameter(var_name, json_result)
                                    var_declare_list.append(f"declare variable ${var_name} external")
                                var_declare_str = '; '.join(var_declare_list)
                                var_declare_str += ";"
                                # Optional: Add declarations to the output Log:
                                if var_declare_str: log = log + "\n" + var_declare_str

                            logger.debug(f"\t\t=> Setting Xquery content on procc: {var_declare_str} {xpath_tst}")
                            xpproc.set_query_content(f"{var_declare_str} {xpath_tst}")

                            # Run our xpath query
                            try:  # Looks like the parser might still print a java.io.IOException, that cannot be caught: FODC0002  I/O error reported by XML parser processing https://curation.clarin.eu/download/profile/clarin_eu_cr1_p_1650879720846. Caused by java.io.IOException: Server returned HTTP response code: 500 for URL: (...)
                                xslt_result = xpproc.run_query_to_value(encoding="UTF-8")
                            except (RuntimeError, BaseException, PySaxonApiError) as err:
                                logger.error(f"\t\tError executing Xpath test: {xpath_tst}: {err}")
                            # print("\t\tTEST Modality:", Modality[metric_test['metric_test_requirements'][0]['modality'].upper()])
                            # print("\t\tTEST Max. SCORE:", metric_test["metric_test_score"])
                            if xslt_result:  # Do not include None results in the metric => TODO: take account for None results (i.e: indeterminate) in the end/total assessment score. For now just skip them.
                                test_result = get_test_result(xslt_result, Modality[metric_test['metric_test_requirements'][0]['modality'].upper()], metric_test["metric_test_score"], metric_test["metric_test_identifier"], metric_test["metric_test_name"], metric_test_requirement["test"], log)
                                metric_tst_results_list.append(test_result)
                                logger.debug(f'\t\t=> Test Result: {test_result}')

                                # Create only one output ftr:TestResultSet per metric: #TODO: Create output result rdf/turtle after ALL tests have executed. Therefore we need to supply timestamps (start & finish) to the TestResults too.
                                if not bln_metric_hasresult: assessment_output.create_testresultset(metric["metric_identifier"], metric["metric_name"])
                                bln_metric_hasresult = True
                                # Create an output ftr:TestResult node for this test and add it to the ftr:TestResultSet:
                                assessment_output.add_testresult(test_result)
                                assessment_output.add_result_to_set(metric["metric_identifier"], test_result)
                            else:
                                logger.warning(f"Test identifier '{metric_test["metric_test_identifier"]}' did NOT yield results!")

                # Tests execution completed, generate metric results:
                metric_result = get_metric_result(metric_tst_results_list, Modality[metric["modality"].upper()], metric["max_score"], metric["metric_identifier"], metric["metric_name"], metric["metric_description"])
                logger.debug(f'\t=> Metric Result: {metric_result}')

            assessment_output.stop_execution_activity()
            logger.info(assessment_output)

if __name__ == '__main__':
    main()

# processing this test
# 1. split test on : prefix(language) = xpath, suffix (test) = $facets/js:map/js:string[@key='_harvesterRoot']='NDE Partners''
# 2. do we know prefix?
# 3. no, error: unknown language!
# 4. yes: pass on to the xpath handler(test) -> result

# xpath handler(test)
# initialize een XPath executor -> xpt (t voor test)
# 1. for each variable
# a. initialize een XPath executor -> xpv (v voor variable)
# b. split on = prefix (varname) = facets, suffix (expr) =  json-to-xml(unparsed-text(concat('http://vlo.clariah.dev.nl/vlo-index?q=_fileName:*','${RECORDPATH}')))
# c. zet de globale global variabelen (e.g. cmdi.name -> RECORDPATH) xpv.setVariable(RECORDPATH,cmdi.name) TODO: uitzoeken of dat kan in de python XPath lib ==> Wilko: dat kan
# d. varval = xpv.eval(expr) # TODO: moet waarschijnlijk een input hebben ... dat kan gewoon het record zijn of een <null/> document ==> Wilko:
# e. zet de variabele op de test xp xpt.setVariable(varname,varval)
# 2. zet de globale global variabelen (e.g. cmdi.name -> RECORDPATH) xpt.setVariable(RECORDPATH,cmdi.name) #TODO: How to 'interpret'/detect this action from the metrics.yaml? i.o.w: Not every test will need this var
# 3. if values
# a. values = xpt.eval(record.values)
# b. for each value in values
# i. xpt.setVariable('value',value)
# ii. xpt.eval(record,test)
# iii. test results += xpt.eval(record,test) context value
# 4. if not values
# a. xpt.eval(record,test)
# b. test results += xpt.eval(record,test)
# return results
