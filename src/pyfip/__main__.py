from importlib import resources

import idutils
from dynaconf import Dynaconf
from lxml import etree

from pyfip.fip.preprocessor import Preprocessor


def main():
    settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)

    print("CONF ENV:", settings.DYNACONF_ENV)
    preproc = Preprocessor(settings)
    preproc.parse_metrics_yaml()

    print(f'Total metrics defined: {Preprocessor.get_total_metrics()}')
    print(f'Metrics version: {Preprocessor.get_metrics_version()}')

    for cmdi in resources.files("tests.resources.cmdi").iterdir():
        print(f'Processing => {cmdi.name}')

        print(Preprocessor.get_metrics()[0]["metric_identifier"])

        xslt_root = etree.parse(cmdi)
        self_link = xslt_root.xpath('//cmd:Header/cmd:MdSelfLink', namespaces=Preprocessor.get_nspace_map())
        for link in self_link:
            found_schemes = idutils.detect_identifier_schemes(link.text)
            if found_schemes:
                print(link.text, found_schemes)
                if idutils.is_doi(link.text): print("Found DOI")


if __name__ == '__main__':
    main()
