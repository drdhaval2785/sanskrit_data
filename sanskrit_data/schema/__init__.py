"""
Intro
-----------
schema package contains modules which define various modules describing various classes for storing Sanskrit data, and their corresponding JSON schema.

- At the base of every such class is the common.JsonObject class.
- Just pick the most suitable class to store your data (or contribute it here).

Data design
-----------

General principles
~~~~~~~~~~~~~~~~~~

-  We want data to be stored and communicated between programs in a
   popular, extensible format - we want to take advantage of existing
   technologies to the maximum possible extant and not waste time
   reinventing associated (de)serialization, validation and other
   libraries.
-  But this does not prevent the data from being presented in a
   different format for human consumption.

While designing the JSON **data-model**:

-  Type-hint in JSON should be jsonClass (a language-independent name
   we've picked).
-  Try to avoid field-names which conflict with programming language
   keywords. (Eg. Prefer "source\_type" to "type").
-  In general, use camelCase or underscore\_case for field names - both
   are fine. Where romanized (potentially mixed case) sanskrit words are
   used, the latter is the superior convention.
-  Where field names and values are to be automatically rendered into
   various scripts, as in case of sanskrit vyAkarana jargon (eg:
   vibhakti, lakAra), we prefer SLP1 transliteration ("viBakti",
   "lakAra").

   -  PS: Convenient transliteration modules are available in various
      languages: please see them listed
      `here <https://github.com/sanskrit-coders/indic-transliteration#libraries-in-other-languages>`__.
   -  A `transliteration
      map <https://docs.google.com/spreadsheets/d/1o2vysXaXfNkFxCO-WD77C4AEbXcAcJmDVgUb-E0mYbg/edit#gid=0>`__
      for reference.

-  When in doubt, keep fields optional.

Python data containers and utilities
------------------------------------

-  For each JSON schema, we have a python class, at the root of which
   there is the generic JsonObject class with a lot of utilities. We
   define a hierarchy of classes so as to share validation and other
   code specific to certain data classes.
-  **Separate Database-specific elements through an interface**. We
   should be able to easily switch to a different database.

Books and annotations
~~~~~~~~~~~~~~~~~~~~~
Please refer to :mod:`~sanskrit_data.schema.books` and :mod:`~sanskrit_data.schema.ullekhanam` .

"""

__all__ = ["common", "books", "ullekhanam", "users"]