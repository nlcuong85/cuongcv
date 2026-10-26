#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import http.client
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dateutil import parser as date_parser


CITY_ALIASES = {
    "Heidelberg": ("heidelberg",),
    "Mannheim": ("mannheim",),
    "Ludwigshafen": ("ludwigshafen",),
    "Heilbronn": ("heilbronn",),
    "Walldorf": ("walldorf",),
    "Karlsruhe": ("karlsruhe",),
    "Bruchsal": ("bruchsal",),
    "Pforzheim": ("pforzheim",),
    "Stuttgart": ("stuttgart",),
    "Sindelfingen": ("sindelfingen",),
    "Boeblingen": ("böblingen", "boeblingen"),
    "Ludwigsburg": ("ludwigsburg",),
    "Esslingen": ("esslingen",),
    "Frankfurt": ("frankfurt",),
    "Darmstadt": ("darmstadt",),
    "Mainz": ("mainz",),
    "Wiesbaden": ("wiesbaden",),
    "Aschaffenburg": ("aschaffenburg",),
    "Wuerzburg": ("würzburg", "wurzburg"),
    "Nuremberg": ("nürnberg", "nuernberg", "nuremberg"),
    "Ulm": ("ulm",),
    "Augsburg": ("augsburg",),
    "Munich": ("münchen", "muenchen", "munich"),
    "Berlin": ("berlin",),
    "Hamburg": ("hamburg",),
    "Cologne": ("köln", "koeln", "cologne"),
    "Duesseldorf": ("düsseldorf", "duesseldorf"),
    "Dortmund": ("dortmund",),
    "Essen": ("essen",),
    "Bremen": ("bremen",),
    "Hanover": ("hannover", "hanover"),
    "Leipzig": ("leipzig",),
    "Dresden": ("dresden",),
    "Bonn": ("bonn",),
    "Muenster": ("münster", "muenster", "munster"),
    "Freiburg": ("freiburg",),
    "Tuebingen": ("tübingen", "tuebingen"),
    "Reutlingen": ("reutlingen",),
    "Regensburg": ("regensburg",),
    "Ingolstadt": ("ingolstadt",),
    "Erlangen": ("erlangen",),
    "Fuerth": ("fürth", "fuerth"),
    "Kassel": ("kassel",),
    "Saarbruecken": ("saarbrücken", "saarbruecken"),
}

DEFAULT_PROFILE = "student"

FULLTIME_NEGATIVE_ROLE_FRAGMENT = (
    '-werkstudent -internship -praktikum -teilzeit -"part-time" -minijob -nebenjob '
    "-masterarbeit -bachelorarbeit -abschlussarbeit -thesis"
)
GERMANY_WIDE_LOCATION_FRAGMENT = (
    "(germany OR deutschland OR berlin OR hamburg OR münchen OR muenchen OR stuttgart OR frankfurt "
    'OR köln OR koeln OR düsseldorf OR duesseldorf OR nürnberg OR nuernberg OR mannheim)'
)
FULLTIME_WEST_LOCATION_FRAGMENT = (
    "(baden-württemberg OR baden wurttemberg OR bayern OR bavaria OR hessen OR hesse "
    "OR rheinland-pfalz OR rhineland-palatinate OR nordrhein-westfalen OR north rhine-westphalia "
    "OR saarland OR niedersachsen OR lower saxony OR bremen OR hamburg OR berlin "
    "OR stuttgart OR karlsruhe OR mannheim OR walldorf OR heilbronn OR münchen OR muenchen "
    "OR nürnberg OR nuernberg OR frankfurt OR mainz OR wiesbaden OR köln OR koeln "
    "OR düsseldorf OR duesseldorf OR bonn OR hannover OR hanover)"
)
SOUTH_GERMANY_LOCATION_FRAGMENT = (
    "(baden-württemberg OR baden wurttemberg OR bayern OR bavaria OR hessen OR hesse OR rheinland-pfalz "
    "OR rhineland-palatinate OR saarland OR nordrhein-westfalen OR north rhine-westphalia OR nrw "
    "OR heidelberg OR mannheim OR walldorf OR heilbronn OR karlsruhe OR stuttgart OR sindelfingen "
    "OR böblingen OR boeblingen OR ulm OR münchen OR muenchen OR augsburg OR nürnberg OR nuernberg "
    "OR regensburg OR ingolstadt OR frankfurt OR darmstadt OR wiesbaden OR mainz OR ludwigshafen "
    "OR koblenz OR saarbrücken OR saarbruecken OR köln OR koeln OR düsseldorf OR duesseldorf OR bonn OR aachen)"
)

ROLE_QUERY_FRAGMENT = (
    '("business analyst" OR "product owner" OR "product management" OR "product manager" '
    'OR "requirements engineering" OR "requirements manager" OR "requirements engineer" '
    'OR requirements OR anforderungsmanagement OR anforderungsanalyse OR anforderungsmanager '
    'OR process OR "process management" OR "process development" OR "process improvement" '
    'OR "process optimization" OR "process automation" OR prozessmanagement OR prozessoptimierung '
    'OR prozessanalyse OR prozessmodellierung OR prozessautomatisierung OR "workflow automation" '
    'OR "business process management" OR "project management" OR "project management office" OR pmo '
    'OR testing OR testmanagement OR compliance OR "quality management" OR qualitätsmanagement '
    'OR digitalisation OR digitalization OR digitalisierung OR signavio OR bpmn OR "ai enablement")'
)

# The 15:00 student pass uses short, focused role groups rather than a single
# giant OR expression.  This avoids search-provider truncation and lets each
# role family compete for its own results.  The employment-type gate below
# still requires a working-student, internship, part-time, or similar student
# role; this is discovery breadth, not a claim that every IT role is a fit.
STUDENT_FOCUSED_ROLE_GROUPS = (
    (
        "business_product",
        '("business analyst" OR "product owner" OR "product management" OR "product manager" '
        'OR "business information systems" OR "business informatics" OR wirtschaftsinformatik '
        'OR "information systems" OR "requirements engineering" OR anforderungsmanagement)',
    ),
    (
        "data_ai",
        '("data analyst" OR "data analytics" OR "data science" OR "data engineer" '
        'OR "ai engineer" OR "artificial intelligence" OR "machine learning" OR "machine learning engineer")',
    ),
    (
        "software_engineering",
        '("software engineer" OR "software engineering" OR "software development" '
        'OR "full stack" OR fullstack OR "web development" OR "cloud engineering")',
    ),
    (
        "agile_it_delivery",
        '("scrum master" OR "agile coach" OR "it project management" OR "it consulting" '
        'OR "digital transformation" OR "process automation" OR "quality management")',
    ),
)

STUDENT_FOCUSED_QUERY_TEMPLATES = (
    'site:jobs.mercedes-benz.com OR site:jobs.sap.com OR site:jobs.bosch.com OR site:jobs.bosch.de OR site:jobs.bmwgroup.com {roles} '
    + SOUTH_GERMANY_LOCATION_FRAGMENT,
    'site:de.linkedin.com/jobs/view OR site:linkedin.com/jobs/view {roles} ' + SOUTH_GERMANY_LOCATION_FRAGMENT,
    'site:stepstone.de/stellenangebote OR site:softgarden.de/jobs OR site:de.indeed.com/viewjob OR site:indeed.com/viewjob OR site:jobs.meinestadt.de {roles} '
    + SOUTH_GERMANY_LOCATION_FRAGMENT,
    'site:jobs.lever.co OR site:boards.greenhouse.io OR site:jobs.ashbyhq.com OR site:jobs.personio.de OR site:join.com OR site:jobteaser.com OR site:workwise.io/jobs {roles} '
    + SOUTH_GERMANY_LOCATION_FRAGMENT,
    '{roles} ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) '
    + SOUTH_GERMANY_LOCATION_FRAGMENT,
)

STUDENT_TARGET_ROLE_PATTERNS = (
    "working student",
    "werkstudent",
    "werkstudentin",
    "werkstudenten",
    "student assistant",
    "student worker",
    "intern",
    "internship",
    "praktikum",
    "praktikant",
    "minijob",
    "mini-job",
    "teilzeit",
    "teilzeitjob",
    "part-time",
    "part time",
    "nebenjob",
    "aushilfe",
)

FULLTIME_TARGET_PATTERNS = (
    "full-time",
    "full time",
    "vollzeit",
    "permanent",
    "festanstellung",
    "unbefristet",
    "permanent employee",
    "regular position",
)

FULLTIME_EXCLUDE_PATTERNS = STUDENT_TARGET_ROLE_PATTERNS + (
    "temporary student",
    "studentische hilfskraft",
    "working student / part-time",
    "masterarbeit",
    "bachelorarbeit",
    "abschlussarbeit",
    "thesis",
)

GERMANY_COUNTRY_TERMS = {
    "de",
    "deu",
    "ger",
    "germany",
    "deutschland",
}

STUDENT_SCOPE_PATTERNS = (
    "baden-württemberg",
    "baden wurttemberg",
    "bavaria",
    "bayern",
    "hessen",
    "hesse",
    "rheinland-pfalz",
    "rhineland-palatinate",
    "saarland",
    "nordrhein-westfalen",
    "north rhine-westphalia",
    "nrw",
    "heidelberg",
    "mannheim",
    "walldorf",
    "heilbronn",
    "karlsruhe",
    "bruchsal",
    "pforzheim",
    "stuttgart",
    "sindelfingen",
    "böblingen",
    "boeblingen",
    "ludwigsburg",
    "esslingen",
    "ulm",
    "freiburg",
    "tübingen",
    "tuebingen",
    "reutlingen",
    "wernau",
    "plochingen",
    "münchen",
    "muenchen",
    "munich",
    "augsburg",
    "nürnberg",
    "nuernberg",
    "nuremberg",
    "würzburg",
    "wuerzburg",
    "regensburg",
    "ingolstadt",
    "erlangen",
    "fürth",
    "fuerth",
    "frankfurt",
    "darmstadt",
    "wiesbaden",
    "mainz",
    "ludwigshafen",
    "koblenz",
    "saarbrücken",
    "saarbruecken",
    "köln",
    "koeln",
    "cologne",
    "düsseldorf",
    "duesseldorf",
    "bonn",
    "aachen",
)

FULLTIME_ALLOWED_SCOPE_PATTERNS = (
    "baden-württemberg",
    "baden wurttemberg",
    "bavaria",
    "bayern",
    "hessen",
    "hesse",
    "rheinland-pfalz",
    "rhineland-palatinate",
    "nordrhein-westfalen",
    "north rhine-westphalia",
    "nrw",
    "saarland",
    "niedersachsen",
    "lower saxony",
    "bremen",
    "hamburg",
    "berlin",
    "heidelberg",
    "mannheim",
    "ludwigshafen",
    "walldorf",
    "heilbronn",
    "karlsruhe",
    "stuttgart",
    "sindelfingen",
    "böblingen",
    "boeblingen",
    "ludwigsburg",
    "esslingen",
    "frankfurt",
    "darmstadt",
    "mainz",
    "wiesbaden",
    "aschaffenburg",
    "würzburg",
    "wuerzburg",
    "nürnberg",
    "nuernberg",
    "nuremberg",
    "ulm",
    "augsburg",
    "munich",
    "münchen",
    "muenchen",
    "regensburg",
    "ingolstadt",
    "erlangen",
    "fürth",
    "fuerth",
    "cologne",
    "köln",
    "koeln",
    "duesseldorf",
    "düsseldorf",
    "bonn",
    "hanover",
    "hannover",
)

FULLTIME_BLOCKED_SCOPE_PATTERNS = (
    "sachsen",
    "saxony",
    "thüringen",
    "thueringen",
    "thuringia",
    "sachsen-anhalt",
    "saxony-anhalt",
    "brandenburg",
    "mecklenburg-vorpommern",
    "mecklenburg western pomerania",
    "leipzig",
    "dresden",
    "chemnitz",
    "erfurt",
    "jena",
    "halle",
    "magdeburg",
    "potsdam",
    "rostock",
    "schwerin",
)

FOREIGN_LOCATION_PATTERNS = (
    "prague",
    "praha",
    "czech republic",
    "czechia",
    "austria",
    "vienna",
    "wien",
    "switzerland",
    "zurich",
    "zürich",
    "netherlands",
    "amsterdam",
    "poland",
    "warsaw",
    "brno",
)

ROLE_KEYWORDS = {
    "product owner support": 18,
    "product owner": 16,
    "product management": 16,
    "product manager": 14,
    "product operations": 16,
    "business analyst": 18,
    "requirements": 18,
    "requirements engineering": 20,
    "requirements manager": 18,
    "requirements engineer": 18,
    "anforderungsmanagement": 20,
    "anforderungsanalyse": 18,
    "anforderungsmanager": 18,
    "fachkonzept": 16,
    "fachkonzeption": 16,
    "process": 16,
    "process development": 18,
    "process improvement": 18,
    "process optimization": 18,
    "process automation": 18,
    "process modelling": 16,
    "process modeling": 16,
    "workflow automation": 18,
    "business process management": 18,
    "prozessmanagement": 18,
    "prozessoptimierung": 18,
    "prozessanalyse": 16,
    "prozessmodellierung": 18,
    "prozessautomatisierung": 18,
    "digitalisierung": 16,
    "project management": 14,
    "project management office": 16,
    "pmo": 14,
    "testing": 14,
    "testmanagement": 14,
    "quality": 12,
    "quality management": 12,
    "qualitätsmanagement": 12,
    "compliance": 12,
    "data quality": 12,
    "datenqualität": 12,
    "signavio": 14,
    "bpmn": 14,
    "digitalisation": 14,
    "digitalization": 14,
    "operational excellence": 14,
    "continuous improvement": 14,
    "ai enablement": 16,
    "automation": 12,
    "prompt engineering": 12,
    "context engineering": 12,
    "internal web": 14,
    "it": 8,
}

