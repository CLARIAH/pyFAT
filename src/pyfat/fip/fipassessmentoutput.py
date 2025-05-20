import os.path
import uuid
from datetime import datetime
from typing import List

from dynaconf import Dynaconf
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

from pyfat import commons
from pyfat.fip.testresult import TestResult, MetricResult


class FipAssessmentOutput:
    """
    A class that implements a FAIR assessment output specification:
    https://ostrails.github.io/FAIR_assessment_output_specification/release/0.0.1/index-en.html
    """

    # settings = Dynaconf(
    #     settings_files=[os.path.join(commons.module_path, "conf/settings.toml")],
    #     secrets=[os.path.join(commons.module_path, "conf/.secrets.toml")],
    #     environments=True,
    #     default_env="default",
    #     load_dotenv=True,
    # )

    settings = commons.setup_env("settings.toml")
    score = None

    def __init__(self, appname: str, version: str, scm: str):
        self.prov = Namespace("http://www.w3.org/ns/prov#")
        self.ftr = Namespace("https://w3id.org/fair_test_result#")
        self.sorg = Namespace("https://schema.org/")
        self.fex = Namespace("http://example.org/fair/")
        self.xsd = Namespace("http://www.w3.org/2001/XMLSchema#")
        self.cln = Namespace("http://www.clarin.eu/ns/rubric#")

        self.g = Graph()
        self._bind_namespaces()

        self._initialize_software(appname, version, scm)

    def _bind_namespaces(self):
        self.g.namespace_manager.bind('prov', self.prov)
        self.g.namespace_manager.bind('ftr', self.ftr)
        self.g.namespace_manager.bind('schema', self.sorg)
        self.g.namespace_manager.bind('fex', self.fex)
        self.g.namespace_manager.bind('xsd', self.xsd)
        self.g.namespace_manager.bind('cln', self.cln)

    def _initialize_software(self, appname: str, version: str, scm: str):
        app_software = self.fex.pyFAT
        self.g.add((app_software, RDF.type, self.sorg.SoftwareApplication))
        self.g.add((app_software, self.sorg.url, Literal(scm)))
        self.g.add((app_software, self.sorg.softwareVersion, Literal(version, datatype=XSD.string)))
        self.g.add((app_software, self.sorg.name, Literal(appname)))

    def add_testresult(self, testresult: TestResult):
        tstresult = self.fex[testresult.testid]
        self._add_testresult_triples(tstresult, testresult)

    def _add_testresult_triples(self, tstresult, testresult):
        self.g.add((tstresult, RDF.type, self.ftr.TestResult))
        self.g.add((tstresult, self.sorg.identifier, Literal(testresult.testid)))
        self.g.add((tstresult, self.sorg.name, Literal(testresult.testname)))
        self.g.add((tstresult, self.ftr.isDefinedBy, URIRef(f"https://pyfat.huc.knaw.nl/api/v1/metric/{testresult.metricid}")))
        self.g.add((tstresult, self.sorg.description, Literal(testresult.testvalue)))
        self.g.add((tstresult, self.ftr.log, Literal(testresult.log)))
        self.g.add((tstresult, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((tstresult, self.prov.generatedAtTime, Literal(testresult.gentime, datatype=XSD.dateTime)))
        self.g.add((tstresult, self.ftr.status, Literal(testresult.success, datatype=XSD.boolean)))
        # TODO: How can one determine TEST completion as a percentage, if a test result can only be True or False or Indeterminate?
        # Until mistery solved, we'll skip this:
        # self.g.add((tstresult, self.ftr.completion, Literal(testresult.score, datatype=XSD.decimal)))

    def set_assessedresource(self, resource: str):
        assessed_resource = self.fex.assessedResource
        self.g.add((assessed_resource, RDF.type, self.prov.Entity))
        self.g.add((assessed_resource, self.sorg.url, Literal(resource)))

    def start_execution_activity(self, agentname: str, agentid: str):
        self._add_agent(agentname, agentid)
        self._add_execution_activity()

    def _add_agent(self, agentname: str, agentid: str):
        agent = self.fex.agent
        self.g.add((agent, RDF.type, self.prov.Agent))
        self.g.add((agent, self.sorg.identifier, Literal(agentid)))
        self.g.add((agent, self.sorg.name, Literal(agentname)))

    def _add_execution_activity(self):
        execution = self.fex.pyFatExecution
        self.g.add((execution, RDF.type, self.ftr.TestExecutionActivity))
        self.g.add((execution, self.prov.used, self.fex.assessedResource))
        self.g.add((execution, self.ftr.usedAPI, Literal("https://pyfat.huc.knaw.nl/api/v1/", datatype=XSD.anyURI)))
        self.g.add((execution, self.prov.wasStartedBy, self.fex.agent))
        self.g.add((execution, self.prov.startedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))

    def create_assessment_rubric(self, metricresults: List[MetricResult], metrics_version: str, metrics_created_by: str):
        self.g.add((self.fex.pyFatExecution, self.prov.endedAtTime, Literal(datetime.now(), datatype=XSD.dateTime)))
        rubricset_uuid = str(uuid.uuid4())
        rubricset = self.cln[rubricset_uuid]
        self._add_rubricset_triples(rubricset, rubricset_uuid, metrics_version, metrics_created_by)
        self._add_completion_status(rubricset, metricresults)
        self._add_metrics_members(rubricset, metricresults)

    def _add_rubricset_triples(self, rubricset, rubricset_uuid: str, metrics_version: str, metrics_created_by: str):
        self.g.add((rubricset, RDF.type, self.cln.AssessmentRubricResultSet))
        self.g.add((rubricset, self.sorg.identifier, Literal(rubricset_uuid)))
        self.g.add((rubricset, self.sorg.license, Literal("https://spdx.org/licenses/WTFPL.html")))
        self.g.add((rubricset, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((rubricset, self.prov.wasGeneratedBy, self.fex.pyFatExecution))
        self.g.add((rubricset, self.prov.used, self.fex.assessedResource))
        self.g.add((rubricset, self.ftr.isDefinedBy, URIRef(f"https://pyfat.huc.knaw.nl/api/v1/metrics/v{metrics_version}")))
        self.g.add((rubricset, self.sorg.name, Literal(metrics_created_by)))

    def _add_completion_status(self, rubricset, metricresults: List[MetricResult]):
        completion = sum(metric.lvl_completion for metric in metricresults) / len(metricresults)
        self.score = completion
        self.g.add((rubricset, self.ftr.completion, Literal(completion, datatype=XSD.decimal)))
        status = "True" if completion >= self.settings.TESTRUBIC_SUCCESS_THRESHOLD else "False"
        self.g.add((rubricset, self.ftr.status, Literal(status, datatype=XSD.boolean)))

    def _add_metrics_members(self, rubricset, metricresults: List[MetricResult]):
        for metric in metricresults:
            self.g.add((rubricset, self.prov.hadMember, self.fex[metric.metricid]))

    def create_testresultset(self, metric_id: str, metric_name: str, completion: float, status: bool):
        testresultset = self.fex[metric_id]
        self._add_testresultset_triples(testresultset, metric_id, metric_name, completion, status)

    def _add_testresultset_triples(self, testresultset, metric_id: str, metric_name: str, completion: float, status: bool):
        self.g.add((testresultset, RDF.type, self.ftr.TestResultSet))
        self.g.add((testresultset, self.sorg.identifier, Literal(metric_id)))
        self.g.add((testresultset, self.sorg.name, Literal(metric_name)))
        self.g.add((testresultset, self.sorg.license, Literal("https://spdx.org/licenses/WTFPL.html")))
        self.g.add((testresultset, self.prov.used, self.fex.assessedResource))
        self.g.add((testresultset, self.prov.wasDerivedFrom, self.fex.assessedResource))
        self.g.add((testresultset, self.prov.wasGeneratedBy, self.fex.pyFatExecution))
        self.g.add((testresultset, self.ftr.completion, Literal(completion, datatype=XSD.decimal)))
        self.g.add((testresultset, self.ftr.status, Literal(status, datatype=XSD.boolean)))

    def add_result_to_set(self, metric_id: str, testid: str):
        self.g.add((self.fex[metric_id], self.prov.hadMember, self.fex[testid]))

    def create_test_results_and_set(self, metricresult: MetricResult):
        self.create_testresultset(metricresult.metricid, metricresult.metricname, metricresult.lvl_completion, metricresult.success)
        for tstresult in metricresult.testresults:
            self.add_testresult(tstresult)
            self.add_result_to_set(metricresult.metricid, tstresult.testid)

    def __repr__(self) -> str:
        return self.g.serialize(format='ttl')

    def ttl(self) -> str:
        return self.g.serialize(format='ttl')
    
    def trix(self) -> str:
        return self.g.serialize(format='trix')