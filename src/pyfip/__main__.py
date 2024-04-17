import os
from dataclasses import dataclass
from enum import unique, StrEnum, auto
from importlib import resources
from typing import List

from dynaconf import Dynaconf
from saxonche import PySaxonProcessor, PyXdmValue, PySaxonApiError

from pyfip.fip.preprocessor import Preprocessor

@dataclass
class TestResult:
    success: bool
    score: int

@unique
class Modality(StrEnum):
    ANY = auto()
    ALL = auto()

def get_test_result(result_list: PyXdmValue, modality: Modality, max_tst_score: int) -> TestResult:
    if result_list:
        for item in result_list:
            # print("\t\tSTR_VALUE:", item.string_value)
            # print("\t\tDOUBLE_VALUE:", item.double_value)
            # print("\t\tBLN_VALUE:", item.boolean_value)
            if item.string_value in ["true", "false"]: # TODO: No method to determine the Python native type: You must cast/ask for a type...
                if modality is Modality.ANY:
                    for item in result_list:
                        if item.boolean_value:
                            return TestResult(True, max_tst_score)
                    return TestResult(False, 0)
                elif modality is Modality.ALL:
                    for item in result_list:
                        if not item.boolean_value:
                            return TestResult(False, 0)
                    return TestResult(True, max_tst_score)
            else: # Alternative is a SINGLE number: Value should be between 0 and 1. Calculate the test score accordingly
                return TestResult(True, round(item.double_value * max_tst_score, 1))
    return TestResult(True, 0)


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
    # Make sure to start the solrproxy.py tool to bypass basicAuth.
    settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)
    print("ENV:", settings.DYNACONF_ENV)
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    print(f'Metrics: version: {Preprocessor.get_metrics_version()}; parsed metrics number: {Preprocessor.get_total_metrics()}')

    with PySaxonProcessor(license=False) as proc:
        print("Saxon processor:", proc.version)
        xpproc = proc.new_xquery_processor()

        for k, v in Preprocessor.get_nspace_map().items():
            xpproc.declare_namespace(k, v)
        xpproc.set_cwd(os.getcwd())

        for cmdi in resources.files("tests.resources.cmdi").iterdir():
            print(f'\nFile assessment => {str(cmdi)}')
            xpproc.set_context(file_name=str(cmdi))
            for metric in Preprocessor.get_metrics():
                print(f'=> Using metric: {metric["metric_name"]} ({metric["metric_identifier"]}), modality: {metric["modality"]}, max_metric_score: {metric["max_score"]}')

                for metric_test in metric["metric_tests"]:
                    print(f'\t=> Test: {metric_test["metric_test_name"]}')
                    metric_tst_results: List[TestResult] = [] # Tst results
                    for metric_test_requirement in metric_test["metric_test_requirements"]:
                        if metric_test_requirement["test"].startswith("xpath:"):  # 4: In Xpath handler...
                            # reset results to None
                            result = None
                            xpath_tst = metric_test_requirement["test"].split("xpath:", 1)[1]
                            print(f'\t\t=> Requirement test: {xpath_tst}')
                            print(f'\t\t=> Test requirement modality = {metric_test_requirement["modality"]}')
                            declaration_list = []
                            declarations =''
                            if metric_test_requirement.get("variables", False):
                                for varia in metric_test_requirement.get("variables"):
                                    var_name = varia.split("=", 1)[0]
                                    var_val = varia.split("=", 1)[1]
                                    print(f'\t\t\t=> Var name={var_name}, value={var_val}')
                                    varproc = proc.new_xpath_processor()
                                    if '$RECORDPATH' in var_val: # TODO: RECORDPATH variable must be known by the caller. Find a way to make this generic.
                                        varproc.declare_variable('RECORDPATH')
                                        varproc.set_parameter('RECORDPATH', proc.make_string_value(cmdi.name, encoding="UTF-8"))
                                    json_result = varproc.evaluate(var_val)
                                    xpproc.set_parameter(var_name, json_result)
                                    declaration_list.append(f"declare variable ${var_name} external")
                                declarations = '; '.join(declaration_list)
                                declarations += ";"
                            # print ("\t\tDeclare ext. vars:", declarations)
                            xpproc.set_query_content(f"{declarations} {xpath_tst}")
                            try: # Looks like the parser might still print a java.io.IOException, that cannot be caught: FODC0002  I/O error reported by XML parser processing https://curation.clarin.eu/download/profile/clarin_eu_cr1_p_1650879720846. Caused by java.io.IOException: Server returned HTTP response code: 500 for URL: (...)
                                result = xpproc.run_query_to_value(encoding="UTF-8")
                            except (RuntimeError, BaseException, PySaxonApiError) as error:
                                print("\t\tError executing Xpath test:", xpath_tst)
                            # print("\t\tTEST Result:", result)
                            # print("\t\tTEST Modality:", Modality[metric_test['metric_test_requirements'][0]['modality'].upper()])
                            # print("\t\tTEST Max. SCORE:", metric_test["metric_test_score"])
                            if result: # None result: Do not include this result in the test => TODO: take account for None results in the end/total assessment score. For now just skip them.
                                test_result = get_test_result(result, Modality[metric_test['metric_test_requirements'][0]['modality'].upper()], metric_test["metric_test_score"])
                                metric_tst_results.append(test_result)
                                print ('\t\t', test_result)
                            # if result:
                            #     for i in range(result.size):
                            #         print(result.item_at(i).get_string_value())
            # break

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