SOURCE_PRIORITIES = {
    "jobs.mercedes-benz.com": 35,
    "jobs.sap.com": 35,
    "jobs.bosch.com": 35,
    "jobs.bosch.de": 35,
    "jobs.bmwgroup.com": 35,
    "jobs.schwarz": 34,
    "jobs.porsche.com": 34,
    "jobs.siemens.com": 34,
    "jobs.smartrecruiters.com": 28,
    "arbeitnow.com": 22,
    "de.linkedin.com": 18,
    "linkedin.com": 18,
    "softgarden.de": 24,
    "de.indeed.com": 18,
    "indeed.com": 18,
    "zenjob.com": 20,
    "jobs.meinestadt.de": 18,
    "jobs.michelin.de": 30,
    "stepstone.de": 18,
    "myability.jobs": 18,
    "jobs.lever.co": 20,
    "boards.greenhouse.io": 20,
    "jobs.ashbyhq.com": 20,
    "jobs.personio.de": 18,
    "join.com": 18,
    "jobteaser.com": 18,
    "workwise.io": 18,
    "jobware.de": 18,
}

DOMAIN_COMPANY_FALLBACKS = {
    "jobs.sap.com": "SAP",
    "jobs.bosch.com": "Robert Bosch GmbH",
    "jobs.bosch.de": "Robert Bosch GmbH",
    "jobs.bmwgroup.com": "BMW Group",
    "jobs.schwarz": "Schwarz Group",
    "jobs.porsche.com": "Porsche",
    "jobs.siemens.com": "Siemens",
    "jobs.smartrecruiters.com": "Bosch Group",
    "arbeitnow.com": "Arbeitnow listing",
    "de.indeed.com": "Indeed listing",
    "indeed.com": "Indeed listing",
    "zenjob.com": "Zenjob listing",
    "jobs.meinestadt.de": "Meinestadt listing",
    "jobs.lever.co": "Lever listing",
    "boards.greenhouse.io": "Greenhouse listing",
    "jobs.ashbyhq.com": "Ashby listing",
    "jobs.personio.de": "Personio listing",
    "join.com": "Join listing",
    "jobteaser.com": "JobTeaser listing",
    "workwise.io": "Workwise listing",
    "jobware.de": "Jobware listing",
}

SEARCH_PROFILES: dict[str, dict[str, Any]] = {
    "student": {
        "heading": "Daily Germany Working Student / Part-Time Search",
        "role_summary": "working student / internship / part-time / minijob / nebenjob",
        "scope_note": (
            "Focused on central and southern Germany: Baden-Württemberg, Bavaria, Hesse, Rhineland-Palatinate, Saarland, and North Rhine-Westphalia; grouped by city for faster scanning."
        ),
        "default_per_query": 10,
        "default_max_validate": 160,
        "target_role_patterns": STUDENT_TARGET_ROLE_PATTERNS,
        "exclude_role_patterns": (),
        "city_scores": {
            "Heidelberg": 18,
            "Heilbronn": 18,
            "Mannheim": 16,
            "Walldorf": 16,
            "Karlsruhe": 14,
            "Stuttgart": 16,
            "Sindelfingen": 16,
            "Boeblingen": 15,
            "Ludwigsburg": 13,
            "Esslingen": 13,
            "Ulm": 12,
            "Freiburg": 12,
            "Tuebingen": 12,
            "Reutlingen": 12,
            "Wuerzburg": 10,
            "Nuremberg": 10,
            "Erlangen": 9,
            "Fuerth": 9,
            "Regensburg": 9,
            "Ingolstadt": 9,
            "Augsburg": 10,
            "Munich": 11,
            "Frankfurt": 12,
            "Darmstadt": 11,
            "Mainz": 10,
            "Wiesbaden": 10,
            "Ludwigshafen": 11,
            "Cologne": 9,
            "Duesseldorf": 9,
            "Bonn": 9,
            "Saarbruecken": 8,
        },
        "output_order": (
            "Remote / Flexible",
            "Heidelberg",
            "Mannheim",
            "Walldorf",
            "Heilbronn",
            "Stuttgart",
            "Sindelfingen",
            "Boeblingen",
            "Ludwigsburg",
            "Esslingen",
            "Karlsruhe",
            "Bruchsal",
            "Pforzheim",
            "Freiburg",
            "Tuebingen",
            "Reutlingen",
            "Ulm",
            "Frankfurt",
            "Darmstadt",
            "Mainz",
            "Wiesbaden",
            "Ludwigshafen",
            "Cologne",
            "Duesseldorf",
            "Bonn",
            "Saarbruecken",
            "Munich",
            "Augsburg",
            "Wuerzburg",
            "Nuremberg",
            "Erlangen",
            "Fuerth",
            "Regensburg",
            "Ingolstadt",
            "Other / Unclear",
        ),
        "query_templates": (
            'site:jobs.mercedes-benz.com ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:jobs.sap.com ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:jobs.bosch.com OR site:jobs.bosch.de OR site:jobs.smartrecruiters.com/BoschGroup ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:de.linkedin.com/jobs/view OR site:linkedin.com/jobs/view ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:stepstone.de/stellenangebote OR site:softgarden.de/jobs OR site:de.indeed.com/viewjob OR site:indeed.com/viewjob OR site:jobs.meinestadt.de ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:jobs.lever.co OR site:boards.greenhouse.io OR site:jobs.ashbyhq.com OR site:jobs.personio.de OR site:join.com OR site:jobteaser.com ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:arbeitnow.com/jobs/companies {roles} ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob) '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:zenjob.com/de (minijob OR nebenjob OR teilzeit OR werkstudent) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            'site:jobware.de OR site:workwise.io/jobs ("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
            '("working student" OR werkstudent OR minijob OR teilzeit OR nebenjob OR internship OR praktikum) {roles} '
            + SOUTH_GERMANY_LOCATION_FRAGMENT,
        ),
    },
    "fulltime": {
        "heading": "Daily Germany Full-Time Search",
        "role_summary": "full-time / permanent / professional roles",
        "scope_note": (
            "Germany excluding East Germany, with Berlin allowed; grouped by city, with preference for southern, western, Hamburg, and Berlin matches."
        ),
        "default_per_query": 16,
        "default_max_validate": 96,
        "target_role_patterns": FULLTIME_TARGET_PATTERNS,
        "exclude_role_patterns": FULLTIME_EXCLUDE_PATTERNS,
        "city_scores": {
            "Heidelberg": 18,
            "Mannheim": 17,
            "Ludwigshafen": 15,
            "Walldorf": 16,
            "Heilbronn": 15,
            "Karlsruhe": 14,
            "Stuttgart": 17,
            "Sindelfingen": 16,
            "Boeblingen": 15,
            "Ludwigsburg": 14,
            "Esslingen": 14,
            "Frankfurt": 15,
            "Darmstadt": 13,
            "Mainz": 12,
            "Wiesbaden": 12,
            "Aschaffenburg": 11,
            "Wuerzburg": 11,
            "Nuremberg": 14,
            "Ulm": 10,
            "Augsburg": 9,
            "Munich": 10,
            "Berlin": 9,
            "Hamburg": 8,
            "Cologne": 8,
            "Duesseldorf": 8,
            "Bonn": 8,
            "Hanover": 7,
            "Bremen": 7,
            "Regensburg": 9,
            "Ingolstadt": 8,
            "Erlangen": 8,
            "Fuerth": 8,
            "Saarbruecken": 7,
        },
        "output_order": (
            "Remote / Flexible",
            "Heidelberg",
            "Mannheim",
            "Ludwigshafen",
            "Walldorf",
            "Heilbronn",
            "Stuttgart",
            "Sindelfingen",
            "Boeblingen",
            "Ludwigsburg",
            "Esslingen",
            "Karlsruhe",
            "Bruchsal",
            "Pforzheim",
            "Frankfurt",
            "Darmstadt",
            "Mainz",
            "Wiesbaden",
            "Aschaffenburg",
            "Wuerzburg",
            "Nuremberg",
            "Ulm",
            "Augsburg",
            "Munich",
            "Berlin",
            "Hamburg",
            "Cologne",
            "Duesseldorf",
            "Bonn",
            "Hanover",
            "Bremen",
            "Regensburg",
            "Ingolstadt",
            "Erlangen",
            "Fuerth",
            "Saarbruecken",
            "Other / Unclear",
        ),
        "query_templates": (
            'site:jobs.mercedes-benz.com {roles} ' + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:jobs.sap.com {roles} ' + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:jobs.bosch.com OR site:jobs.bosch.de OR site:jobs.smartrecruiters.com/BoschGroup OR site:jobs.porsche.com OR site:jobs.siemens.com {roles} '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:de.linkedin.com/jobs/view OR site:linkedin.com/jobs/view {roles} '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:stepstone.de/stellenangebote OR site:softgarden.de/jobs OR site:de.indeed.com/viewjob OR site:indeed.com/viewjob OR site:jobs.meinestadt.de OR site:jobware.de {roles} '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:jobs.lever.co OR site:boards.greenhouse.io OR site:jobs.ashbyhq.com OR site:jobs.personio.de OR site:join.com OR site:jobteaser.com OR site:workwise.io/jobs {roles} '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:arbeitnow.com/jobs/companies {roles} ' + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:de.linkedin.com/jobs/view OR site:linkedin.com/jobs/view ("business analyst" OR "product owner" OR "product manager" OR "project manager" OR "project management office") '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:de.linkedin.com/jobs/view OR site:linkedin.com/jobs/view ("requirements engineer" OR "requirements manager" OR "process manager" OR "process automation" OR "workflow automation" OR signavio OR bpmn) '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:stepstone.de/stellenangebote OR site:jobs.personio.de OR site:join.com ("business analyst" OR "product owner" OR "product manager" OR "process manager" OR signavio OR bpmn OR compliance OR testing) '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            'site:workwise.io/jobs OR site:jobware.de OR site:boards.greenhouse.io OR site:jobs.lever.co ("business analyst" OR "product owner" OR "process automation" OR "project management office" OR "quality management") '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
            '{roles} ("full-time" OR "full time" OR vollzeit OR festanstellung OR unbefristet OR remote OR hybrid OR permanent) '
            + FULLTIME_WEST_LOCATION_FRAGMENT + ' ' + FULLTIME_NEGATIVE_ROLE_FRAGMENT,
        ),
    },
}

OPENCLAW_HOME = Path(os.environ.get("OPENCLAW_HOME", str(Path.home() / ".openclaw"))).expanduser()
WORKSPACE_ROOT = Path(os.environ.get("FRANKLEE_WORKSPACE_ROOT", "/root/clawdFrankLee")).expanduser()
SERPAPI_ENV_FILE = Path(os.environ.get("SERPAPI_ENV_FILE", str(OPENCLAW_HOME / "serpapi.env"))).expanduser()
WEB_SEARCH_ENV_FILE = Path(
    os.environ.get("WEB_SEARCH_ENV_FILE", str(Path.home() / ".config" / "codex" / "web-search.env"))
).expanduser()
SERPAPI_FALLBACK_PATH = Path(
    os.environ.get("SERPAPI_FALLBACK_PATH", str(WORKSPACE_ROOT / "dist" / "serpapi_fallback.py"))
).expanduser()
EXA_SEARCH_PATH = Path(os.environ.get("EXA_SEARCH_PATH", str(WORKSPACE_ROOT / "dist" / "exa_search.py"))).expanduser()
GITHUB_INTAKES_API_URL = "https://api.github.com/repos/nlcuong85/cuongcv/contents/application-system/intakes?ref=main"
GITHUB_REPO_BLOB_PREFIX = "https://github.com/nlcuong85/cuongcv/blob/main/application-system/intakes/"
RECENT_POSTED_URLS_PATH = Path(
    os.environ.get("RECENT_POSTED_URLS_PATH", str(WORKSPACE_ROOT / "data" / "recent_posted_urls.json"))
).expanduser()
DIRECT_SOURCE_SITEMAPS = {
    "jobs.mercedes-benz.com": "https://jobs.mercedes-benz.com/sitemap.xml",
    "jobs.sap.com": "https://jobs.sap.com/sitemap.xml",
    "jobs.bosch.com": "https://jobs.bosch.com/sitemap.xml",
    "jobs.bmwgroup.com": "https://jobs.bmwgroup.com/sitemap.xml",
    "jobs.schwarz": "https://jobs.schwarz/sitemap.xml",
    "jobs.porsche.com": "https://jobs.porsche.com/sitemap.xml",
    "jobs.siemens.com": "https://jobs.siemens.com/sitemap.xml",
}

GENERIC_PAGE_PATTERNS = [
    "job offer result list",
    "jobs result",
    "stellenangebote",
    "suchergebnisse",
]

BROWSER_FALLBACK_DOMAINS = {
    "jobs.mercedes-benz.com",
    "jobs.sap.com",
    "jobs.bosch.com",
    "jobs.bosch.de",
    "jobs.bmwgroup.com",
    "jobs.schwarz",
    "jobs.porsche.com",
    "jobs.siemens.com",
    "jobs.smartrecruiters.com",
    "stepstone.de",
    "jobware.de",
    "jobs.lever.co",
    "boards.greenhouse.io",
    "jobs.ashbyhq.com",
    "jobs.personio.de",
}

BROWSER_BLOCK_PATTERNS = (
    "access denied",
    "forbidden",
    "enable javascript",
    "verify you are human",
    "just a moment",
    "request unsuccessful",
    "temporarily unavailable",
)

RAW_URL_REJECT_PATTERNS = {
    "stepstone.de": (
        "/jobs/",
        "/stellenangebote/in-",
    ),
    "jobware.de": (
        "/jobs/",
        "/jobsuche",
    ),
    "jobworld.de": (
        "/jobs-",
    ),
    "zenjob.com": (
        "/de/jobs/",
    ),
    "hays.de": (
        "/jobprofile/",
    ),
}

