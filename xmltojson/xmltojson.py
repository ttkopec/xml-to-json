import os

import lxml.etree as ET
import xmltojson._pyang as _pyang


class PyangWrapper:
    _dir = os.path.dirname(os.path.realpath(__file__))
    xsl = os.path.join(_dir, 'out.xsl')
    xml = os.path.join(_dir, 'out.xml')
    _files = [xsl, xml]

    @staticmethod
    def gen_xslt_string(models, yang_directory):
        _pyang.run(models, 'jsonxsl', PyangWrapper.xsl, yang_directory)

    @staticmethod
    def gen_sample_xml_string(models, yang_directory):
        _pyang.run(models, 'sample-xml-skeleton', PyangWrapper.xml, yang_directory, sample_defaults=True)

    @staticmethod
    def cleanup():
        for f in PyangWrapper._files:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

    @staticmethod
    def parse(xsl, xml):
        xsl_tree = ET.parse(xsl)
        xml_tree = ET.parse(xml)

        transform = ET.XSLT(xsl_tree)
        transformed_xml = transform(xml_tree)

        return transform.tostring(transformed_xml)

    @staticmethod
    def yangs_to_json(models, yang_directory):
        try:
            PyangWrapper.gen_sample_xml_string(models, yang_directory)
            PyangWrapper.gen_xslt_string(models, yang_directory)

            return PyangWrapper.parse(*PyangWrapper._files)
        except Exception as e:
            PyangWrapper.cleanup()
            raise e
