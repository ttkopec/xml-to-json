import os

import lxml.etree as ET
import pyang.stub as stub

_dir = os.path.dirname(os.path.realpath(__file__))
xsl_path = os.path.join(_dir, 'out.xsl')
xml_path = os.path.join(_dir, 'out.xml')
_files = [xsl_path, xml_path]


def gen_xslt_string(models, yang_directory):
    stub.run(models, 'jsonxsl', xsl_path, yang_directory)


def gen_sample_xml_string(models, yang_directory):
    stub.run(models, 'sample-xml-skeleton', xml_path, yang_directory, sample_defaults=True)


def cleanup():
    for f in _files:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


def parse(xsl, xml):
    xsl_tree = ET.parse(xsl)
    xml_tree = ET.parse(xml)

    transform = ET.XSLT(xsl_tree)
    transformed_xml = transform(xml_tree)

    return transform.tostring(transformed_xml)


def yangs_to_json(models, yang_directory, do_cleanup=True):
    try:
        cleanup()

        gen_sample_xml_string(models, yang_directory)
        gen_xslt_string(models, yang_directory)

        result = parse(*_files)

        if do_cleanup:
            cleanup()

        return result
    except Exception as e:
        if do_cleanup:
            cleanup()
        raise e
