"""A capacity-expansion planner on lpspec: a solve job, an archive directory, and a site that reads it.

The solve job (:mod:`showcase.solve`) is the only module that imports lpspec.
The queries (:mod:`showcase.warehouse`) and the site's data loader read the
parquet the job archived, and nothing else.
"""
