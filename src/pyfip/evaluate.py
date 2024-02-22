import os
from importlib import resources

from dynaconf import Dynaconf
from saxonche import PySaxonProcessor

from pyfip.fip.preprocessor import Preprocessor


def main():
    settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)
    print("CONF ENV:", settings.DYNACONF_ENV)
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    print(f'Total metrics defined: {Preprocessor.get_total_metrics()}')
    print(f'Metrics version: {Preprocessor.get_metrics_version()}')
    print(f'Namespaces: {Preprocessor.get_nspace_map()}')

    with PySaxonProcessor(license=False) as proc:
        print("Using Saxon processor:", proc.version, "/n")
        xpproc = proc.new_xpath_processor()

        for k, v in Preprocessor.get_nspace_map().items():
            xpproc.declare_namespace(k, v)
        xpproc.set_cwd(os.getcwd())

        for cmdi in resources.files("tests.resources.cmdi").iterdir():
            print(f'### {cmdi.name} ###')
            xpproc.set_context(file_name=str(cmdi))
            for test in Preprocessor.get_metrics():
                # print ("TSTS",test["metric_tests"])
                for tset in test["metric_tests"]:
                    print("TEST ID:", tset["metric_test_identifier"], end=". ")
                    print(tset["metric_test_requirements"][0]["value"])
                    result = xpproc.evaluate(tset["metric_test_requirements"][0]["value"])
                    print("Evaluation:", result)


if __name__ == '__main__':
    main()
