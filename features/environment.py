"""behave lifecycle hooks - the only wiring in the suite.

before_all picks which package the features run against. HADR_PKG defaults to the
student's own code (hadr_agent); the instructor/CI run sets HADR_PKG=hadr_solution
to prove the same feature files pass against the reference. That is the whole "does
a reference satisfy these specs" guarantee, in one readable place - no interpreter,
no injection magic. (No per-scenario reset needed: behave's layered context drops
everything a scenario set when it ends.)
"""

import importlib
import os


def before_all(context):
    pkg = os.environ.get("HADR_PKG", "hadr_agent")
    reports = importlib.import_module(f"{pkg}.stores.reports")
    incidents = importlib.import_module(f"{pkg}.stores.incidents")
    context.Report = reports.Report
    context.ReportStore = reports.ReportStore
    context.IncidentStore = incidents.IncidentStore
    context.reconcile = importlib.import_module(f"{pkg}.reconcile")
    context.intake = importlib.import_module(f"{pkg}.intake")
    context.agent = importlib.import_module(f"{pkg}.agent")
    context.dispatch = importlib.import_module(f"{pkg}.dispatch")
