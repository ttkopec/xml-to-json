import os
import re

PATTERNS = {'namespace': re.compile(r'namespace \"(.*)\"'),
            'revision': re.compile(r'revision (.*) {')}


class Model:
    def __init__(self, namespace=None, revision=None, name=None, file_name=None, abs_path=None):
        self.namespace = namespace
        self.revision = revision
        self.name = name
        self.file_name = file_name
        self.abs_path = abs_path

    def __repr__(self):
        return str(self.__dict__)


def search_line(pattern, line):
    res = pattern.search(line)

    if res:
        return res.group(1)
    else:
        return None


def search_file(file_path, pattern_dict):
    collected_params = {key: None for key in pattern_dict.keys()}

    with open(file_path, 'r') as fp:
        for line in fp.readlines():
            for param, value in collected_params.items():
                if value is None:
                    collected_params[param] = search_line(pattern_dict[param], line)

            if all(param is not None for param in collected_params.values()):
                return collected_params

    return collected_params


def extract_namespaces(xml_string):
    pattern = re.compile(r'xmlns=\"(.*?)\"')
    return pattern.findall(xml_string)


def get_models_dict(directories):
    YANGs = {}

    for directory in directories.split(':'):
        for root, subdirs, files in os.walk(directory):
            for yang_file_name in filter(lambda file: file.endswith('.yang'), files):
                abs_path = os.path.abspath(os.path.join(root, yang_file_name))
                name = os.path.splitext(yang_file_name)[0]

                # STRIP REVISION NUMBER - TO REMOVE
                # name = name.split('@')[0]
                ##################

                params = search_file(abs_path, PATTERNS)
                params['name'] = name
                params['file_name'] = yang_file_name
                params['abs_path'] = abs_path

                YANGs[params['namespace']] = Model(**params)

    return YANGs
