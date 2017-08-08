Alert: PIP documentation could be badly formatted due to [this pypan bug](https://github.com/jgm/pandoc/issues/3511) , please see https://github.com/sanskrit-coders/sanskrit_data/blob/master/README.md in the meantime.

# Introduction
This module defines:

- **schema**
    - shared standard schema for communicating and storing Sanskrit data of various types.
    - various idiosyncratic notations used by various modules which deviate from the proposed standards.
- **python classes** (corresponding to the schema) and **shared libraries** for validating, (de-)serializing and storing sanskrit data of various types.
- a **common database interface** for accessing various databases (so that a downstream app can switch to a different database with a single line change).

Similar libraries in various other languages are being built:

- Scala (likely compatible with Java): [db-interface](https://github.com/sanskrit-coders/db-interface) .

## Motivation
- Various sanskrit modules need to communicate data amongst each other (for example through a REST API or database stores or even function calls). **Examples of the data being communicated** could be:
    - Gramatical details of a given word
    - Sentences in a given book chapter
    - Annotations on a given phrase
- When it comes to serialization formats - two distinct approaches present themselves to us:
    - One possible route is to have each project defining and using its own idiosyncratic notation. But this entails an additional burdens:
        - Each communicating module having to convert the data from one idiosyncratic notation to another.
        - Good schema design or notation is non trivial. Even if no external module is using the data, it is a waste to have to reinvent the wheel.
    - A superior route is to have a common, standard format for encoding various data-types for storage/ communication.
- To the extant possible, we should take latter approach to data storage and communication.
- Where idiosyncratic notations are adapted for various reasons, it is still desirable to collect such definitions in a single module - to facilitate conversion to the standard format.

# For users
## Installation
* Latest release: `sudo pip2 install sanskrit_data -U`
* Development copy: `sudo pip2 install git+https://github.com/sanskrit-coders/sanskrit_data@master -U`
* [Web](https://pypi.python.org/pypi/sanskrit_data).

## Usage
- Please see the generated python sphynx docs in one of the following places:
    - http://sanskrit-data.readthedocs.io - currently broken due to BUILD errors - see [bug](https://github.com/rtfd/readthedocs.org/issues/3021) .
    - under docs/_build/html/index.html
    - [project page](https://sanskrit-coders.github.io/sanskrit_data/build/html/sanskrit_data.html).
- Design considerations for data containers corresponding to the various submodules (such as books and annotations) are given below - or in the corresponding source files.

# For contributors
## Contact
Have a problem or question? Please head to [github](https://github.com/sanskrit-coders/sanskrit_data).

## Packaging
* ~/.pypirc should have your pypi login credentials.
```
python setup.py bdist_wheel
twine upload dist/* --skip-existing
```

## Document generation
- Sphynx html docs can be generated with `cd docs; make html`
- http://sanskrit-data.readthedocs.io/en/latest/sanskrit_data.html should automatically have good updated documentation - unless there are build errors.
