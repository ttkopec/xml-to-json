from distutils.core import setup

setup(
    name='xml-to-json',
    packages=['xmltojson'],
    version='0.1',
    description='Schema aware xml to json translator based on xsl',
    author='Tomasz Kopec',
    author_email='tkopec@cisco.com',
    url='https://github.com/ttkopec/pyang',
    install_requires=[
        "pyang !=1.7.4, >= 1.7.3"
    ],
    keywords=['xml', 'yang', 'xsl'],
)
