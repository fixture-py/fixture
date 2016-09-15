from setuptools import setup, find_packages


setup(
    name='addressbook',
    version='0.1',
    description='',
    author='',
    author_email='',
    url='',
    install_requires=[
        "Routes==1.10.3",
        "Pylons==0.9.7",
        "SQLAlchemy==0.4.8",
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'addressbook': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'addressbook': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = addressbook.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
