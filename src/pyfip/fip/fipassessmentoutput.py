from datetime import datetime

import toml
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

from pyfip.fip.testresult import TestResult


class FipAssessmentOutput(object):
    """
    A class that implements a FAIR assessment output specification:
    https://ostrails.github.io/FAIR_assessment_output_specification/release/0.0.1/index-en.html
    """

    def add_testresult(self, testresult: TestResult):
        # Add result triples
        result = self.fex[testresult.testid]
        self.g.add((result, RDF.type, self.ftr.TestResult))
        self.g.add((result, self.sorg.identifier, Literal(testresult.testid)))
        self.g.add((result, self.sorg.name, Literal(testresult.testname)))
        self.g.add((result, self.ftr.isDefinedBy, URIRef("http://example.org/foops/test/2")))
        self.g.add((result, self.sorg.description, Literal(testresult.testvalue)))
        self.g.add((result, self.ftr.log, Literal(testresult.log)))
        self.g.add((result, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((result, self.prov.generatedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))
        self.g.add((result, self.ftr.status, Literal(testresult.success, datatype=XSD.boolean)))
        # Add completion: This smells like FAIR "maturity":
        # "Percentage value of completion of a test result for a given resource. For example, if the test passes, completion is expected to be 1. Otherwise, completion is a value 0..1"
        self.g.add((result, self.ftr.completion, Literal(testresult.score, datatype=XSD.decimal)))

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
        self.g.add((pyfatexecution, self.ftr.usedAPI, Literal("https://pyfat.huc.knaw.nl/assessOntology/", datatype=XSD.anyURI)))
        self.g.add((pyfatexecution, self.prov.wasStartedBy, self.fex.agent))
        self.g.add((pyfatexecution, self.prov.startedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))

    def stop_execution_activity(self):
        self.g.add((self.fex.pyFatExecution, self.prov.endedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))

    def create_testresultset(self, metric_id, metric_name):
        resultset = self.fex[metric_id]
        self.g.add((resultset, RDF.type, self.ftr.TestResultSet))
        self.g.add((resultset, self.sorg.identifier, Literal(metric_id)))
        self.g.add((resultset, self.sorg.name, Literal(metric_name)))
        self.g.add((resultset, self.sorg.license, Literal("https://spdx.org/licenses/WTFPL.html")))
        self.g.add((resultset, self.prov.used, self.fex.assessedResource))
        self.g.add((resultset, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((resultset, self.prov.wasGeneratedBy, self.fex.pyFatExecution))

    def add_result_to_set(self, metric_id, testresult):
        self.g.add((self.fex[metric_id], self.prov.hadMember, self.fex[testresult.testid]))

    def __init__(self, appname: str, version: str, scm: str):
        # Define namespaces
        self.prov = Namespace("http://www.w3.org/ns/prov#")
        self.ftr = Namespace("https://w3id.org/fair_test_result#")
        self.sorg = Namespace("https://schema.org/")
        self.fex = Namespace("http://example.org/fair/")
        self.xsd = Namespace("http://www.w3.org/2001/XMLSchema#")

        # Create the graph
        self.g = Graph()

        # Explicitly name our prefixes:
        self.g.namespace_manager.bind('prov', self.prov)
        self.g.namespace_manager.bind('ftr', self.ftr)
        self.g.namespace_manager.bind('schema', self.sorg)
        self.g.namespace_manager.bind('fex', self.fex)
        self.g.namespace_manager.bind('xsd', self.xsd)

        app_software = self.fex.pyFAT

        self.g.add((app_software, RDF.type, self.sorg.SoftwareApplication))
        self.g.add((app_software, self.sorg.url, Literal(scm)))
        self.g.add((app_software, self.sorg.softwareVersion, Literal(version)))  # , datatype=XSD.string outputs: sorg:softwareVersion "0.1.1"^^xsd:string ;
        self.g.add((app_software, self.sorg.name, Literal(appname)))

    def __repr__(self) -> str:
        return self.g.serialize(format='ttl')


def main():
    pyproject_toml = toml.load(str("../../../pyproject.toml"))
    rdf_test_result = FipAssessmentOutput(pyproject_toml['tool']['poetry']['name'], pyproject_toml['tool']['poetry']['version'], pyproject_toml['project']['urls']['Repository'])
    print(rdf_test_result)


if __name__ == '__main__':
    main()
