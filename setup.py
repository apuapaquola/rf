from setuptools import setup, find_packages

setup(
    name='rf',
    version='0.1.1.dev0',
    description='A framework for collaborative data analysis',
    long_description='A git-based framework enabling workflow, sharing and reproducibility for computational analyses',
    author='Apua Paquola',
    author_email='apuapaquola@gmail.com',
    url='https://github.com/apuapaquola/rf',
    license='GPLv3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha'
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
    ],
    keywords='bioinformatics reproducibility collaboration workflow git',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    entry_points={
        'console_scripts': [
            'rf=rf:main',
            ]
    }
)