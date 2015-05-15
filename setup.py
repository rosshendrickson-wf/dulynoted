from setuptools import find_packages, setup


def get_version():
    import imp
    import os

    with open(os.path.join('dulynoted', '_pkg_meta.py'), 'rb') as f:
        mod = imp.load_source('_pkg_meta', 'biloba', f)

        return mod.version


setup_args = dict(
    name='dulynoted',
    version=get_version(),
    license='Apache',
    description="""dulynoted is a light weight commit log for Google App Engine
                that allows you to write changes quickly and update them to
                 using a different process in a more structured way than just
                 using a pull queue.""",
    author='Ross Hendrickson',
    author_email='ross.hendrickson@savorywatt.com',
    url='http://github.com/savorywatt/dulynoted',
    packages=find_packages(exclude=['example']),
    classifiers=[
        'Development Status :: 1 - Pre-Production/Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: Apache',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)


if __name__ == '__main__':
    setup(**setup_args)
