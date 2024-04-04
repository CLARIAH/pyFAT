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
    # Make sure to start the solrproxy.py tool to bypass basicAuth.
    settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)
    print("ENV:", settings.DYNACONF_ENV)
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    print(f'Metrics: version: {Preprocessor.get_metrics_version()}; parsed metrics number: {Preprocessor.get_total_metrics()}')
    # print(f'Namespaces: {Preprocessor.get_nspace_map()}')


    # xquery_processor = proc.new_xquery_processor()
    # xdm_int_value = proc.make_integer_value(12)
    # # print(xdm_int_value)
    # xquery_processor.set_parameter('n', xdm_int_value)
    #
    # result = xquery_processor.run_query_to_value(query_text='declare variable $n external; (1 to $n)!(. * .)')
    # print(result.size)


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
                    for metric_test_requirement in metric_test["metric_test_requirements"]:
                        if metric_test_requirement["test"].startswith("xpath:"):  # 4: In Xpath handler...
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
                            print ("Declare ext. vars:", declarations)
                            xpproc.set_query_content(f"{declarations} {xpath_tst}")
                            result = xpproc.run_query_to_value(encoding="UTF-8")
                            print("Result:", result)
                            # for i in range(result.size):
                            #     print(result.item_at(i))

            # break


                #         str_eval = f"for-each({test['metric_test_requirements'][0]['values']}, function($value) {{ {test['metric_test_requirements'][0]['test']} }} )"
                #         results = xpproc.evaluate(str_eval)
                #         test_results = get_test_result(results, Modality[test['metric_test_requirements'][0]['modality'].upper()], test["metric_test_score"])
                #         tst_results.append(test_results)
                #         print("\t", f'TestID: {test["metric_test_identifier"]}, {test_results.success}, score earned: {test_results.score}')
                #         # print("\tTEST STATUS:", get_test_result(results, test['metric_test_requirements'][0]['modality'], test["metric_test_score"]))
                # m_results = get_metric_result(tst_results, Modality[metric['modality'].upper()], metric["max_score"])
                # print("\t", m_results)

if __name__ == '__main__':
    main()
