from setuptools import setup, find_packages

setup(
    name='NoseDjango',
    version='0.6',
    author='Victor Ng',
    author_email = 'crankycoder@gmail.com',
    description = 'nose plugin for easy testing of django projects ' \
        'and apps. Sets up a test database (or schema) and installs apps ' \
        'from test settings file before tests are run, and tears the test ' \
        'database (or schema) down after all tests are run.',
    install_requires='nose>=0.10',
    url = "http://www.assembla.com/spaces/nosedjango",
    license = 'GNU LGPL',
    packages = find_packages(),
    zip_safe = False,
    include_package_data = True,
    entry_points = {
        'nose.plugins': [
            'django = nosedjango.nosedjango:NoseDjango',
            ]
        }
    )

