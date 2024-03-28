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

                for test in metric["metric_tests"]: #TODO: Looping over multiple variables,
                    if test['metric_test_requirements'][0]['test'].startswith("xpath:"):
                        str_xpath = test['metric_test_requirements'][0]['test'].split("xpath:", 1)[1]
                        var_name = test['metric_test_requirements'][0]['variable'].split("=", 1)[0]
                        var_value = test['metric_test_requirements'][0]['variable'].split("=", 1)[1]

                        varproc = proc.new_xpath_processor() #TODO: Looping
                        varproc.declare_variable('RECORDPATH') #TODO: Need to find a generic way to get and assign value this variable. Now we know it is there/needed
                        varproc.set_parameter('RECORDPATH', proc.make_string_value("json", encoding="UTF-8")) # must be cmdi.name, now 'json' to prrof concat() works.
                        # json_result = varproc.evaluate("json-to-xml(unparsed-text(concat(f'http://{settings.solr_vlo_usr}:{solr_vlo_pwd}@localhost:8183/solr/vlo-index/select?wt=json&q=_fileName:*',$RECORDPATH)))") #Does NOT work.
                        json_result = varproc.evaluate(var_value)
                        print(f"${var_name} xml: {json_result}")
                        # xpproc.set_parameter('RECORDPATH', proc.make_string_value(cmdi.name, encoding="UTF-8"))
                        xpproc.set_parameter(var_name, json_result)
                        # var_value = var_value.replace("{RECORDPATH}", cmdi.name)
                        xpproc.set_query_content(f"declare variable $facets external; {str_xpath}") #TODO: Add declarations in a loop here, in case of multiple variables.

                        # result = xpproc.run_query_to_string(query_text='declare variable $'+var_facets_name+' external; '+ var_facets_name) # All in one.
                        result = xpproc.run_query_to_value(encoding="UTF-8")

                        print("Result:", result)
                        # print("Result size:", result.size)
                        for i in range(result.size):
                            print(result.item_at(i))
            break


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