CLOSED_PATTERNS = [
    "no longer available",
    "position has been filled",
    "job is no longer available",
    "stelle ist nicht mehr verfügbar",
    "job not found",
    "404",
    "position closed",
    "bewerbungsfrist abgelaufen",
]

APPLY_PATTERNS = [
    "apply now",
    "apply for this job",
    "jetzt bewerben",
    "bewerben",
    "zur bewerbung",
    "application form",
    "easy apply",
]

TARGET_ROLE_PATTERNS = [
    "working student",
    "werkstudent",
    "werkstudentin",
    "werkstudenten",
    "student assistant",
    "student worker",
    "intern",
    "internship",
    "praktikum",
    "praktikant",
    "minijob",
    "mini-job",
    "teilzeit",
    "teilzeitjob",
    "part-time",
    "part time",
    "nebenjob",
    "aushilfe",
]


@dataclass
class Candidate:
    query: str
    title: str
    url: str
    snippet: str
    source: str
    search_date: str


def get_profile(profile_name: str) -> dict[str, Any]:
    if profile_name not in SEARCH_PROFILES:
        raise ValueError(f"Unknown search profile: {profile_name}")
    return SEARCH_PROFILES[profile_name]


def build_discovery_queries(profile_name: str) -> list[str]:
    profile = get_profile(profile_name)
    if profile_name == "student":
        return [
            template.format(roles=roles)
            for _, roles in STUDENT_FOCUSED_ROLE_GROUPS
            for template in STUDENT_FOCUSED_QUERY_TEMPLATES
        ]
    return [template.format(roles=ROLE_QUERY_FRAGMENT) for template in profile["query_templates"]]


def default_runs_path_for_profile(profile_name: str) -> Path:
    if profile_name == "fulltime":
        return OPENCLAW_HOME / "cron" / "runs" / "daily-germany-fulltime-0900-berlin.jsonl"
    return OPENCLAW_HOME / "cron" / "runs" / "74e37d6d-099b-4ef8-84b1-53a5cbc06b43.jsonl"


def default_recent_cache_for_profile(profile_name: str) -> Path:
    if profile_name == "fulltime":
        return WORKSPACE_ROOT / "data" / "recent_posted_urls_fulltime.json"
    return RECENT_POSTED_URLS_PATH


def canonical_city_from_text(text: str) -> str | None:
    text_lower = text.lower()
    for city, aliases in CITY_ALIASES.items():
        if any(alias in text_lower for alias in aliases):
            return city
    return None


def render_city_label(city: str) -> str:
    replacements = {
        "Wuerzburg": "Wuerzburg",
        "Boeblingen": "Boeblingen",
        "Duesseldorf": "Duesseldorf",
        "Tuebingen": "Tuebingen",
        "Muenster": "Muenster",
        "Fuerth": "Fuerth",
        "Saarbruecken": "Saarbruecken",
    }
    return replacements.get(city, city)


def bucket_from_location(location: str) -> str:
    canonical = canonical_city_from_text(location)
    if canonical:
        return canonical
    cleaned = re.sub(r"\s+", " ", location).strip(" -")
    if not cleaned:
        return "Other / Unclear"
    primary = re.split(r"\s*(?:,|/|\|| near | bei )\s*", cleaned, maxsplit=1)[0].strip()
    if not primary or primary.lower() in {"germany", "deutschland", "de"}:
        return "Other / Unclear"
    return primary[:48]


def render_city_bucket(item: dict[str, Any]) -> str:
    work_model = str(item.get("work_model") or "").lower()
    if "remote" in work_model:
        return "Remote / Flexible"
    return bucket_from_location(str(item.get("location") or ""))


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def build_provider_env() -> dict[str, str]:
    env = os.environ.copy()
    for env_file in (WEB_SEARCH_ENV_FILE, SERPAPI_ENV_FILE):
        for key, value in load_env_file(env_file).items():
            env[key] = value
    return env


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", parsed.path).rstrip("/")
    se_match = re.search(r"/jobs/([0-9]+)", path)
    if se_match and "careers.se.com" in host:
        return f"{host}/jobid/{se_match.group(1)}"
    mercedes_match = re.search(r"(MER[0-9A-Z]+)", path, flags=re.I)
    if mercedes_match and "mercedes-benz.com" in host:
        return f"{host}/jobid/{mercedes_match.group(1).upper()}"
    sap_match = re.search(r"/(\d{7,})/?$", path)
    if sap_match and "jobs.sap.com" in host:
        return f"{host}/jobid/{sap_match.group(1)}"
    bosch_match = re.search(r"[?&]id=([A-Za-z0-9-]+)", parsed.query)
    if bosch_match and ("bosch" in host or "smartrecruiters.com" in host):
        return f"{host}/jobid/{bosch_match.group(1)}"
    arbeitnow_match = re.search(r"-([0-9]{4,})$", path)
    if arbeitnow_match and "arbeitnow.com" in host:
        return f"{host}/jobid/{arbeitnow_match.group(1)}"
    if host.endswith("linkedin.com"):
        return f"{host}{path}"
    return f"{host}{path}"


