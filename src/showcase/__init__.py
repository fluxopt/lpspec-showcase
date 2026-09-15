"""A capacity-expansion planner on lpspec: a solve job, an archive directory, and a dashboard.

The solve job (:mod:`showcase.solve`) is the only module that imports lpspec.
The dashboard (:mod:`showcase.dashboard`) and the queries under it
(:mod:`showcase.warehouse`) read the parquet the job archived, and nothing else.
"""
