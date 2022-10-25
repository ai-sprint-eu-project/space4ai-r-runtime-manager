from setuptools import setup, find_packages

setup(
    name='runtime',
    version='0.1',
    author='Giuseppe Caccia e Nhikolas Bedoya',
    long_description='runtime_manager',
    url='',
    python_requires='>=3.7',
    # package_data={"": ['Dockerfile.template', 'script.sh', 'oscar.yaml', 'oscar_wn.yaml']},
    # packages = find_packages(),
    install_requires=['requests', 'click'],
    entry_points={
        'console_scripts': [
            'runtime=runtime_manager.bin.runtime_manager_cli:runtime_manager_cli',
        ]
    }
)