def normalize_title_text(value: str) -> str:
    text = urllib.parse.unquote(str(value or "")).lower()
    text = re.sub(r"\|.*$", "", text)
    text = re.sub(r"\bjob details\b.*$", "", text)
    text = re.sub(r"\s*[-–—]\s*\d+\s*$", "", text)
    text = re.sub(r"\((?:f/m/d|m/w/d|w/m/d|d/m/w|all genders|gn)\)", "", text)
    text = re.sub(r"\b(?:f/m/d|m/w/d|w/m/d|d/m/w|all genders|gn)\b", "", text)
    text = re.sub(r"[^a-z0-9äöüß+/#.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_company_text(value: str) -> str:
    text = urllib.parse.unquote(str(value or "")).lower()
    text = re.sub(r"\b(?:gmbh|ag|se|kg|co|ltd|inc|group|listing)\b", " ", text)
    text = re.sub(r"[^a-z0-9äöüß]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def job_fingerprint(title: str, company: str) -> str:
    title_norm = normalize_title_text(title)
    company_norm = normalize_company_text(company)
    if not title_norm:
        return ""
    return f"{company_norm}|{title_norm}" if company_norm else title_norm


def hostname(url: str) -> str:
    return urllib.parse.urlparse(url.strip()).netloc.lower().removeprefix("www.")


def host_matches(host: str, domains: set[str]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def looks_browser_blocked(body: str) -> bool:
    sample = strip_tags(body)[:2000].lower()
    return any(pattern in sample for pattern in BROWSER_BLOCK_PATTERNS)


def fetch_url_browser(url: str, timeout: int = 25) -> tuple[str, str]:
    marker_url = "__FRANKLEE_FINAL_URL__="
    marker_code = "__FRANKLEE_HTTP_CODE__="
    proc = subprocess.run(
        [
            "curl",
            "-sS",
            "-L",
            "--compressed",
            "--connect-timeout",
            "8",
            "--max-time",
            str(timeout),
            "-A",
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            ),
            "-H",
            "Accept-Language: en,de;q=0.9",
            "-H",
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "-H",
            "Upgrade-Insecure-Requests: 1",
            "-w",
            f"\n{marker_url}%{{url_effective}}\n{marker_code}%{{http_code}}\n",
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    output = proc.stdout or ""
    body = output
    final_url = url
    http_code = "000"
    if marker_url in output and marker_code in output:
        body, trailer = output.rsplit(f"\n{marker_url}", 1)
        final_url_line, _, code_part = trailer.partition(f"\n{marker_code}")
        final_url = final_url_line.strip() or url
        http_code = code_part.strip().splitlines()[0] if code_part.strip() else "000"
    if body.strip():
        return final_url, body
    if proc.returncode != 0:
        raise TimeoutError(proc.stderr.strip() or f"curl failed for {url}")
    raise urllib.error.HTTPError(final_url, int(http_code or "0"), f"HTTP {http_code}", hdrs=None, fp=None)


def fetch_url(url: str) -> tuple[str, str]:
    host = hostname(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FrankleeJobSearchPrefilter/1.0",
            "Accept-Language": "en,de;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            final_url = response.geturl()
            body = response.read().decode("utf-8", errors="replace")
        if host_matches(host, BROWSER_FALLBACK_DOMAINS) and looks_browser_blocked(body):
            return fetch_url_browser(url)
        return final_url, body
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        http.client.RemoteDisconnected,
        http.client.IncompleteRead,
    ):
        if host_matches(host, BROWSER_FALLBACK_DOMAINS):
            return fetch_url_browser(url)
        raise


def fetch_text_url(url: str, *, accept: str | None = None, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "FrankleeJobSearchPrefilter/1.0",
        "Accept-Language": "en,de;q=0.9",
    }
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_json_url(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FrankleeJobSearchPrefilter/1.0",
            "Accept": "application/vnd.github+json, application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def raw_candidate_score(candidate: Candidate, profile_name: str) -> int:
    url_norm = normalize_url(candidate.url)
    domain = url_norm.split("/", 1)[0]
    score = SOURCE_PRIORITIES.get(domain, 8)
    text = f"{candidate.title} {candidate.snippet}".lower()
    for keyword, points in ROLE_KEYWORDS.items():
        if keyword in text:
            score += points
    profile = get_profile(profile_name)
    for city in profile["city_scores"]:
        for alias in CITY_ALIASES.get(city, ()):
            if alias in text:
                score += 6
                break
    for pattern in profile["target_role_patterns"]:
        if pattern in text:
            score += 6
    if candidate.search_date:
        score += 3
    return score


def raw_candidate_reject_reason(candidate: Candidate, profile_name: str) -> str | None:
    parsed = urllib.parse.urlparse(candidate.url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = urllib.parse.unquote(parsed.path).lower()
    title_lower = candidate.title.lower()
    text = f"{candidate.title} {candidate.snippet} {candidate.url}".lower()

    for blocked_host, patterns in RAW_URL_REJECT_PATTERNS.items():
        if host == blocked_host and any(pattern in path for pattern in patterns):
            return "raw_search_results_url"

    if host.endswith("linkedin.com") and "/jobs/view/" not in path:
        return "raw_non_detail_url"
    if host == "jobs.lever.co" and len([part for part in path.split("/") if part]) < 2:
        return "raw_non_detail_url"
    if host == "boards.greenhouse.io" and len([part for part in path.split("/") if part]) < 2:
        return "raw_non_detail_url"
    if host == "jobs.ashbyhq.com" and len([part for part in path.split("/") if part]) < 3:
        return "raw_non_detail_url"
    if host == "jobs.personio.de" and "/job/" not in path:
        return "raw_non_detail_url"
    if host == "jobworld.de" and "traumjob" in text:
        return "raw_search_results_url"
    if host == "zenjob.com" and not any(pattern in text for pattern in TARGET_ROLE_PATTERNS):
        return "raw_search_results_url"
    if host == "jobs.sap.com" and path.startswith("/go/"):
        return "raw_non_detail_url"
    if host == "jobs.bosch.de" and not path.startswith(("/job/", "/en/job/")):
        return "raw_non_detail_url"
    if host == "jobs.bmwgroup.com" and not path.startswith("/job/"):
        return "raw_non_detail_url"
    if host == "jobs.schwarz" and "/job/" not in path:
        return "raw_non_detail_url"
    if host == "stepstone.de" and "stellenangebote" not in path:
        return "raw_non_detail_url"
    if host.endswith("findjob24h.com"):
        return "raw_search_results_url"

    if any(pattern in title_lower for pattern in ("jobs in", "stellenangebote", "suchergebnisse")):
        title_role_hit = any(pattern in title_lower for pattern in get_profile(profile_name)["target_role_patterns"])
        if not title_role_hit:
            return "raw_search_results_url"
    return None


def final_url_reject_reason(final_url: str) -> str | None:
    parsed = urllib.parse.urlparse(final_url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = urllib.parse.unquote(parsed.path).lower()
    query = urllib.parse.unquote(parsed.query).lower()
    if "expired_jd_redirect" in query:
        return "final_expired_redirect"
    if host.endswith("linkedin.com") and "/jobs/view/" not in path:
        return "final_non_detail_url"
    if host == "hays.de" and path.startswith("/jobprofile/"):
        return "final_generic_jobprofile"
    if host.endswith("findjob24h.com"):
        return "final_generic_scraper"
    return None


def strip_tags(html_text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", html_text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def extract_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
    return html.unescape(match.group(1)).strip() if match else ""


def load_jsonld_objects(html_text: str) -> list[dict[str, Any]]:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html_text,
        flags=re.I | re.S,
    )
    objects: list[dict[str, Any]] = []
    for raw in blocks:
        raw = html.unescape(raw).strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        stack = [parsed]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                objects.append(item)
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return objects


def pick_jobposting(jsonld_objects: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in jsonld_objects:
        t = item.get("@type")
        if t == "JobPosting":
            return item
        if isinstance(t, list) and "JobPosting" in t:
            return item
    return None


def parse_date_string(value: str | None, today: dt.date) -> dt.date | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None

    lower = text.lower()
    rel = re.search(r"(\d+)\s+days?\s+ago", lower)
    if rel:
        return today - dt.timedelta(days=int(rel.group(1)))
    rel = re.search(r"vor\s+(\d+)\s+tagen", lower)
    if rel:
        return today - dt.timedelta(days=int(rel.group(1)))
    rel = re.search(r"(\d+)\s+hours?\s+ago", lower)
    if rel:
        return today
    rel = re.search(r"vor\s+(\d+)\s+stunden", lower)
    if rel:
        return today

    date_patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
        r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            text = match.group(0)
            break

    try:
        parsed = date_parser.parse(text, fuzzy=True, dayfirst=True)
        return parsed.date()
    except Exception:
        return None


def extract_text_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(extract_text_value(v) for v in value)
    if isinstance(value, dict):
        return " ".join(extract_text_value(v) for v in value.values())
    return ""


def infer_work_model(text_lower: str) -> str:
    if "remote" in text_lower and "hybrid" in text_lower:
        return "Remote / Hybrid"
    if "remote" in text_lower:
        return "Remote possible"
    if "hybrid" in text_lower:
        return "Hybrid"
    if "on-site" in text_lower or "onsite" in text_lower or "vor ort" in text_lower:
        return "On-site"
    return "Not clearly stated"


LANGUAGE_NAMES = {
    "german": r"\b(?:german|deutsch(?:e|er|es|en)?|deutschkenntnisse)\b",
    "english": r"\b(?:english|englisch(?:e|er|es|en)?|englischkenntnisse)\b",
}
CEFR_PATTERN = re.compile(
    r"\b(?P<level>a1|a2|b1|b2|c1|c2)\s*(?P<plus>\+|plus)?"
    r"(?:\s+(?:language\s+)?(?:level|niveau))?(?:\s+of)?\s+(?:the\s+)?"
    r"(?P<language>german|deutsch|english|englisch)\b"
    r"|\b(?P<language_after>german|deutschkenntnisse|deutsch|english|englisch)\s*"
    r"(?:language\s*|level\s*|proficiency\s*|at\s+|auf\s+niveau\s+|auf\s+|niveau\s*)?(?:at\s+least\s+)?"
    r"(?P<level_after>a1|a2|b1|b2|c1|c2)\b\s*(?P<plus_after>\+|plus)?",
    re.I,
)
LANGUAGE_OPTIONAL_CUES = (
    "is a plus", "are a plus", "a plus", "nice to have", "welcome but not",
    "welcome, but not", "advantageous", "beneficial", "desirable", "preferred",
    "wünschenswert", "von vorteil", "vorteilhaft", "gerne gesehen", "kein muss",
    "kein muss-kriterium", "nicht zwingend erforderlich",
)
LANGUAGE_OPTIONAL_ONLY_CUES = ("optional", "optionally")
LANGUAGE_NOT_REQUIRED_CUES = (
    "not required", "not a requirement", "not mandatory", "not necessary",
    "not essential", "not needed", "not a must", "does not require", "no requirement", "isn't required",
    "nicht erforderlich", "nicht vorausgesetzt", "nicht notwendig", "keine voraussetzung",
    "not a prerequisite", "not needed for the role", "not necessary for the role",
    "keine pflicht", "kein muss", "nicht zwingend",
)
LANGUAGE_REQUIRED_CUES = (
    "required", "requirement", "must have", "must speak", "must be able", "working language",
    "mandatory", "essential", "minimum", "at least", "fluent", "business fluent",
    "very good", "excellent", "good knowledge", "good command", "strong command",
    "proficient", "verhandlungssicher", "fließend", "sehr gute kenntnisse",
    "gute kenntnisse", "gutes deutsch", "sehr gutes deutsch", "erforderlich",
    "vorausgesetzt", "muss", "sicheres deutsch",
)


def _language_sentences(text: str, language_pattern: str) -> list[str]:
    """Return bounded sentence-sized evidence, not a page-wide keyword verdict."""
    normalized = re.sub(r"\s+", " ", html.unescape(strip_tags(text or ""))).strip()
    chunks = re.split(r"(?<=[.!?])\s+|\s*[;|]\s+|\s{2,}", normalized)
    pattern = re.compile(language_pattern, re.I)
    found: list[str] = []
    for chunk in chunks:
        sentence = chunk.strip(" \t\r\n•-*|:")
        if sentence and pattern.search(sentence):
            sentence = sentence[:360]
            if sentence not in found:
                found.append(sentence)
    return found[:20]


def _classify_one_language(text: str, language: str) -> dict[str, Any]:
    evidence = _language_sentences(text, LANGUAGE_NAMES[language])
    if not evidence:
        return {"requirement": "not_mentioned", "cefr_level": None, "evidence": [], "needs_review": False}

    required_evidence: list[str] = []
    preferred_evidence: list[str] = []
    optional_evidence: list[str] = []
    not_required_evidence: list[str] = []
    unclear_evidence: list[str] = []
    cefr_levels: list[str] = []
    lang_aliases = {
        "german": ("german", "deutsch", "deutschkenntnisse"),
        "english": ("english", "englisch", "englischkenntnisse"),
    }[language]

    for sentence in evidence:
        lower = sentence.lower()
        level_match = CEFR_PATTERN.search(lower)
        if level_match:
            level = (level_match.group("level") or level_match.group("level_after") or "").upper()
            plus = level_match.group("plus") or level_match.group("plus_after") or ""
            level = f"{level}+" if plus else level
            matched_language = (level_match.group("language") or level_match.group("language_after") or "").lower()
            if matched_language in lang_aliases:
                cefr_levels.append(level)

        has_not_required = any(cue in lower for cue in LANGUAGE_NOT_REQUIRED_CUES) or bool(
            re.search(
                r"\b(?:no|kein|keine|keinen)\s+(?:need for\s+)?(?:german|deutsch\w*)\b"
                r"(?:\s+(?:language|kenntnisse))?\s*(?:is\s+)?(?:required|erforderlich|needed|necessary|vorausgesetzt|requirement)?\b",
                lower,
            )
        )
        has_preferred = any(cue in lower for cue in LANGUAGE_OPTIONAL_CUES)
        has_optional = any(cue in lower for cue in LANGUAGE_OPTIONAL_ONLY_CUES)
        has_required = not has_not_required and (any(cue in lower for cue in LANGUAGE_REQUIRED_CUES) or bool(
            re.search(
                r"\b(?:good|very good|excellent|fluent|business fluent|strong|proficient|sehr gut|gut|fließend|verhandlungssicher)"
                r"\s+(?:knowledge of\s+|command of\s+|in\s+)?(?:german|deutsch|english|englisch)\b"
                r"|\b(?:german|deutsch|english|englisch)(?:kenntnisse)?\s+(?:is\s+)?"
                r"(?:good|very good|excellent|fluent|business fluent|strong|proficient|sehr gut|gut|fließend|verhandlungssicher)\b",
                lower,
            )
        ))

        # Generic negative phrases apply only when their nearby clause also
        # contains the target language; sentence segmentation limits bleed.
        if has_required and (has_not_required or has_preferred or has_optional):
            required_evidence.append(sentence)
            if has_not_required:
                not_required_evidence.append(sentence)
            if has_preferred:
                preferred_evidence.append(sentence)
            if has_optional:
                optional_evidence.append(sentence)
        elif has_not_required:
            not_required_evidence.append(sentence)
        elif has_preferred:
            preferred_evidence.append(sentence)
        elif has_optional:
            optional_evidence.append(sentence)
        elif has_required or level_match:
            required_evidence.append(sentence)
        else:
            unclear_evidence.append(sentence)

    level = cefr_levels[0] if cefr_levels else None
    conflict = bool(required_evidence and (not_required_evidence or preferred_evidence or optional_evidence))
    if conflict:
        requirement, selected = "conflicting", required_evidence + not_required_evidence + preferred_evidence + optional_evidence
    elif required_evidence:
        requirement, selected = "required", required_evidence
    elif preferred_evidence:
        requirement, selected = "preferred", preferred_evidence
    elif optional_evidence:
        requirement, selected = "optional", optional_evidence
    elif not_required_evidence:
        requirement, selected = "not_required", not_required_evidence
    else:
        requirement, selected = "unclear", unclear_evidence or evidence

    return {
        "requirement": requirement,
        "cefr_level": level,
        "evidence": selected[:3],
        "needs_review": requirement in {"unclear", "conflicting"},
    }


def classify_language_requirements(text: str) -> dict[str, Any]:
    """Classify language requirements independently and retain auditable evidence."""
    return {
        "german": _classify_one_language(text, "german"),
        "english": _classify_one_language(text, "english"),
    }


def _language_note(classification: dict[str, Any]) -> str:
    german = classification["german"]
    english = classification["english"]
    requirement = german["requirement"]
    if requirement == "required":
        note = "German required" + (f" ({german['cefr_level']})" if german["cefr_level"] else "")
    elif requirement == "preferred":
        note = "German preferred"
    elif requirement == "optional":
        note = "German optional"
    elif requirement == "not_required":
        note = "German explicitly not required"
    elif requirement == "conflicting":
        note = "German requirement conflicting — review"
    elif requirement == "unclear":
        note = "German mentioned — unclear"
    elif english["requirement"] == "required":
        note = "English required; no German requirement found"
    else:
        note = "No explicit language requirement found"

    if english["requirement"] == "required" and requirement not in {"not_mentioned", "not_required"}:
        note += "; English also required"
    elif english["requirement"] == "required" and requirement == "not_mentioned":
        note = "English required; no German requirement found"
    if english["cefr_level"]:
        note += f" (English {english['cefr_level']})"
    return note


def assess_language(text: str) -> tuple[bool, str, str]:
    """Backward-compatible wrapper; uncertain language evidence stays reviewable."""
    classification = classify_language_requirements(text)
    german_requirement = classification["german"]["requirement"]
    note = _language_note(classification)
    bucket = "german_required" if german_requirement in {"required", "unclear", "conflicting"} else "main"
    return german_requirement != "required", note, bucket


def _language_evidence_summary(classification: dict[str, Any]) -> str:
    pieces = []
    for language in ("german", "english"):
        item = classification[language]
        if item["evidence"]:
            quote = re.sub(r"\s+", " ", item["evidence"][0]).strip()
            # Keep public posting text readable but prevent it from adding
            # Slack/Markdown links, emphasis, or multiline formatting.
            quote = re.sub(r"(?:https?://|www\.)\S+", "[link omitted]", quote, flags=re.I)
            quote = quote.replace("`", "'").replace("*", "").replace("_", "")
            quote = quote.replace("<", "(").replace(">", ")").replace("|", "/")
            pieces.append(f'{language.title()}: “{quote[:160]}”')
    return " | ".join(pieces)


def _language_display(item: dict[str, Any]) -> str:
    note = str(item.get("language_note") or "")
    evidence = str(item.get("language_evidence_summary") or "")
    return f"{note} — Evidence: {evidence}" if evidence else note


def looks_generic_page(final_url: str, title: str, text_lower: str, has_jobposting: bool) -> bool:
    if has_jobposting:
        return False
    parsed = urllib.parse.urlparse(final_url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = urllib.parse.unquote(parsed.path).lower()
    title_lower = title.lower()
    combined = f"{title_lower} {text_lower[:2500]}"
    if host == "stepstone.de" and re.search(r"--\d+-inline\.html$", path):
        return False
    if host == "jobware.de" and path.startswith("/job/"):
        return False
    if host in {"jobs.sap.com", "jobs.bmwgroup.com", "jobs.schwarz"}:
        if any(pattern in title_lower for pattern in TARGET_ROLE_PATTERNS):
            return False
    if any(pattern in title_lower for pattern in TARGET_ROLE_PATTERNS) and any(
        pattern in text_lower[:2500] for pattern in APPLY_PATTERNS
    ):
        return False
    return any(pattern in combined for pattern in GENERIC_PAGE_PATTERNS)


def looks_closed(text_lower: str) -> bool:
    return any(pattern in text_lower for pattern in CLOSED_PATTERNS)


def has_apply_signal(text_lower: str, has_jobposting: bool) -> bool:
    if has_jobposting:
        return True
    return any(pattern in text_lower for pattern in APPLY_PATTERNS)


def is_target_role(title: str, employment_type: str, description: str, profile_name: str) -> bool:
    profile = get_profile(profile_name)
    title_and_type = " ".join([title, employment_type])
    combined = " ".join([title, employment_type, description])
    title_and_type = re.sub(r"\s+", " ", title_and_type).lower()
    combined = re.sub(r"\s+", " ", combined).lower()
    if any(pattern in combined for pattern in profile["exclude_role_patterns"]):
        return False
    if profile_name == "student":
        if any(pattern in title_and_type for pattern in profile["target_role_patterns"]):
            return True
        if not title_and_type.strip():
            return any(pattern in combined for pattern in profile["target_role_patterns"])
        return False
    if any(pattern in combined for pattern in profile["target_role_patterns"]):
        return True
    return any(keyword in combined for keyword in ROLE_KEYWORDS)


def parse_location(jobposting: dict[str, Any], text: str) -> str:
    raw_location = jobposting.get("jobLocation")
    if isinstance(raw_location, list) and raw_location:
        raw_location = raw_location[0]
    if isinstance(raw_location, dict):
        address = raw_location.get("address") if isinstance(raw_location.get("address"), dict) else {}
        parts = [
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("addressCountry"),
        ]
        parts = [str(part).strip() for part in parts if part]
        if parts:
            return ", ".join(parts[:3])
    location = extract_text_value(raw_location)
    if location:
        location = re.sub(r"\s+", " ", location).strip()
        return location[:140]
    city = canonical_city_from_text(text)
    if not city:
        return "Germany"
    return f"{city}, DE"


def extract_job_country(jobposting: dict[str, Any]) -> str:
    raw_location = jobposting.get("jobLocation")
    if isinstance(raw_location, list) and raw_location:
        raw_location = raw_location[0]
    if isinstance(raw_location, dict):
        address = raw_location.get("address")
        if isinstance(address, dict):
            country = extract_text_value(address.get("addressCountry"))
            if country:
                return re.sub(r"\s+", " ", country).strip()
    return ""


def looks_like_germany_scope(country: str, geo_text: str) -> bool:
    country_lower = country.lower()
    if country_lower:
        return country_lower in GERMANY_COUNTRY_TERMS
    return any(term in geo_text for term in GERMANY_COUNTRY_TERMS)


def location_within_profile_scope(location: str, context_text: str, profile_name: str) -> bool:
    combined = f"{location} {context_text}".lower()
    if profile_name == "student":
        return any(pattern in combined for pattern in STUDENT_SCOPE_PATTERNS)
    if profile_name == "fulltime":
        if "berlin" in combined:
            return True
        if any(pattern in combined for pattern in FULLTIME_BLOCKED_SCOPE_PATTERNS):
            return False
        return any(pattern in combined for pattern in FULLTIME_ALLOWED_SCOPE_PATTERNS)
    return True


def score_candidate(
    title: str,
    location: str,
    work_model: str,
    domain: str,
    age_days: int | None,
    language_note: str,
    profile_name: str,
) -> int:
    score = SOURCE_PRIORITIES.get(domain, 12)
    profile = get_profile(profile_name)

    title_lower = title.lower()
    for keyword, points in ROLE_KEYWORDS.items():
        if keyword in title_lower:
            score += points

    city = canonical_city_from_text(location)
    if city:
        score += profile["city_scores"].get(city, 6)

    if "remote" in work_model.lower():
        score += 8
    elif "hybrid" in work_model.lower():
        score += 5

    if age_days is None:
        score += 2
    else:
        score += max(0, 20 - age_days)

    if language_note.startswith("English-friendly") or language_note.startswith("English required"):
        score += 8
    elif language_note.startswith("German preferred") or language_note.startswith("German optional") or language_note.startswith("German explicitly not required"):
        score += 6
    elif language_note.startswith("No explicit language requirement"):
        score += 5

    return score


def render_posted_label(item: dict[str, Any]) -> str:
    posted_date = item.get("posted_date")
    age_days = item.get("age_days")
    if not posted_date:
        return "Date not found"
    if age_days is None:
        return str(posted_date)
    return f"{posted_date} ({age_days}d ago)"


def choose_display_title(jobposting_title: str, candidate_title: str, title_tag: str) -> str:
    for value in (jobposting_title, candidate_title, title_tag):
        title = re.sub(r"\s+", " ", str(value or "")).strip()
        if not title:
            continue
        if re.fullmatch(r"\d{6,}", title):
            continue
        return title
    return re.sub(r"\s+", " ", str(candidate_title or title_tag or jobposting_title or "")).strip()


def company_from_jobposting(jobposting: dict[str, Any], domain: str) -> str:
    hiring = jobposting.get("hiringOrganization")
    if isinstance(hiring, dict):
        name = str(hiring.get("name") or "").strip()
        if name:
            return name[:120]
    name = extract_text_value(hiring)
    if name:
        return re.sub(r"\s+", " ", name).strip()[:120]
    return DOMAIN_COMPANY_FALLBACKS.get(domain, domain)


def candidate_from_payload(
    *,
    query: str,
    url: Any,
    title: Any,
    snippet: Any = "",
    source: Any = "",
    search_date: Any = "",
) -> Candidate | None:
    if not isinstance(url, str) or not url.startswith("http"):
        return None
    return Candidate(
        query=query,
        title=str(title or ""),
        url=url,
        snippet=str(snippet or ""),
        source=str(source or ""),
        search_date=str(search_date or ""),
    )


def query_serpapi(query: str, num: int) -> list[Candidate]:
    env = build_provider_env()

    if SERPAPI_FALLBACK_PATH.exists():
        proc = subprocess.run(
            [
                "python3",
                str(SERPAPI_FALLBACK_PATH),
                query,
                "--num",
                str(num),
                "--gl",
                "de",
                "--hl",
                "en",
                "--freshness",
                "month",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        data = json.loads(proc.stdout)
        results: list[Candidate] = []
        for item in data.get("results", []):
            candidate = candidate_from_payload(
                query=query,
                url=item.get("url"),
                title=item.get("title"),
                snippet=item.get("snippet"),
                source=item.get("source"),
                search_date=item.get("date"),
            )
            if candidate:
                results.append(candidate)
        return results

    api_key = env.get("SERPAPI_API_KEY") or env.get("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("Missing SerpAPI key and no serpapi_fallback.py is available")

    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "num": str(num),
            "gl": "de",
            "hl": "en",
            "api_key": api_key,
        }
    )
    req = urllib.request.Request(
        f"https://serpapi.com/search.json?{params}",
        headers={"User-Agent": "FrankleeJobPrefilter/1.0"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))

    results: list[Candidate] = []
    for item in data.get("organic_results", []):
        candidate = candidate_from_payload(
            query=query,
            url=item.get("link"),
            title=item.get("title"),
            snippet=item.get("snippet"),
            source="serpapi_http",
            search_date=item.get("date"),
        )
        if candidate:
            results.append(candidate)
    return results


def query_exa(query: str, num: int) -> list[Candidate]:
    if not EXA_SEARCH_PATH.exists():
        raise RuntimeError("Missing exa_search.py")
    proc = subprocess.run(
        [
            "python3",
            str(EXA_SEARCH_PATH),
            "--query",
            query,
            "--type",
            "auto",
            "--num-results",
            str(max(1, min(num, 10))),
            "--content-mode",
            "highlights",
            "--timeout",
            "25",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=build_provider_env(),
    )
    data = json.loads(proc.stdout)
    results: list[Candidate] = []
    for item in data.get("results", []):
        candidate = candidate_from_payload(
            query=query,
            url=item.get("url"),
            title=item.get("title"),
            snippet=item.get("snippet"),
            source=item.get("provider") or "exa",
            search_date=item.get("published_at"),
        )
        if candidate:
            results.append(candidate)
    return results


def likely_job_url(url: str) -> bool:
    text = urllib.parse.unquote(url).lower()
    return any(
        token in text
        for token in (
            "/job",
            "/jobs",
            "/careers",
            "/career",
            "stellen",
            "karriere",
            "vacancy",
            "position",
            "reqid",
            "jobid",
        )
    )


def direct_url_text(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    pieces = [parsed.netloc, urllib.parse.unquote(parsed.path), urllib.parse.unquote(parsed.query)]
    return re.sub(r"[^a-z0-9äöüß]+", " ", " ".join(pieces).lower())


def direct_url_score(url: str, profile_name: str, domain: str) -> int:
    text = direct_url_text(url)
    score = SOURCE_PRIORITIES.get(domain, 10) + 8
    for keyword, points in ROLE_KEYWORDS.items():
        if slug(keyword) in text.replace(" ", "-") or keyword in text:
            score += max(5, points // 2)
    profile = get_profile(profile_name)
    for pattern in profile["target_role_patterns"]:
        if pattern in text:
            score += 12
    for pattern in profile["exclude_role_patterns"]:
        if pattern in text:
            score -= 60
    if profile_name == "student":
        if any(pattern in text for pattern in STUDENT_SCOPE_PATTERNS):
            score += 8
    else:
        if any(pattern in text for pattern in ("germany", "deutschland", "remote", "bundesweit")):
            score += 4
    if any(pattern in text for pattern in FOREIGN_LOCATION_PATTERNS):
        score -= 40
    return score


def parse_sitemap(xml_text: str) -> tuple[list[str], list[str]]:
    urls: list[str] = []
    nested: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls, nested
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag != "loc" or not element.text:
            continue
        value = element.text.strip()
        if "<sitemapindex" in xml_text[:200].lower():
            nested.append(value)
        else:
            urls.append(value)
    return urls, nested


def crawl_direct_source(source_domain: str, sitemap_url: str, profile_name: str, limit: int) -> list[Candidate]:
    queue = [sitemap_url]
    visited: set[str] = set()
    candidates: list[tuple[int, Candidate]] = []
    while queue and len(visited) < 8 and len(candidates) < limit * 3:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        try:
            xml_text = fetch_text_url(current, accept="application/xml,text/xml,*/*", timeout=18)
        except Exception:
            continue
        urls, nested = parse_sitemap(xml_text)
        for child in nested[:12]:
            if child not in visited:
                queue.append(child)
        for url in urls:
            parsed = urllib.parse.urlparse(url)
            if source_domain not in parsed.netloc.lower():
                continue
            if not likely_job_url(url):
                continue
            score = direct_url_score(url, profile_name, source_domain)
            if score <= 0:
                continue
            title = re.sub(r"[-_/]+", " ", Path(parsed.path).name or parsed.path).strip()
            candidates.append(
                (
                    score,
                    Candidate(
                        query=f"direct:{source_domain}",
                        title=title[:160],
                        url=url,
                        snippet=f"Direct sitemap candidate from {source_domain}",
                        source=f"direct_sitemap:{source_domain}",
                        search_date="",
                    ),
                )
            )
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in candidates[:limit]]


def crawl_direct_sources(profile_name: str, limit_per_source: int = 10) -> list[Candidate]:
    results: list[Candidate] = []
    for domain, sitemap_url in DIRECT_SOURCE_SITEMAPS.items():
        results.extend(crawl_direct_source(domain, sitemap_url, profile_name, limit_per_source))
    return results


def load_applied(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    urls = set()
    for item in data:
        url = item.get("job_url") or item.get("normalized_url")
        if isinstance(url, str) and url.strip():
            urls.add(normalize_url(url))
    return urls


def refresh_applied_from_github(path: Path) -> dict[str, Any]:
    try:
        listing = fetch_json_url(GITHUB_INTAKES_API_URL)
        if not isinstance(listing, list):
            raise ValueError("GitHub intakes listing did not return a file list")

        refreshed: list[dict[str, Any]] = []
        for item in listing:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "file":
                continue
            name = str(item.get("name") or "")
            if not name.endswith(".json"):
                continue
            download_url = str(item.get("download_url") or "")
            if not download_url:
                continue
            try:
                intake = fetch_json_url(download_url)
            except Exception:
                continue
            if not isinstance(intake, dict):
                continue
            job_url = intake.get("job_url")
            if not isinstance(job_url, str) or not job_url.startswith("http"):
                continue
            refreshed.append(
                {
                    "source_file": f"{GITHUB_REPO_BLOB_PREFIX}{name}",
                    "company_name": intake.get("company_name") or intake.get("company"),
                    "job_title": intake.get("job_title") or intake.get("title"),
                    "job_url": job_url,
                    "language": intake.get("language"),
                    "primary_role": intake.get("primary_role"),
                }
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(refreshed, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)
        return {"ok": True, "count": len(refreshed), "source": "github"}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "source": "github"}


def load_recent_urls(runs_path: Path, days: int, now_ms: int) -> set[str]:
    if not runs_path.exists():
        return set()
    cutoff = now_ms - days * 24 * 60 * 60 * 1000
    urls: set[str] = set()
    for line in runs_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("runAtMs", 0) < cutoff:
            continue
        summary = str(row.get("summary") or "")
        for url in re.findall(r"https?://[^\s)>]+", summary):
            urls.add(normalize_url(url.rstrip(".,`")))
    return urls


def is_truncated_summary_url(url: str) -> bool:
    return "…" in url or "\\u2026" in url or "%E2%80%A6" in url.upper()


def extract_urls_from_summary(summary: str) -> set[str]:
    return {
        normalize_url(url.rstrip(".,`"))
        for url in re.findall(r"https?://[^\s)>]+", summary)
        if not is_truncated_summary_url(url)
    }


def extract_fingerprints_from_summary(summary: str) -> set[str]:
    fingerprints: set[str] = set()
    pattern = re.compile(r"^- \*{1,2}(.*?)\*{1,2} — \*{1,2}(.*?)\*{1,2}", flags=re.MULTILINE)
    for title, company in pattern.findall(summary):
        fingerprint = job_fingerprint(title, company)
        if fingerprint:
            fingerprints.add(fingerprint)
    return fingerprints


def recent_history_sources(runs_path: Path) -> list[Path]:
    sources: list[Path] = []
    candidates = [
        runs_path,
        runs_path.with_name(f"{runs_path.name}.migrated"),
        runs_path.with_suffix(f"{runs_path.suffix}.migrated") if runs_path.suffix else runs_path.with_name(f"{runs_path.name}.migrated"),
    ]
    for path in candidates:
        if path.exists() and path not in sources:
            sources.append(path)

    recovery_dir = OPENCLAW_HOME / "manual-recovery"
    if recovery_dir.exists():
        for path in sorted(recovery_dir.glob("job-search-*.md")):
            if path not in sources:
                sources.append(path)
    return sources


def history_signature(sources: list[Path]) -> list[dict[str, Any]]:
    signature: list[dict[str, Any]] = []
    for path in sources:
        try:
            stat = path.stat()
        except OSError:
            continue
        signature.append(
            {
                "path": str(path),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    return signature


def extract_run_at_ms_from_recovery_path(path: Path, fallback_ms: int) -> int:
    match = re.search(r"job-search-(\d{4})-(\d{2})-(\d{2})", path.name)
    if not match:
        return fallback_ms
    try:
        date = dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        noon_utc = dt.datetime.combine(date, dt.time(12, 0), tzinfo=dt.timezone.utc)
        return int(noon_utc.timestamp() * 1000)
    except Exception:
        return fallback_ms


def refresh_recent_urls_cache(
    runs_path: Path,
    cache_path: Path,
    days: int,
    now_ms: int,
) -> tuple[set[str], set[str], dict[str, Any]]:
    cutoff = now_ms - days * 24 * 60 * 60 * 1000
    sources = recent_history_sources(runs_path)
    source_signature = history_signature(sources)
    source_size = sum(item["size"] for item in source_signature)
    entries: dict[str, int] = {}
    fingerprint_entries: dict[str, int] = {}
    mode = "rebuilt"

    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            if (
                isinstance(cache, dict)
                and cache.get("source_path") == str(runs_path)
                and cache.get("source_signature") == source_signature
                and isinstance(cache.get("entries"), list)
                and isinstance(cache.get("fingerprints"), list)
            ):
                for item in cache["entries"]:
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url")
                    last_seen = item.get("last_seen_run_at_ms")
                    if isinstance(url, str) and isinstance(last_seen, int) and last_seen >= cutoff:
                        entries[url] = max(entries.get(url, 0), last_seen)
                for item in cache["fingerprints"]:
                    if not isinstance(item, dict):
                        continue
                    fingerprint = item.get("fingerprint")
                    last_seen = item.get("last_seen_run_at_ms")
                    if isinstance(fingerprint, str) and isinstance(last_seen, int) and last_seen >= cutoff:
                        fingerprint_entries[fingerprint] = max(fingerprint_entries.get(fingerprint, 0), last_seen)
                mode = "cache_hit"
        except Exception:
            entries = {}
            fingerprint_entries = {}
            mode = "rebuilt"

    if mode != "cache_hit":
        entries = {}
        fingerprint_entries = {}
        for source in sources:
            if source.suffix == ".md":
                try:
                    summary = source.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                run_at_ms = extract_run_at_ms_from_recovery_path(source, now_ms)
                if run_at_ms < cutoff:
                    continue
                for url in extract_urls_from_summary(summary):
                    entries[url] = max(entries.get(url, 0), run_at_ms)
                for fingerprint in extract_fingerprints_from_summary(summary):
                    fingerprint_entries[fingerprint] = max(fingerprint_entries.get(fingerprint, 0), run_at_ms)
                continue
            for raw_line in source.read_bytes().splitlines():
                try:
                    row = json.loads(raw_line.decode("utf-8", errors="replace"))
                except Exception:
                    continue
                run_at_ms = row.get("runAtMs", 0)
                if not isinstance(run_at_ms, int) or run_at_ms < cutoff:
                    continue
                summary = str(row.get("summary") or "")
                for url in extract_urls_from_summary(summary):
                    entries[url] = max(entries.get(url, 0), run_at_ms)
                for fingerprint in extract_fingerprints_from_summary(summary):
                    fingerprint_entries[fingerprint] = max(fingerprint_entries.get(fingerprint, 0), run_at_ms)

    entries = {url: ts for url, ts in entries.items() if ts >= cutoff}
    fingerprint_entries = {fp: ts for fp, ts in fingerprint_entries.items() if ts >= cutoff}
    cache_payload = {
        "updated_at_ms": now_ms,
        "dedupe_days": days,
        "source_path": str(runs_path),
        "source_size": source_size,
        "source_signature": source_signature,
        "entries": [
            {"url": url, "last_seen_run_at_ms": ts}
            for url, ts in sorted(entries.items(), key=lambda item: (-item[1], item[0]))
        ],
        "fingerprints": [
            {"fingerprint": fingerprint, "last_seen_run_at_ms": ts}
            for fingerprint, ts in sorted(fingerprint_entries.items(), key=lambda item: (-item[1], item[0]))
        ],
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_name(f"{cache_path.name}.{os.getpid()}.{now_ms}.tmp")
    tmp_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(cache_path)
    return set(entries.keys()), set(fingerprint_entries.keys()), {
        "mode": mode,
        "count": len(entries),
        "fingerprint_count": len(fingerprint_entries),
        "cache_path": str(cache_path),
        "source_count": len(sources),
    }


def validate_candidate(candidate: Candidate, today: dt.date, max_age_days: int, profile_name: str) -> dict[str, Any] | None:
    def description_excerpt(value: str) -> str:
        plain = strip_tags(value or "")
        return re.sub(r"\s+", " ", html.unescape(plain)).strip()[:1200]

    def linkedin_discovery_or_reject(reason: str, url: str) -> dict[str, Any]:
        """Keep a public LinkedIn detail URL as an explicitly unverified lead.

        LinkedIn often blocks lightweight server requests.  Those blocks do not
        establish that a result is closed, so preserve role/location/date facts
        available from the search provider for manual opening instead of silently
        converting the lead into a fetch failure.
        """
        title = choose_display_title("", candidate.title, "")
        context = " ".join([title, candidate.snippet, candidate.url])
        context_lower = context.lower()
        posted_date = parse_date_string(candidate.search_date, today)
        age_days = (today - posted_date).days if posted_date else None
        if age_days is not None and (age_days < 0 or age_days > max_age_days):
            return {"reject_reason": "stale", "url": url, "age_days": age_days}
        if any(pattern in context_lower for pattern in FOREIGN_LOCATION_PATTERNS):
            return {"reject_reason": "outside_germany", "url": url}
        if not is_target_role(title, "", candidate.snippet, profile_name):
            return {"reject_reason": "not_target_role", "url": url, "title": title}
        location = parse_location({}, context_lower)
        if not location_within_profile_scope(location, context_lower, profile_name):
            return {"reject_reason": "outside_profile_scope", "url": url, "location": location}
        language_classification = classify_language_requirements(context)
        language_note = _language_note(language_classification)
        german_requirement = language_classification["german"]["requirement"]
        language_bucket = "german_required" if german_requirement in {"required", "unclear", "conflicting"} else "main"
        return {
            "title": title,
            "company": "LinkedIn listing",
            "location": location,
            "work_model": infer_work_model(context_lower),
            "posted_date": posted_date.isoformat() if posted_date else None,
            "age_days": age_days,
            "date_status": "found" if posted_date else "missing",
            "url": url,
            "normalized_url": normalize_url(url),
            "domain": hostname(url),
            "language_note": language_note,
            "language_bucket": language_bucket,
            "german_language": language_classification["german"],
            "english_language": language_classification["english"],
            "language_evidence_summary": _language_evidence_summary(language_classification),
            "score": score_candidate(title, location, "Not clearly stated", hostname(url), age_days, language_note, profile_name),
            "why_match": "LinkedIn discovery lead; manual review required",
            "listing_status": f"LinkedIn discovery-only ({reason}); open manually",
            "description_excerpt": description_excerpt(candidate.snippet),
        }

    is_linkedin_detail = hostname(candidate.url).endswith("linkedin.com") and "/jobs/view/" in urllib.parse.urlparse(candidate.url).path
    try:
        final_url, body = fetch_url(candidate.url)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        http.client.RemoteDisconnected,
        http.client.IncompleteRead,
    ):
        if is_linkedin_detail:
            return linkedin_discovery_or_reject("automated page check unavailable", candidate.url)
        return {"reject_reason": "fetch_failed", "url": candidate.url}

    final_norm = normalize_url(final_url)
    final_url_reason = final_url_reject_reason(final_url)
    if final_url_reason:
        return {"reject_reason": final_url_reason, "url": final_url}

    title_tag = extract_title(body)
    text = strip_tags(body)
    text_lower = text.lower()

    jsonld_objects = load_jsonld_objects(body)
    jobposting = pick_jobposting(jsonld_objects) or {}
    has_jobposting = bool(jobposting)

    if looks_generic_page(final_url, title_tag, text_lower, has_jobposting):
        if is_linkedin_detail:
            return linkedin_discovery_or_reject("automated page check unavailable", final_url)
        return {"reject_reason": "generic_page", "url": final_url}
    if looks_closed(text_lower):
        return {"reject_reason": "closed", "url": final_url}
    if not has_apply_signal(text_lower, has_jobposting):
        if is_linkedin_detail:
            return linkedin_discovery_or_reject("automated page check unavailable", final_url)
        return {"reject_reason": "no_apply_signal", "url": final_url}

    date_candidates = [
        extract_text_value(jobposting.get("datePosted")),
        candidate.search_date,
        title_tag,
        text[:1200],
    ]
    posted_date = None
    for date_value in date_candidates:
        posted_date = parse_date_string(date_value, today)
        if posted_date:
            break
    age_days = (today - posted_date).days if posted_date else None
    if age_days is not None and (age_days < 0 or age_days > max_age_days):
        return {"reject_reason": "stale", "url": final_url, "age_days": age_days}

    description_text = extract_text_value(jobposting.get("description"))
    qualifications_text = extract_text_value(jobposting.get("qualifications"))
    # Prefer the structured job description and qualifications. Fall back to
    # rendered page text only when the posting lacks structured content.
    language_source = " ".join(part for part in (description_text, qualifications_text) if part).strip()
    if not language_source:
        language_source = text
    language_classification = classify_language_requirements(language_source)
    language_note = _language_note(language_classification)
    german_requirement = language_classification["german"]["requirement"]
    language_bucket = "german_required" if german_requirement in {"required", "unclear", "conflicting"} else "main"
    language_ok = german_requirement != "required"
    if not language_ok and language_bucket != "german_required":
        return {"reject_reason": "language", "url": final_url}

    domain = urllib.parse.urlparse(final_url).netloc.lower().removeprefix("www.")
    company = company_from_jobposting(jobposting, domain)
    title = choose_display_title(extract_text_value(jobposting.get("title")), candidate.title, title_tag)
    employment_type = extract_text_value(jobposting.get("employmentType"))
    country = extract_job_country(jobposting)
    geo_context = " ".join([title, candidate.snippet, final_url, description_text[:800], text_lower[:1200]]).lower()
    if country and not looks_like_germany_scope(country, geo_context):
        return {"reject_reason": "outside_germany", "url": final_url, "country": country}
    if any(pattern in geo_context for pattern in FOREIGN_LOCATION_PATTERNS) and not looks_like_germany_scope(country, geo_context):
        return {"reject_reason": "outside_germany", "url": final_url}
    if not is_target_role(title, employment_type, f"{description_text} {text_lower[:2000]}", profile_name):
        return {"reject_reason": "not_target_role", "url": final_url, "title": re.sub(r"\s+", " ", title).strip()}
    location = parse_location(jobposting, text_lower)
    if not location_within_profile_scope(location, geo_context, profile_name):
        return {"reject_reason": "outside_profile_scope", "url": final_url, "location": location}
    work_model = infer_work_model(
        " ".join(
            [
                text_lower[:3000],
                employment_type.lower(),
                description_text.lower(),
            ]
        )
    )
    score = score_candidate(title, location, work_model, domain, age_days, language_note, profile_name)

    why = []
    title_lower = title.lower()
    for keyword in [
        "business analyst",
        "product owner",
        "product management",
        "requirements",
        "process",
        "project management",
        "testing",
        "compliance",
        "digitalisation",
        "digitalization",
        "quality",
    ]:
        if keyword in title_lower:
            why.append(keyword)
    if not why:
        why.append("general profile fit")

    return {
        "title": re.sub(r"\s+", " ", title).strip(),
        "company": company,
        "location": location,
        "work_model": work_model,
        "posted_date": posted_date.isoformat() if posted_date else None,
        "age_days": age_days,
        "date_status": "found" if posted_date else "missing",
        "url": final_url,
        "normalized_url": final_norm,
        "domain": domain,
        "language_note": language_note,
        "language_bucket": language_bucket,
        "german_language": language_classification["german"],
        "english_language": language_classification["english"],
        "language_evidence_summary": _language_evidence_summary(language_classification),
        "score": score,
        "why_match": ", ".join(why[:3]),
        "description_excerpt": description_excerpt(description_text),
    }


def render_markdown(
    results: list[dict[str, Any]],
    max_age_days: int,
    profile_name: str,
    analytics: dict[str, Any] | None = None,
) -> str:
    today = dt.date.today().isoformat()
    profile = get_profile(profile_name)
    lines = [
        f"{profile['heading']} — Validated Shortlist ({today})",
        "",
        (
            f"Rules applied: URL live, application open, age <= {max_age_days} days, target role only "
            f"({profile['role_summary']}), German-heavy roles routed separately, no recent repeats, "
            "not already applied."
        ),
        f"Scope: {profile['scope_note']}",
        "Main shortlist prioritizes English-first, optional-German, and no-explicit-German roles; required, unclear, or conflicting German evidence is separated for review.",
        "",
    ]
    if not results:
        lines.append("No high-confidence matches passed the validator today.")
        return "\n".join(lines)

    main_results = [item for item in results if item.get("language_bucket") != "german_required"]
    german_required_results = [item for item in results if item.get("language_bucket") == "german_required"]

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in main_results:
        grouped.setdefault(render_city_bucket(item), []).append(item)

    ordered_buckets = [bucket for bucket in profile["output_order"] if bucket in grouped]
    for bucket in sorted(grouped):
        if bucket not in ordered_buckets:
            ordered_buckets.append(bucket)

    for bucket in ordered_buckets:
        lines.append(f"## {render_city_label(bucket)}")
        for item in grouped[bucket]:
            lines.append(
                f"- **{item['title']}** — **{item['company']}** — {item['location']} — "
                f"Work model: {item['work_model']} — Posted: {render_posted_label(item)} — "
                f"Language: {_language_display(item)} — Why it matches: {item['why_match']} — Apply: <{item['url']}>"
            )
        lines.append("")

    if german_required_results:
        lines.append("## German-Required or Language-Needs-Review Roles")
        lines.append(
            "Roles with an explicit German requirement and postings whose language wording is unclear or conflicting are separated here. Check the quoted evidence and stated level before deciding."
        )
        lines.append("")
        for item in german_required_results:
            lines.append(
                f"- **{item['title']}** — **{item['company']}** — {item['location']} — "
                f"Work model: {item['work_model']} — Posted: {render_posted_label(item)} — "
                f"Language: {_language_display(item)} — Why it matches: {item['why_match']} — Apply: <{item['url']}>"
            )
        lines.append("")

    if analytics:
        reject_counts = analytics.get("reject_counts") or {}
        reject_summary = ", ".join(f"{key}={value}" for key, value in sorted(reject_counts.items())) or "none"
        provider_summary = []
        for name, info in (analytics.get("providers") or {}).items():
            provider_summary.append(
                f"{name}:ready={info.get('ready')},queries={info.get('queries', 0)},results={info.get('results', 0)},errors={len(info.get('errors') or [])}"
            )
        lines.extend(
            [
                "",
                "Analytics:",
                f"- Profile: {analytics.get('profile', DEFAULT_PROFILE)}",
                f"- Discovery queries: {analytics.get('query_count', 0)}",
                f"- Discovery providers: {'; '.join(provider_summary) if provider_summary else 'n/a'}",
                f"- Applied jobs synced: {analytics.get('applied_jobs_count', 0)}",
                f"- Recent-posted cache: {analytics.get('recent_cache_count', 0)} ({analytics.get('recent_cache_mode', 'n/a')})",
                f"- Raw discovered: {analytics.get('raw_candidates', 0)}",
                f"- Unique after dedupe: {analytics.get('unique_candidates', 0)}",
                f"- Page-validated inputs: {analytics.get('validated_inputs', 0)}",
                f"- Passed validator: {analytics.get('validated_count', 0)}",
                f"- Main shortlist: {analytics.get('main_results', len(main_results))}",
                f"- German-required / language-review shortlist: {analytics.get('german_required_results', len(german_required_results))}",
                f"- Posted now: {analytics.get('final_results', 0)}",
                f"- Reject breakdown: {reject_summary}",
            ]
        )
    return "\n".join(lines)


LANGUAGE_SORT_ORDER = {
    "required": 10,
    "conflicting": 9,
    "unclear": 8,
    "preferred": 3,
    "optional": 2,
    "not_required": 2,
    "not_mentioned": 1,
}


def language_sort_rank(item: dict[str, Any]) -> int:
    german = item.get("german_language")
    if isinstance(german, dict):
        return LANGUAGE_SORT_ORDER.get(str(german.get("requirement") or ""), 5)
    return 10 if item.get("language_bucket") == "german_required" else 5


def result_sort_key(item: dict[str, Any]) -> tuple[int, int, int, int, str, str]:
    age_days = item.get("age_days")
    return (
        language_sort_rank(item),
        int(item.get("_ai_priority") or 0),
        -int(item.get("score") or 0),
        int(age_days) if isinstance(age_days, int) else 999,
        str(item.get("company") or ""),
        str(item.get("title") or ""),
    )


def run_profile_json(
    *,
    profile_name: str,
    max_age_days: int,
    per_query: int,
    max_validate: int,
    runs_path: str | None,
    recent_cache: str | None,
) -> list[dict[str, Any]]:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--profile",
        profile_name,
        "--max-age-days",
        str(max_age_days),
        "--per-query",
        str(per_query),
        "--max-validate",
        str(max_validate),
        "--max-results",
        "0",
        "--format",
        "json",
    ]
    if runs_path:
        cmd.extend(["--runs-path", runs_path])
    if recent_cache:
        cmd.extend(["--recent-cache", recent_cache])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    return data if isinstance(data, list) else []


def provider_readiness() -> dict[str, bool]:
    loaded_env = build_provider_env()
    serpapi_ready = SERPAPI_FALLBACK_PATH.exists() or bool(
        loaded_env.get("SERPAPI_API_KEYS")
        or loaded_env.get("SERPAPI_API_KEY")
        or loaded_env.get("SERPAPI_KEY")
    )
    exa_ready = EXA_SEARCH_PATH.exists() and bool(loaded_env.get("EXA_API_KEY"))
    direct_ready = bool(DIRECT_SOURCE_SITEMAPS)
    return {
        "serpapi": serpapi_ready,
        "exa": exa_ready,
        "direct": direct_ready,
    }


def discover_profile_candidates(profile_name: str, per_query: int, readiness: dict[str, bool]) -> dict[str, Any]:
    raw_candidates: list[Candidate] = []
    discovery_queries = build_discovery_queries(profile_name)
    provider_stats: dict[str, dict[str, Any]] = {
        "serpapi": {"ready": readiness.get("serpapi", False), "queries": 0, "results": 0, "errors": []},
        "exa": {"ready": readiness.get("exa", False), "queries": 0, "results": 0, "errors": []},
        "direct": {"ready": readiness.get("direct", False), "queries": 0, "results": 0, "errors": []},
    }

    for query in discovery_queries:
        if readiness.get("serpapi"):
            provider_stats["serpapi"]["queries"] += 1
            try:
                results = query_serpapi(query, per_query)
                provider_stats["serpapi"]["results"] += len(results)
                raw_candidates.extend(results)
            except Exception as exc:
                provider_stats["serpapi"]["errors"].append(str(exc)[:180])
        if readiness.get("exa"):
            provider_stats["exa"]["queries"] += 1
            try:
                results = query_exa(query, max(4, min(per_query, 8)))
                provider_stats["exa"]["results"] += len(results)
                raw_candidates.extend(results)
            except Exception as exc:
                provider_stats["exa"]["errors"].append(str(exc)[:180])

    if readiness.get("direct"):
        provider_stats["direct"]["queries"] = len(DIRECT_SOURCE_SITEMAPS)
        try:
            direct_results = crawl_direct_sources(profile_name, limit_per_source=max(8, per_query))
            provider_stats["direct"]["results"] = len(direct_results)
            raw_candidates.extend(direct_results)
        except Exception as exc:
            provider_stats["direct"]["errors"].append(str(exc)[:180])

    return {
        "profile": profile_name,
        "query_count": len(discovery_queries),
        "per_query": per_query,
        "raw_candidates": raw_candidates,
        "providers": provider_stats,
    }


def candidate_profile_score(record: dict[str, Any], profile_name: str) -> int:
    scores = record.get("scores") or {}
    score = scores.get(profile_name)
    return int(score) if isinstance(score, int) else -9999


def choose_combined_validation_profile(record: dict[str, Any]) -> str:
    candidate = record["candidate"]
    profiles = set(record.get("profiles") or ())
    text = f"{candidate.title} {candidate.snippet} {candidate.url}".lower()
    if "student" in profiles and any(pattern in text for pattern in STUDENT_TARGET_ROLE_PATTERNS):
        return "student"
    if "fulltime" in profiles and any(pattern in text for pattern in FULLTIME_TARGET_PATTERNS):
        return "fulltime"
    return max(profiles, key=lambda profile_name: candidate_profile_score(record, profile_name))


def combined_provider_summary(profile_discovery: dict[str, dict[str, Any]]) -> dict[str, Any]:
    providers: dict[str, Any] = {}
    for profile_name, data in profile_discovery.items():
        providers[profile_name] = data.get("providers") or {}
    return providers


def split_language(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    main = [item for item in results if item.get("language_bucket") != "german_required"]
    german = [item for item in results if item.get("language_bucket") == "german_required"]
    return sorted(main, key=result_sort_key), sorted(german, key=result_sort_key)


def append_grouped_results(
    lines: list[str],
    results: list[dict[str, Any]],
    profile_name: str,
    *,
    bucket_heading: str = "###",
) -> None:
    if not results:
        lines.append("No high-confidence matches passed this section today.")
        lines.append("")
        return

    profile = get_profile(profile_name)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        grouped.setdefault(render_city_bucket(item), []).append(item)

    ordered_buckets = [bucket for bucket in profile["output_order"] if bucket in grouped]
    for bucket in sorted(grouped):
        if bucket not in ordered_buckets:
            ordered_buckets.append(bucket)

    for bucket in ordered_buckets:
        lines.append(f"{bucket_heading} {render_city_label(bucket)}")
        for item in sorted(grouped[bucket], key=result_sort_key):
            listing_status = item.get("listing_status")
            action = "Open manually" if listing_status else "Apply"
            status_note = f" — Listing status: {listing_status}" if listing_status else ""
            lines.append(
                f"- **{item['title']}** — **{item['company']}** — {item['location']} — "
                f"Work model: {item['work_model']} — Posted: {render_posted_label(item)} — "
                f"Language: {_language_display(item)} — Why it matches: {item['why_match']}{status_note} — {action}: <{item['url']}>"
            )
        lines.append("")


def render_combined_1500(
    *,
    student_results: list[dict[str, Any]],
    fulltime_results: list[dict[str, Any]],
    max_age_days: int,
    analytics: dict[str, Any] | None = None,
) -> str:
    today = dt.date.today()
    student_display = sorted(student_results, key=result_sort_key)[:7]
    fulltime_display = sorted(fulltime_results, key=result_sort_key)[:9]
    student_german_count = sum(1 for item in student_display if item.get("language_bucket") == "german_required")
    fulltime_german_count = sum(1 for item in fulltime_display if item.get("language_bucket") == "german_required")

    lines = [
        f"Daily Germany Job Search — Combined Validated Shortlist ({today})",
        "",
        (
            f"Rules applied: official-source roles are URL-live and application-open, age <= {max_age_days} days, target role fit, "
            "and already-applied/recent repeats removed. LinkedIn detail URLs blocked from automated checks are retained only as clearly labelled manual-review leads; LinkedIn redirect/search URLs are rejected."
        ),
        "Language note: English-first roles are listed first; German-required or German-unclear roles remain in their matching section for awareness.",
        "",
        "## Section 1 — Working Student / Internship / Part-Time",
        "Scope: Baden-Württemberg + Bavaria only; grouped by city for fast scanning.",
        "",
    ]
    append_grouped_results(lines, student_display, "student")
    lines.extend(
        [
            "## Section 2 — Full-Time Roles",
            (
                "Scope: Germany excluding East Germany; Berlin is allowed. Included states/cities: Baden-Württemberg, "
                "Bavaria, Hesse, Rhineland-Palatinate, North Rhine-Westphalia, Saarland, Lower Saxony, Bremen, "
                "Hamburg, and Berlin; grouped by city."
            ),
            "",
        ]
    )
    append_grouped_results(lines, fulltime_display, "fulltime")
    lines.extend(
        [
            "Analytics:",
            f"- Student validated total: {len(student_results)}; posted: {len(student_display)}; German-heavy included: {student_german_count}",
            f"- Full-time validated total: {len(fulltime_results)}; posted: {len(fulltime_display)}; German-heavy included: {fulltime_german_count}",
            "- Token control: discovery and merging ran in Python; the cron agent should post this markdown unchanged.",
        ]
    )
    if analytics:
        discovery = analytics.get("discovery") or {}
        raw_reject_counts = analytics.get("raw_reject_counts") or {}
        reject_counts = analytics.get("reject_counts") or {}
        raw_reject_summary = ", ".join(f"{key}={value}" for key, value in sorted(raw_reject_counts.items())) or "none"
        reject_summary = ", ".join(f"{key}={value}" for key, value in sorted(reject_counts.items())) or "none"
        for profile_name in ("student", "fulltime"):
            profile_discovery = discovery.get(profile_name) or {}
            lines.append(
                f"- {profile_name.title()} discovery: queries={profile_discovery.get('query_count', 0)}, "
                f"per_query={profile_discovery.get('per_query', 0)}, raw={profile_discovery.get('raw_candidates', 0)}, "
                f"cap={profile_discovery.get('max_validate', 0)}"
            )
        lines.extend(
            [
                f"- Applied jobs synced: {analytics.get('applied_jobs_count', 0)}",
                f"- Recent-posted cache: {analytics.get('recent_cache_count', 0)} URLs / {analytics.get('recent_fingerprint_count', 0)} fingerprints ({analytics.get('recent_cache_mode', 'n/a')})",
                f"- Raw unique after shared dedupe: {analytics.get('unique_candidates', 0)}",
                f"- Cross-pass duplicate raw URLs skipped: {analytics.get('cross_pass_duplicates', 0)}",
                f"- Unique page inputs selected: {analytics.get('validated_inputs', 0)}",
                f"- Page validation attempts: {analytics.get('validation_attempts', 0)}",
                f"- Passed validator before display cap: {analytics.get('validated_count', 0)}",
                f"- Raw reject breakdown: {raw_reject_summary}",
                f"- Page reject breakdown: {reject_summary}",
            ]
        )
    return "\n".join(lines)


def run_combined_1500(args: argparse.Namespace) -> int:
    runs_path = args.runs_path or str(default_runs_path_for_profile("student"))
    recent_cache = args.recent_cache or str(default_recent_cache_for_profile("student"))
    today = dt.date.today()
    now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    readiness = provider_readiness()
    if not any(readiness.values()):
        print(
            "Discovery is not configured for this runtime: no SerpAPI, no Exa, and no direct-source crawl configured.",
            file=sys.stderr,
        )
        return 2

    try:
        applied_path = Path(args.applied)
        refresh_status = refresh_applied_from_github(applied_path)
        applied_urls = load_applied(applied_path)
        recent_urls, recent_fingerprints, recent_cache_status = refresh_recent_urls_cache(
            Path(runs_path),
            Path(recent_cache),
            args.dedupe_days,
            now_ms,
        )
    except Exception as exc:
        print(f"Combined validator setup failed: {exc}", file=sys.stderr)
        return 1

    profile_limits = {
        "student": args.student_max_validate,
        "fulltime": args.fulltime_max_validate,
    }
    profile_per_query = {
        "student": args.student_per_query,
        "fulltime": args.fulltime_per_query,
    }
    profile_discovery: dict[str, dict[str, Any]] = {}
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(discover_profile_candidates, profile_name, per_query, readiness): profile_name
                for profile_name, per_query in profile_per_query.items()
            }
            for future in as_completed(futures):
                profile_name = futures[future]
                profile_discovery[profile_name] = future.result()
    except Exception as exc:
        print(f"Combined discovery failed: {exc}", file=sys.stderr)
        return 1

    raw_reject_counts: dict[str, int] = {}
    raw_debug_samples: list[dict[str, Any]] = []
    records: dict[str, dict[str, Any]] = {}
    cross_pass_duplicates = 0
    for profile_name in ("student", "fulltime"):
        for candidate in profile_discovery.get(profile_name, {}).get("raw_candidates", []):
            norm = normalize_url(candidate.url)
            if norm in applied_urls or norm in recent_urls:
                raw_reject_counts["applied_or_recent"] = raw_reject_counts.get("applied_or_recent", 0) + 1
                continue
            raw_reason = raw_candidate_reject_reason(candidate, profile_name)
            if raw_reason:
                raw_reject_counts[raw_reason] = raw_reject_counts.get(raw_reason, 0) + 1
                if len(raw_debug_samples) < 20:
                    raw_debug_samples.append(
                        {
                            "stage": "raw",
                            "profile": profile_name,
                            "title": candidate.title,
                            "url": candidate.url,
                            "reason": raw_reason,
                            "detail": {"source": candidate.source, "query": candidate.query},
                        }
                    )
                continue

            score = raw_candidate_score(candidate, profile_name)
            if norm not in records:
                records[norm] = {
                    "candidate": candidate,
                    "profiles": {profile_name},
                    "scores": {profile_name: score},
                }
                continue

            record = records[norm]
            if profile_name not in record["profiles"]:
                cross_pass_duplicates += 1
            previous_best = max(record["scores"].values())
            record["profiles"].add(profile_name)
            record["scores"][profile_name] = max(record["scores"].get(profile_name, -9999), score)
            if score > previous_best:
                record["candidate"] = candidate

    selected_norms: set[str] = set()
    for profile_name, limit in profile_limits.items():
        profile_records = [
            (norm, record)
            for norm, record in records.items()
            if profile_name in record.get("profiles", set())
        ]
        profile_records.sort(
            key=lambda item: candidate_profile_score(item[1], profile_name),
            reverse=True,
        )
        selected_norms.update(norm for norm, _ in profile_records[:limit])

    ordered_records = [
        records[norm]
        for norm in sorted(
            selected_norms,
            key=lambda key: max(records[key].get("scores", {}).values()),
            reverse=True,
        )
    ]

    student_results: list[dict[str, Any]] = []
    fulltime_results: list[dict[str, Any]] = []
    seen_final: set[str] = set()
    seen_final_fingerprints: set[str] = set()
    reject_counts: dict[str, int] = {}
    debug_samples: list[dict[str, Any]] = list(raw_debug_samples)
    validation_attempts = 0

    for record in ordered_records:
        candidate = record["candidate"]
        profiles = set(record.get("profiles") or ())
        primary_profile = choose_combined_validation_profile(record)
        fallback_profiles = [
            profile_name
            for profile_name in ("student", "fulltime")
            if profile_name in profiles and profile_name != primary_profile
        ]
        item: dict[str, Any] | None = None
        rejected_items: list[dict[str, Any]] = []
        for profile_name in [primary_profile, *fallback_profiles]:
            validation_attempts += 1
            checked = validate_candidate(candidate, today, args.max_age_days, profile_name)
            if not checked:
                continue
            if checked.get("reject_reason"):
                rejected_items.append(checked)
                reason = str(checked["reject_reason"])
                if reason not in {"not_target_role", "outside_profile_scope"}:
                    break
                continue
            item = checked
            item["_profile"] = profile_name
            break

        if not item:
            detail = rejected_items[-1] if rejected_items else {"reject_reason": "empty_validation"}
            reason = str(detail.get("reject_reason") or "empty_validation")
            reject_counts[reason] = reject_counts.get(reason, 0) + 1
            if len(debug_samples) < 20:
                debug_samples.append(
                    {
                        "title": candidate.title,
                        "url": candidate.url,
                        "reason": reason,
                        "detail": detail,
                    }
                )
            continue

        final_norm = item["normalized_url"]
        final_fingerprint = job_fingerprint(str(item.get("title") or ""), str(item.get("company") or ""))
        if (
            final_norm in applied_urls
            or final_norm in recent_urls
            or final_norm in seen_final
            or (final_fingerprint and final_fingerprint in recent_fingerprints)
            or (final_fingerprint and final_fingerprint in seen_final_fingerprints)
        ):
            reject_counts["final_applied_or_recent"] = reject_counts.get("final_applied_or_recent", 0) + 1
            continue

        seen_final.add(final_norm)
        if final_fingerprint:
            seen_final_fingerprints.add(final_fingerprint)
        if item.get("_profile") == "student":
            student_results.append(item)
        else:
            fulltime_results.append(item)

    student_results.sort(key=result_sort_key)
    fulltime_results.sort(key=result_sort_key)
    for profile_name, discovery in profile_discovery.items():
        discovery["raw_candidates"] = len(discovery.get("raw_candidates") or [])
        discovery["max_validate"] = profile_limits.get(profile_name, 0)

    analytics = {
        "applied_jobs_count": len(applied_urls),
        "applied_refresh": refresh_status,
        "recent_cache_mode": recent_cache_status.get("mode"),
        "recent_cache_count": recent_cache_status.get("count", 0),
        "recent_fingerprint_count": recent_cache_status.get("fingerprint_count", 0),
        "discovery": profile_discovery,
        "providers": combined_provider_summary(profile_discovery),
        "raw_reject_counts": raw_reject_counts,
        "unique_candidates": len(records),
        "cross_pass_duplicates": cross_pass_duplicates,
        "validated_inputs": len(ordered_records),
        "validation_attempts": validation_attempts,
        "validated_count": len(student_results) + len(fulltime_results),
        "reject_counts": reject_counts,
        "samples": debug_samples,
    }

    if args.debug:
        debug_payload = {
            "runs_path": runs_path,
            "recent_cache_path": recent_cache,
            **analytics,
            "student_results": student_results,
            "fulltime_results": fulltime_results,
        }
        print(json.dumps(debug_payload, ensure_ascii=False, indent=2))
        return 0

    print(
        render_combined_1500(
            student_results=student_results,
            fulltime_results=fulltime_results,
            max_age_days=args.max_age_days,
            analytics=analytics,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(SEARCH_PROFILES), default=os.environ.get("FRANKLEE_SEARCH_PROFILE", DEFAULT_PROFILE))
    parser.add_argument("--combined-1500", action="store_true", help="Render the combined 15:00 student + full-time daily job-search post")
    parser.add_argument("--max-age-days", type=int, default=20)
    parser.add_argument("--max-results", type=int, default=0)
    parser.add_argument("--per-query", type=int)
    parser.add_argument("--student-per-query", type=int, default=12)
    parser.add_argument("--student-max-validate", type=int, default=180)
    parser.add_argument("--fulltime-per-query", type=int, default=14)
    parser.add_argument("--fulltime-max-validate", type=int, default=180)
    parser.add_argument("--applied", default=str(WORKSPACE_ROOT / "data" / "applied_jobs.json"))
    parser.add_argument("--runs-path", default=os.environ.get("FRANKLEE_CRON_RUNS_PATH"))
    parser.add_argument("--recent-cache", default=os.environ.get("RECENT_POSTED_URLS_PATH"))
    parser.add_argument("--dedupe-days", type=int, default=21)
    parser.add_argument("--max-validate", type=int)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.combined_1500:
        return run_combined_1500(args)
    profile_name = args.profile
    profile = get_profile(profile_name)
    per_query = args.per_query if args.per_query is not None else int(profile.get("default_per_query", 8))
    max_validate = args.max_validate if args.max_validate is not None else int(profile.get("default_max_validate", 36))

    today = dt.date.today()
    now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)

    loaded_env = build_provider_env()
    serpapi_ready = SERPAPI_FALLBACK_PATH.exists() or bool(
        loaded_env.get("SERPAPI_API_KEYS")
        or loaded_env.get("SERPAPI_API_KEY")
        or loaded_env.get("SERPAPI_KEY")
    )
    exa_ready = EXA_SEARCH_PATH.exists() and bool(loaded_env.get("EXA_API_KEY"))
    direct_ready = bool(DIRECT_SOURCE_SITEMAPS)
    discovery_ready = serpapi_ready or exa_ready or direct_ready
    if not discovery_ready:
        print(
            "Discovery is not configured for this runtime: no SerpAPI, no Exa, and no direct-source crawl configured.",
            file=sys.stderr,
        )
        return 2

    applied_path = Path(args.applied)
    runs_path = Path(args.runs_path) if args.runs_path else default_runs_path_for_profile(profile_name)
    recent_cache_path = Path(args.recent_cache) if args.recent_cache else default_recent_cache_for_profile(profile_name)
    refresh_status = refresh_applied_from_github(applied_path)
    applied_urls = load_applied(applied_path)
    recent_urls, recent_fingerprints, recent_cache_status = refresh_recent_urls_cache(
        runs_path,
        recent_cache_path,
        args.dedupe_days,
        now_ms,
    )

    raw_candidates: list[Candidate] = []
    discovery_queries = build_discovery_queries(profile_name)
    provider_stats: dict[str, dict[str, Any]] = {
        "serpapi": {"ready": serpapi_ready, "queries": 0, "results": 0, "errors": []},
        "exa": {"ready": exa_ready, "queries": 0, "results": 0, "errors": []},
        "direct": {"ready": direct_ready, "queries": 0, "results": 0, "errors": []},
    }
    for query in discovery_queries:
        if serpapi_ready:
            provider_stats["serpapi"]["queries"] += 1
            try:
                results = query_serpapi(query, per_query)
                provider_stats["serpapi"]["results"] += len(results)
                raw_candidates.extend(results)
            except Exception as exc:
                provider_stats["serpapi"]["errors"].append(str(exc)[:180])
        if exa_ready:
            provider_stats["exa"]["queries"] += 1
            try:
                results = query_exa(query, max(4, min(per_query, 8)))
                provider_stats["exa"]["results"] += len(results)
                raw_candidates.extend(results)
            except Exception as exc:
                provider_stats["exa"]["errors"].append(str(exc)[:180])

    if direct_ready:
        provider_stats["direct"]["queries"] = len(DIRECT_SOURCE_SITEMAPS)
        try:
            direct_results = crawl_direct_sources(profile_name, limit_per_source=max(8, per_query))
            provider_stats["direct"]["results"] = len(direct_results)
            raw_candidates.extend(direct_results)
        except Exception as exc:
            provider_stats["direct"]["errors"].append(str(exc)[:180])

    deduped_raw: dict[str, Candidate] = {}
    raw_reject_counts: dict[str, int] = {}
    raw_debug_samples: list[dict[str, Any]] = []
    for candidate in raw_candidates:
        norm = normalize_url(candidate.url)
        if norm in applied_urls or norm in recent_urls:
            raw_reject_counts["applied_or_recent"] = raw_reject_counts.get("applied_or_recent", 0) + 1
            continue
        raw_reason = raw_candidate_reject_reason(candidate, profile_name)
        if raw_reason:
            raw_reject_counts[raw_reason] = raw_reject_counts.get(raw_reason, 0) + 1
            if len(raw_debug_samples) < 20:
                raw_debug_samples.append(
                    {
                        "stage": "raw",
                        "title": candidate.title,
                        "url": candidate.url,
                        "reason": raw_reason,
                        "detail": {"source": candidate.source, "query": candidate.query},
                    }
                )
            continue
        if norm in deduped_raw:
            continue
        deduped_raw[norm] = candidate

    ordered_raw = sorted(
        deduped_raw.values(),
        key=lambda candidate: raw_candidate_score(candidate, profile_name),
        reverse=True,
    )[: max_validate]

    validated: list[dict[str, Any]] = []
    seen_final: set[str] = set()
    seen_final_fingerprints: set[str] = set()
    reject_counts: dict[str, int] = {}
    debug_samples: list[dict[str, Any]] = list(raw_debug_samples)
    for candidate in ordered_raw:
        item = validate_candidate(candidate, today, args.max_age_days, profile_name)
        if not item:
            continue
        if item.get("reject_reason"):
            reason = str(item["reject_reason"])
            reject_counts[reason] = reject_counts.get(reason, 0) + 1
            if len(debug_samples) < 20:
                debug_samples.append(
                    {
                        "title": candidate.title,
                        "url": candidate.url,
                        "reason": reason,
                        "detail": item,
                    }
                )
            continue
        final_norm = item["normalized_url"]
        final_fingerprint = job_fingerprint(str(item.get("title") or ""), str(item.get("company") or ""))
        if (
            final_norm in applied_urls
            or final_norm in recent_urls
            or final_norm in seen_final
            or (final_fingerprint and final_fingerprint in recent_fingerprints)
            or (final_fingerprint and final_fingerprint in seen_final_fingerprints)
        ):
            reject_counts["final_applied_or_recent"] = reject_counts.get("final_applied_or_recent", 0) + 1
            continue
        seen_final.add(final_norm)
        if final_fingerprint:
            seen_final_fingerprints.add(final_fingerprint)
        validated.append(item)

    validated.sort(key=result_sort_key)
    final_results = validated if args.max_results <= 0 else validated[: args.max_results]
    main_results_count = sum(1 for item in final_results if item.get("language_bucket") != "german_required")
    german_required_results_count = sum(1 for item in final_results if item.get("language_bucket") == "german_required")

    analytics = {
        "profile": profile_name,
        "applied_jobs_count": len(applied_urls),
        "recent_cache_mode": recent_cache_status.get("mode"),
        "recent_cache_count": recent_cache_status.get("count", 0),
        "recent_fingerprint_count": recent_cache_status.get("fingerprint_count", 0),
        "query_count": len(discovery_queries),
        "per_query": per_query,
        "raw_candidates": len(raw_candidates),
        "raw_reject_counts": raw_reject_counts,
        "unique_candidates": len(deduped_raw),
        "validated_inputs": len(ordered_raw),
        "max_validate": max_validate,
        "validated_count": len(validated),
        "final_results": len(final_results),
        "main_results": main_results_count,
        "german_required_results": german_required_results_count,
        "reject_counts": reject_counts,
        "providers": provider_stats,
    }

    if args.debug:
        payload = {
            "profile": profile_name,
            "runs_path": str(runs_path),
            "recent_cache_path": str(recent_cache_path),
            "applied_refresh": refresh_status,
            "recent_cache": recent_cache_status,
            "raw_candidates": len(raw_candidates),
            "raw_reject_counts": raw_reject_counts,
            "unique_candidates": len(deduped_raw),
            "validated_inputs": len(ordered_raw),
            "validated_count": len(validated),
            "final_results": len(final_results),
            "main_results": main_results_count,
            "german_required_results": german_required_results_count,
            "reject_counts": reject_counts,
            "providers": provider_stats,
            "samples": debug_samples,
            "results": final_results,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.format == "json":
        print(json.dumps(final_results, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(final_results, args.max_age_days, profile_name, analytics=analytics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
