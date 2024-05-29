import uuid
from datetime import datetime
from typing import List

import toml
from dynaconf import Dynaconf
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

from pyfat.fip.testresult import TestResult, MetricResult


class FipAssessmentOutput(object):
    """
    A class that implements a FAIR assessment output specification:
    https://ostrails.github.io/FAIR_assessment_output_specification/release/0.0.1/index-en.html
    """
    settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)

    def add_testresult(self, testresult: TestResult):
        # Add result triples
        tstresult = self.fex[testresult.testid]
        self.g.add((tstresult, RDF.type, self.ftr.TestResult))
        self.g.add((tstresult, self.sorg.identifier, Literal(testresult.testid)))
        self.g.add((tstresult, self.sorg.name, Literal(testresult.testname)))
        self.g.add((tstresult, self.ftr.isDefinedBy, URIRef(f"https://pyfat.huc.knaw.nl/api/v1/metric/{testresult.metricid}")))
        self.g.add((tstresult, self.sorg.description, Literal(testresult.testvalue)))
        self.g.add((tstresult, self.ftr.log, Literal(testresult.log)))
        self.g.add((tstresult, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((tstresult, self.prov.generatedAtTime, Literal(testresult.gentime, datatype=XSD.dateTime)))
        self.g.add((tstresult, self.ftr.status, Literal(testresult.success, datatype=XSD.boolean)))
        # Add completion: This smells like FAIR "maturity":
        # "Percentage value of completion of a test result for a given resource. For example, if the test passes, completion is expected to be 1. Otherwise, completion is a value 0..1"
        #TODO: How can you detrmine TEST completion as a percentage, if a test outcome can only be True or False or Indeterminate...
        # Until mistery solved, we'll skip this:
        # self.g.add((tstresult, self.ftr.completion, Literal(testresult.score, datatype=XSD.decimal)))

    def set_assessedresource(self, resource: str):
        assessedResource = self.fex.assessedResource
        self.g.add((assessedResource, RDF.type, self.prov.Entity))
        self.g.add((assessedResource, self.sorg.url, Literal(resource)))

    def start_execution_activity(self, agentname, agentid):
        # Create an agent that is the executor
        self.g.add((self.fex.agent, RDF.type, self.prov.Agent))
        self.g.add((self.fex.agent, self.sorg.identifier, Literal(agentid)))
        self.g.add((self.fex.agent, self.sorg.name, Literal(agentname)))

        pyfatexecution = self.fex.pyFatExecution
        self.g.add((pyfatexecution, RDF.type, self.ftr.TestExecutionActivity))
        self.g.add((pyfatexecution, self.prov.used, self.fex.assessedResource))
        self.g.add((pyfatexecution, self.ftr.usedAPI, Literal("https://pyfat.huc.knaw.nl/api/v1/", datatype=XSD.anyURI)))
        self.g.add((pyfatexecution, self.prov.wasStartedBy, self.fex.agent))
        self.g.add((pyfatexecution, self.prov.startedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))

    # def stop_execution_activity(self, metricresults: List[MetricResult], metrics_version: str, metrics_created_by: str):
    #     self.g.add((self.fex.pyFatExecution, self.prov.endedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))
    #     self.create_assessment_rubric(metricresults, metrics_version, metrics_created_by)

    def create_assessment_rubric(self, metricresults: List[MetricResult], metrics_version: str, metrics_created_by: str):
        # Stop execution time: We're finished
        self.g.add((self.fex.pyFatExecution, self.prov.endedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))

        str_uuid = str(uuid.uuid4())
        rubricset = self.cln[str_uuid]
        self.g.add((rubricset, RDF.type, self.cln.AssessmentRubricResultSet))
        self.g.add((rubricset, self.sorg.identifier, Literal(str_uuid)))
        self.g.add((rubricset, self.sorg.license, Literal("https://spdx.org/licenses/WTFPL.html")))
        self.g.add((rubricset, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((rubricset, self.prov.wasGeneratedBy, self.fex.pyFatExecution))
        self.g.add((rubricset, self.prov.used, self.fex.assessedResource))
        self.g.add((rubricset, self.ftr.isDefinedBy, URIRef(f"https://pyfat.huc.knaw.nl/api/v1/metrics/v{metrics_version}")))
        self.g.add((rubricset, self.sorg.name, Literal(metrics_created_by)))

        value_of_completion = 0
        for metric in metricresults:
            self.g.add((rubricset, self.prov.hadMember, self.fex[metric.metricid]))
            if metric.success: # Succes, level of completeness is 1
                value_of_completion = value_of_completion + 1
            else: # Failure: Calculate the level of completeness:
                value_of_completion = value_of_completion + (metric.score / metric.max_score)

        testrubic_completion = value_of_completion/len(metricresults)

        # Add completion: This smells like FAIR "maturity":
        # "Percentage value of completion of a test result for a given resource. For example, if the test passes, completion is expected to be 1. Otherwise, completion is a value 0..1"
        self.g.add((rubricset, self.ftr.completion, Literal(testrubic_completion, datatype=XSD.decimal)))

        # TODO: Agree on Pass or Fail the AssessmentRubricResultSet
        # For now we'll use the percentage of completion and check this to a given threshold:
        self.g.add((rubricset, self.ftr.status, Literal("True" if testrubic_completion >= self.settings.TESTRUBIC_SUCCESS_THRESHOLD else "False", datatype=XSD.boolean)))

    def create_testresultset(self, metric_id, metric_name, completion, bln_status):
        testresultset = self.fex[metric_id]
        self.g.add((testresultset, RDF.type, self.ftr.TestResultSet))
        self.g.add((testresultset, self.sorg.identifier, Literal(metric_id)))
        self.g.add((testresultset, self.sorg.name, Literal(metric_name)))
        self.g.add((testresultset, self.sorg.license, Literal("https://spdx.org/licenses/WTFPL.html")))
        self.g.add((testresultset, self.prov.used, self.fex.assessedResource))
        self.g.add((testresultset, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((testresultset, self.prov.wasGeneratedBy, self.fex.pyFatExecution))
        self.g.add((testresultset, self.ftr.completion, Literal(completion, datatype=XSD.decimal)))
        self.g.add((testresultset, self.ftr.status, Literal(bln_status, datatype=XSD.boolean)))

    def add_result_to_set(self, metric_id, testid):
        self.g.add((self.fex[metric_id], self.prov.hadMember, self.fex[testid]))

    def __init__(self, appname: str, version: str, scm: str):
        # Define namespaces
        self.prov = Namespace("http://www.w3.org/ns/prov#")
        self.ftr = Namespace("https://w3id.org/fair_test_result#")
        self.sorg = Namespace("https://schema.org/")
        self.fex = Namespace("http://example.org/fair/")
        self.xsd = Namespace("http://www.w3.org/2001/XMLSchema#")
        self.cln = Namespace("http://www.clarin.eu/ns/rubric#")

        # Create the graph
        self.g = Graph()

        # Explicitly name our prefixes:
        self.g.namespace_manager.bind('prov', self.prov)
        self.g.namespace_manager.bind('ftr', self.ftr)
        self.g.namespace_manager.bind('schema', self.sorg)
        self.g.namespace_manager.bind('fex', self.fex)
        self.g.namespace_manager.bind('xsd', self.xsd)
        self.g.namespace_manager.bind('cln', self.cln)

        app_software = self.fex.pyFAT

        self.g.add((app_software, RDF.type, self.sorg.SoftwareApplication))
        self.g.add((app_software, self.sorg.url, Literal(scm)))
        self.g.add((app_software, self.sorg.softwareVersion, Literal(version, datatype=XSD.string)))  # , datatype=XSD.string outputs: sorg:softwareVersion "0.1.1"^^xsd:string ;
        self.g.add((app_software, self.sorg.name, Literal(appname)))

    def __repr__(self) -> str:
        return self.g.serialize(format='ttl')

    def create_test_results_and_set(self, metricresult: MetricResult):  # TODO: Check metric score and pass/fail for each TestResultSet
        # Add the testResult nodes to the KG:
        self.create_testresultset(metricresult.metricid, metricresult.metricname, metricresult.score/metricresult.max_score, metricresult.success)
        for tstresult in metricresult.testresults:
            self.add_testresult(tstresult)
            self.add_result_to_set(metricresult.metricid, tstresult.testid)

def main():
    pyproject_toml = toml.load(str("../../../pyproject.toml"))
    rdf_test_result = FipAssessmentOutput(pyproject_toml['tool']['poetry']['name'], pyproject_toml['tool']['poetry']['version'], pyproject_toml['project']['urls']['Repository'])
    print(rdf_test_result)


if __name__ == '__main__':
    main()
