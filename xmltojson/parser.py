import os
import xmltojson.yang as yang
import lxml.etree as ET
import pyang.stub as stub

_dir = os.getcwd()
xsl_path = os.path.join(_dir, 'out.xsl')
xml_path = os.path.join(_dir, 'out.xml')
_files = [xsl_path, xml_path]


def gen_xsl_file(models, yang_directory, output_file=xsl_path):
    """
    :param models: list of yang models, for example ['ietf-interfaces.yang', ...]
    :param yang_directory: single yang directory where models reside
    :param output_file: output file, default is `pwd`/out.xml
    :return: None
    """
    models = [os.path.join(yang_directory, model) for model in models]

    stub.run(models, 'jsonxsl', output_file, yang_directory)


def gen_sample_file(models, yang_directory, output_file=xml_path):
    models = [os.path.join(yang_directory, model) for model in models]

    stub.run(models, 'sample-xml-skeleton', output_file, yang_directory, sample_defaults=True)


def cleanup():
    for f in _files:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


def parse(xsl_tree, xml_tree):
    transform = ET.XSLT(xsl_tree)
    transformed_xml = transform(xml_tree)

    return transform.tostring(transformed_xml)


def parse_from_files(xsl_path, xml_path):
    xsl_tree = ET.parse(xsl_path)
    xml_tree = ET.parse(xml_path)

    return parse_from_files(xsl_tree, xml_tree)


def parse_from_strings(xsl_string, xml_string):
    xsl_tree = ET.fromstring(xsl_string)
    xml_tree = ET.fromstring(xml_string)

    return parse_from_files(xsl_tree, xml_tree)


def parse_from_rpc(rpc_string, yang_directory):
    rpc_tree = ET.fromstring(rpc_string)

    # get rid of <rpc-reply>
    data = rpc_tree.xpath('/nc:rpc-reply/nc:data/*', namespaces={'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0'})

    if len(data) == 0:
        print('Invalid rpc: no <data> inside <rpc-reply>')
        return None

    config = ET.fromstring('<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"></config>')

    for element in data:
        config.append(element)

    yangs = yang.get_models_dict(yang_directory)

    models = []

    for namespace in yang.extract_namespaces(ET.tostring(config).decode()):
        model = yangs.get(namespace, None)
        if not model:
            print('WARNING: No model with namespace: ({}) in directory: ({})'.format(namespace, model))
        else:
            models.append(model.file_name)

    output_file = xsl_path
    gen_xsl_file(models, yang_directory, output_file=output_file)
    xsl_tree = ET.parse(output_file)

    return parse(xsl_tree, config)


def yangs_to_json(models, yang_directory, do_cleanup=True):
    try:
        cleanup()

        gen_sample_file(models, yang_directory)
        gen_xsl_file(models, yang_directory)

        result = parse_from_files(*_files)

        if do_cleanup:
            cleanup()

        return result
    except Exception as e:
        if do_cleanup:
            cleanup()
        raise e