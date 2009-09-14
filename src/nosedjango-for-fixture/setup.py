from setuptools import setup, find_packages

setup(
    name='NoseDjango',
    version='0.6',
    author='',
    author_email = '',
    description = '',
    install_requires='nose>=0.10',
    url = "",
    license = '',
    packages = find_packages(),
    zip_safe = False,
    include_package_data = True,
    entry_points = {
        'nose.plugins': [
            'django = nosedjango.nosedjango:NoseDjango',
            ]
        }
    )

