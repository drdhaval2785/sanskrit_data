Alert: PIP documentation is badly formatted due to [this pypan bug](https://github.com/bebraw/pypandoc/issues/143) , please see https://github.com/sanskrit-coders/sanskrit_data/blob/master/README.md in the meantime.

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
- http://sanskrit-data.readthedocs.io should automatically have good updated documentation - unless there are build errors.

# Design principles
## Data design
### General principles
- We want data to be stored and communicated between programs in a popular, extensible format - we want to take advantage of existing technologies to the maximum possible extant and not waste time reinventing associated (de)serialization, validation and other libraries.
- But this does not prevent the data from being presented in a different format for human consumption.

While designing the JSON **data-model**:
- Type-hint in JSON should be jsonClass (a language-independent name we've picked).
- Try to avoid field-names which conflict with programming language keywords. (Eg. Prefer "source_type" to "type").
- In general, use camelCase or underscore_case for field names - both are fine. Where romanized (potentially mixed case) sanskrit words are used, the latter is the superior convention.
- Where field names and values are to be automatically rendered into various scripts, as in case of sanskrit vyAkarana jargon (eg: vibhakti, lakAra), we prefer SLP1 transliteration ("viBakti", "lakAra").
  - PS: Convenient transliteration modules are available in various languages: please see them listed [here](https://github.com/sanskrit-coders/indic-transliteration#libraries-in-other-languages).
  - A [transliteration map](https://docs.google.com/spreadsheets/d/1o2vysXaXfNkFxCO-WD77C4AEbXcAcJmDVgUb-E0mYbg/edit#gid=0) for reference.
- When in doubt, keep fields optional.

### Books and annotations
- Basic principles
  - Books are stored as a hierarchy of BookPortion objects - book containing many chapters containing many lines etc..
  - Annotations are stored in a similar hierarchy, for example - a TextAnnotation having PadaAnnotations having SamaasaAnnotations.
    - Some Annotations (eg. SandhiAnnotation, TextAnnotation) can have multiple "targets" (ie. other objects being annotated).
    - Rather than a simple tree, we end up with a Directed Acyclic Graph (DAG) of Annotation objects.
- JSON schema mindmap [here](https://drive.mindmup.com/map?state=%7B%22ids%22:%5B%220B1_QBT-hoqqVbHc4QTV3Q2hjdTQ%22%5D,%22action%22:%22open%22,%22userId%22:%22109000762913288837175%22%7D) (Updated as needed).
- The data containers are in a separate sanskrit_data module - so that it can be extracted and used outside this server.

## Python data containers and utilities
- For each JSON schema, we have a python class, at the root of which there is the generic JsonObject class with a lot of utilities. We define a hierarchy of classes so as to share validation and other code specific to certain data classes.
- **Separate Database-specific elements through an interface**. We should be able to easily switch to a different database.
