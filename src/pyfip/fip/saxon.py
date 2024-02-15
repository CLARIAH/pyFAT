import os
from importlib import resources
from xml.etree import ElementTree

import elementpath
from elementpath.xpath30 import XPath30Parser
from saxonche import PySaxonProcessor, PyXdmNode, PyXdmValue

with PySaxonProcessor(license=False) as proc:
    print(proc.version)
    xsltproc = proc.new_xslt30_processor()
    executable = xsltproc.compile_stylesheet(stylesheet_file=str(resources.files("tests.resources.xsl").joinpath("cat.xsl")))

    result = executable.apply_templates_returning_string(source_file=str(resources.files("tests.resources.xsl").joinpath("person.xml")))
    print(result)

    value = PyXdmValue()

    for n in [8, 9, 10]:
        value.add_xdm_item(proc.make_integer_value(n))

    print(value)
    executable.set_parameter("values", value)

    result = executable.apply_templates_returning_string(source_file=str(resources.files("tests.resources.xsl").joinpath("person.xml")))
    print(result)

# SaxonC-HE 12.4.1 processor:
# Provides processing in XSLT 3.0, XQuery 3.0/3.1 and XPath 2.0/3.0/3.1, and Schema validation 1.0/1.1.
# https://www.saxonica.com/saxon-c/doc12/html/saxonc.html
# https://github.com/tennom/saxonpy-win/blob/master/python_saxon/saxon_example.py
# https://github.com/tennom/saxonpy-win/blob/master/samples/data/test.xsl

# https://medium.com/@eric.websmith/python-xpath-2-0-with-elementpath-b31176e1fe4f
# https://elementpath.readthedocs.io/en/latest/introduction.html
# https://www.w3.org/TR/xpath-functions-30/

root = ElementTree.XML('<A><B1/><B2><C1>c1</C1><C2>c2</C2><C3>c3</C3></B2></A>')

mat = elementpath.select(root, 'math:atan(1.0e0)', parser=XPath30Parser)
print(mat)

e = elementpath.select(root, "/A/*/*/text()")
for t in e:
    print(t)

with PySaxonProcessor(license=False) as proc:
    print(proc.version)
    xquery_processor = proc.new_xquery_processor()
    xdm_int_value = proc.make_integer_value(12)
    # print(xdm_int_value)
    xquery_processor.set_parameter('n', xdm_int_value)

    result = xquery_processor.run_query_to_value(query_text='declare variable $n external; (1 to $n)!(. * .)')
    print(result.size)

with PySaxonProcessor(license=False) as proc:
    print(proc.version)
    # print(dir(proc))
    xdmAtomicval = proc.make_boolean_value(False)

    xsltproc = proc.new_xslt30_processor()

    xsltproc.set_cwd(os.getcwd())
    # xsltproc.set_source("person.xml")
    xml_doc = proc.parse_xml(xml_text="<out><person>text1</person><person>text2</person><person>text3</person></out>")
    # xslt_exec = xsltproc.compile_stylesheet(stylesheet_text="<xsl:stylesheet xmlns:xsl='http://www.w3.org/1999/XSL/Transform' version='2.0'>       <xsl:param name='values' select='(2,3,4)' /><xsl:output method='xml' indent='yes' /><xsl:template match='*'><output><xsl:value-of select='//person[1]'/><xsl:for-each select='$values' ><out><xsl:value-of select='. * 3'/></out></xsl:for-each></output></xsl:template></xsl:stylesheet>")
    executable = xsltproc.compile_stylesheet(stylesheet_file=str(resources.files("tests.resources.xsl").joinpath("cat.xsl")))

    if xsltproc.exception_occurred:
        print("Error found: ")
        print(xsltproc.error_message)
    print(xml_doc)

    output = executable.transform_to_string(xdm_node=xml_doc)
    if output is None:
        print(executable.error_message)
    else:
        print(output)

    # xsltproc.set_source(xdm_node=document)
    # xsltproc.set_jit_compilation(True)
    # result = xsltproc.transform_to_string(source_file="person.xml", stylesheet_file="cat.xsl")
    # result = xsltproc.transform_to_string(source_file="cat.xml", stylesheet_file="test1.xsl")
    # result = xsltproc.apply_templates_returning_value(xdm_value=xml_doc)

    # print(result)
    print('test 0 \n')
    xml = """\
    <out>
        <person>text1</person>
        <person>text2</person>
        <person>text3</person>
    </out>"""
    xp = proc.new_xpath_processor()

    node = proc.parse_xml(xml_text=xml)
    print('test 1\n node=' + node.string_value)
    xp.set_context(xdm_item=node)
    item = xp.evaluate_single('//person[1]')
    if isinstance(item, PyXdmNode):
        print(item.string_value)

    value = proc.make_double_value(3.5)
    print(value.primitive_type_name)

    print("new test case")
    xml2 = """\
    <out>
        <person att1='value1' att2='value2'>text1</person>
        <person>text2</person>
        <person>text3</person>
    </out>
    """

    node2 = proc.parse_xml(xml_text=xml2)
    print("node.node_kind=" + node2.node_kind_str)
    print("node.size=" + str(node2.size))
    print('cp1\n')
    outNode = node2.children
    print("len of children=" + str(len(node2.children)))
    print('element name=' + outNode[0].name)
    children = outNode[0].children
    print(*children)
    attrs = children[1].attributes
    if len(attrs) == 2:
        print(attrs[1].string_value)

    xsltproc = proc.new_xslt30_processor()
    xsltproc.set_cwd(os.getcwd())

    executable = xsltproc.compile_stylesheet(stylesheet_file=str(resources.files("tests.resources.xsl").joinpath("cat.xsl")))
    executable.set_result_as_raw_value(True)
    executable.set_initial_match_selection(file_name=str(resources.files("tests.resources.xsl").joinpath("person.xml")))

    # xdm_atomic_value = proc.make_integer_value(2)
    # xdm_atomic_value = proc.make_integer_value(6)
    # value = proc.make_array([proc.make_integer_value(i) for i in [8,9,10]])
    # value = proc.make_integer_value((2, 3, 4, 5, 6))
    value = proc.make_integer_value(23)

    print(value)
    executable.set_parameter("values", value)
    # executable.set_parameter("param2", xdm_atomic_value)
    result = executable.apply_templates_returning_string()
    print(result)

# SaxonC-HE 12.4.1 processor:
# Provides processing in XSLT 3.0, XQuery 3.0/3.1 and XPath 2.0/3.0/3.1, and Schema validation 1.0/1.1.
# https://www.saxonica.com/saxon-c/doc12/html/saxonc.html
# https://github.com/tennom/saxonpy-win/blob/master/python_saxon/saxon_example.py
# https://github.com/tennom/saxonpy-win/blob/master/samples/data/test.xsl

# https://medium.com/@eric.websmith/python-xpath-2-0-with-elementpath-b31176e1fe4f
# https://elementpath.readthedocs.io/en/latest/introduction.html
# https://www.w3.org/TR/xpath-functions-30/

with PySaxonProcessor(license=False) as proc:
    print(proc.version)
    xpproc = proc.new_xpath_processor()
    xpproc.set_cwd(os.getcwd())
    xpproc.set_context(file_name=str(resources.files("tests.resources.cmdi").joinpath("example-md-instance-1_2.cmdi.xml")))
    xpproc.declare_namespace("cmd", "http://www.clarin.eu/cmd/1")
    xpproc.set_parameter("f_A_1", proc.make_integer_value(23))

    result = xpproc.evaluate("string-join((//cmd:MdCreator,$f_A_1 * 10),':')")
    print(result)
