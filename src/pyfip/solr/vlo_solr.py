import json

import emoji
import pysolr
from dynaconf import Dynaconf
from requests.auth import HTTPBasicAuth

settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)

solr = pysolr.Solr(settings.vlo_solr_url, auth=HTTPBasicAuth(settings.solr_vlo_usr, settings.solr_vlo_pwd), always_commit=False)
print(settings.vlo_solr_url)
# Create a client instance. The timeout and authentication options are not required.
# solr = pysolr.Solr('http://localhost:8983/solr/', always_commit=True, [timeout=10], [auth=<type of authentication>])

# Note that auto_commit defaults to False for performance. You can set
# `auto_commit=True` to have commands always update the index immediately, make
# an update call with `commit=True`, or use Solr's `autoCommit` / `commitWithin`
# to have your data be committed following a particular policy.

# Do a health check.
ping = json.loads(solr.ping())
print("PING:", ping.get("status", False))


def _get_results(q: str, fq: [str], rows: int, start: int) -> pysolr.Results:
    return solr.search(q=q, fq=fq, rows=rows, start=start)


# From Raw response:
# print(results.raw_response['response']['numFound'])
# http://localhost:8183/solr/vlo-index/select?indent=true&q.op=OR&q=_harvesterRoot%3ANDEE
# CLARIAH Partners

# https://stackoverflow.com/questions/50720165/how-to-do-facet-search-with-pysolr
# solr.search([solrquery], facet = True , ** {'facet': 'true', 'facet.field' : ['cLp_fair_a1_1']})

# result = conn.search('*:*', **{
#     'fl': 'content',
#     'facet': 'true',
#     'facet.field': 'cLp_fair_a1_1'
# })
# response:
# {'facet_dates': {},
#  'facet_fields': {'field_name': ['value', 54439, 'value2', 21179]},
#  'facet_intervals': {},
#  'facet_queries': {},
#  'facet_ranges': {}}

results = True
start_idx = 0
batch_size = 10

filter_queries = ['_harvesterRoot:(NDE*)']
query = "*:*"

while results:
    results = _get_results(query, fq=filter_queries, rows=batch_size, start=start_idx)
    if start_idx == 0: print("TOTAL HITS:", str(results.hits))
    start_idx = start_idx + batch_size
    for result in results:
        print("Name: {0}.".format(result['name'][0]))
        # print("\t {0}.".format(result['description'][0]))

    # Stop after first 10 results...
    if start_idx >= 10:
        results = False
        print(emoji.emojize(':construction:'), "Stopped printing results...")

# How you'd index data.
# solr.add([
#     {
#         "id": "doc_1",
#         "title": "A test document",
#     },
#     {
#         "id": "doc_2",
#         "title": "The Banana: Tasty or Dangerous?",
#         "_doc": [
#             { "id": "child_doc_1", "title": "peel" },
#             { "id": "child_doc_2", "title": "seed" },
#         ]
#     },
# ])


# You can index a parent/child document relationship by
# associating a list of child documents with the special key '_doc'. This
# is helpful for queries that join together conditions on children and parent
# documents.

# Later, searching is easy. In the simple case, just a plain Lucene-style
# query is fine.

# The ``Results`` object stores total results found, by default the top
# ten most relevant results and any additional data like
# facets/highlighting/spelling/etc.


# For a more advanced query, say involving highlighting, you can pass
# additional options to Solr.
# results = solr.search('bananas', **{
#     'hl': 'true',
#     'hl.fragsize': 10,
# })

# You can also perform More Like This searches, if your Solr is configured
# correctly.
# similar = solr.more_like_this(q='id:doc_2', mltfl='text')

# Finally, you can delete either individual documents,
# solr.delete(id='doc_1')

# also in batches...
# solr.delete(id=['doc_1', 'doc_2'])

# ...or all documents.
# solr.delete(q='*:*')
#
