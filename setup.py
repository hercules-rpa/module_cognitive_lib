from setuptools import find_packages, setup

setup(
    name='module_cognitive_treelogic',
    packages=find_packages(),
    version='0.1.0',
    description='Module cognitive for Hercules project',
    author='Treelogic',
    license='Treelogic',
    install_requires=['pandas','matplotlib','pdf2image','numpy==1.22','imutils','PyPDF2','RPA','camelot-py[cv]','playwright','bs4'],
    setup_requires=['pytest-runner'],
    test_suite='test'
)