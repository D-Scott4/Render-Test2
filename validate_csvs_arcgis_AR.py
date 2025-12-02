"""
CSV Batch Validator (ArcGIS Pro ready)
- Input: a single CSV file OR a folder containing CSVs
- Output: a single HTML dashboard (Validation_Dashboard_*.html)

Run (CLI):
  python validate_csvs_arcgis_AR_modified.py <csv_or_folder>

ArcGIS Pro:
  Use as a script tool (Parameter 0: Input CSV or Folder)

Dependencies: Python 3.9+, pandas (ArcGIS Pro ships with pandas)
"""

import os
import re
import sys
import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

# Try arcpy for ArcGIS Pro integration; fall back to CLI if not present
try:
    import arcpy  # type: ignore
except Exception:
    arcpy = None  # running outside ArcGIS Pro

try:
    import pandas as pd
except ImportError:
    msg = "pandas is required. Install with: python -m pip install pandas"
    if arcpy:
        arcpy.AddError(msg)
    else:
        print(msg, file=sys.stderr)
    raise


# --------------------------------------------------------------------------------
# 1) EDITABLE VALIDATION RULES
# --------------------------------------------------------------------------------

# Expected filename pattern: MU123_2028_AR_TBL_Anything.csv
FILENAME_REGEX = re.compile(
    r"^(MU)(\d{3})_(\d{4})_(AR|Y6|FY)_(TBL)_([A-Za-z0-9_\-]+)\.csv$",
    re.IGNORECASE,
)

MIN_YEAR = 2024

RULES: Dict[str, Any] = {
    "options": {
        "case_insensitive_columns": False,   # column name matching
        "trim_strings": False,               # strip whitespace from string cells
        "warn_on_extra_columns": True,       # extra columns -> WARN
        "fail_fast": False,                  # stop on first error per file
        "aggregate_per_file": True,          # aggregate row-level issues into one line per file/column/error
        "case_insensitive_values": True,     # treat some field values case-insensitively for 'in' and 'regex' checks
    },
    "domains": {
        # Each of these is a list of allowed values for the respective column rules.
        "age_class_allowed": [],  # will be auto-generated below
        "HARVEST_TYPE": ["Regular", "Salvage"],
        "SPECIES_CODE": ["AX","Ab","Aw","Pl","Pt","Bd","Be","Bw","By","Bn","CE","Cr","Cw","CH","Cb","OC","EX","Ew","Bf","OH","He","Hi","Iw","La","Mh","Mr","Ms","Ob","Or","Ow","Pn","Pj","Pr","Ps","Pw","PO","Pb","SX","Sb","Sr","Sw","HwS"],
        "category": ["collect","seeding","planting"],
        "sourcesc": ["wild","orchard"],
        "account": ["renewal","futures"],
        "activity": ["natural","marking","artificial","site preparation","tending","support","survey","other","protection"],
        "type": ["aerial","ground"],
        "purpose": ["siteprep","tending","insect"],
        "regional_office": ["Thunder Bay","Sudbury","Kingston"],
        "Y_N": ["Y","N"],
        "operation_type": ["access","harvest","renewal","maintenance"],
        "inspector": ["licensee","ministry","joint","nonlicensee"],
        "status": ["in compliance","not in compliance", "pending"],
        "activity_remedies": ["aggregates","AOC","prevention","construction","crossing","cutting","utilization","measure","pesticide","renewal","tending","other"],
        "remedy": ["warning","s55","s56","s57","penalty","offence","suspended"],
        "category_harvest": ["projected","planned","actual"],
        "activity_renewal": ["regeneration","site preparation","tending","protection"],
        "treatment_method": ["natural","strip cut","seed tree","harp","claag","uniform","strip","group shelterwood","irregular","single tree","group selection","plant","seed","mechanical","chemical aerial","chemical ground","prescribed burn","cleaning chemical aerial","cleaning chemical ground","cleaning manual","cleaning mechanical","cleaning prescribed burn","improvement","pre-commercial thin","cultivation","pruning","protection chemical aerial","protection chemical ground","protection manual"],
        "category_silvobjectives": ["projected","planned","assigned","established"],
        "geo_area": [
  "2E.2", "3E.7", "1E.2", "2W.1", "2W.2", "2W.3", "3S.1", "3S.2", "3S.3", "3S.4", "3S.5", "3W.1", "4S.1", "4S.2", "4S.3", "4S.4", "Union", "Adams", "3E.4", "4W.2", "Lake", "Will", "Clay", "Clinton", "Monroe", "Delta", "Marquette", "Menominee", "Hennepin", "Renville", "Scott", "Washington", "Grant", "Sawyer", "Gogebic", "Keweenaw", "Keweenaw", "Cook", "Stark", "Carroll", "Grundy", "Marion", "Palo Alto", "Webster", "Blue Earth", "Cook", "Lake", "Morrison", "Redwood", "Wright", "Bayfield", "Crawford", "Iron", "Juneau", "Rusk", "Trempealeau", "Clarke", "Cass", "Grand Traverse", "Brown", "Adams", "Door", "Emmet", "St. Louis", "Henry", "Buffalo", "Emmet", "Florence", "Marinette", "Alger", "Leelanau", "Baraga", "Iron", "Charlevoix", "Charlevoix", "Mercer", "Stephenson", "Warren", "Bureau", "Carroll", "Grundy", "Henry", "Kankakee", "Adair", "Bremer", "Calhoun", "Kosciusko", "LaPorte", "Marshall", "Newton", "Dallas", "Delaware", "Greene", "Hamilton", "Hardin", "Jackson", "Johnson", "Lucas", "Marshall", "Mitchell",
  "Story", "Union", "Winnebago", "Carver", "Cottonwood", "Faribault", "Koochiching", "Martin", "Mille Lacs", "Olmsted", "Todd", "Wabasha", "Branch", "Cass", "Houghton", "Kalkaska", "Luce", "Ontonagon", "Osceola", "St. Joseph", "Van Buren", "Wexford", "Aitkin", "Calumet", "Columbia", "Dane", "Fond du Lac", "Kenosha", "Langlade", "Marathon", "Marquette", "Oneida", "Ozaukee", "Rock", "Taylor", "Vernon", "Walworth", "Barron", "Allegan", "Antrim", "Barry", "Berrien", "Calhoun", "Clare", "Dickinson", "Ionia", "Isabella", "Kent", "Manistee", "Montcalm", "Muskegon", "Beltrami", "LaSalle", "Lee", "Livingston", "Des Moines", "Dubuque", "Floyd", "Marshall", "Guthrie", "Hancock", "Howard", "Ogle", "Iowa", "Jasper", "Jefferson", "Jones", "Kossuth", "Linn", "Louisa", "Muscatine", "Polk", "Poweshiek", "Whiteside", "Sac", "Tama", "Warren", "Winneshiek", "Worth", "Wright", "DeKalb", "Elkhart", "Fulton", "Jasper", "Porter", "Pulaski", "St. Joseph", "Starke", "Allamakee", "Henderson", "Black Hawk", "Buchanan", "Butler", "Cass", "Chickasaw", "Jo Daviess", "Kane", "Clayton", "Houston", "Isanti",
  "Kanabec", "McLeod", "Meeker", "Mower", "Ramsey", "Rice", "Sherburne", "Steele", "Wadena", "Winona", "Carlton", "Crow Wing", "Fillmore", "Goodhue", "Vilas", "Washburn", "Washington", "Winnebago", "Wood", "Dickinson", "Washington", "Ashland", "Brown", "Newaygo", "Freeborn", "Burnett", "Chippewa", "Clark", "La Crosse", "Douglas", "Dunn", "Shawano", "Forest", "Green", "Green Lake", "Kewaunee", "Lafayette", "Manitowoc", "Milwaukee", "Outagamie", "Pepin", "Pierce", "Portage", "Racine", "Richland", "Knox", "Fayette", "Mahaska", "Madison", "Pocahontas", "Wapello", "Boone", "Lincoln", "Missaukee", "Dodge", "Jackson", "Pine", "Lake", "Buena Vista", "Sibley", "Franklin", "Keokuk", "Lake", "Ottawa", "McHenry", "Jackson", "Monroe", "Waushara", "Benton", "Hubbard", "Chisago", "Le Sueur", "Watonwan", "LaGrange", "Noble", "Steuben", "Cedar", "Benzie", "Eaton", "DeKalb", "Dodge", "Jefferson", "Kalamazoo", "Mecosta", "Boone", "Oconto", "Iowa", "Kendall", "Polk", "Waukesha", "Whitley", "Cerro Gordo", "Humboldt", "Waupaca", "Winnebago", "Benton", "Putnam", "Adams", "Sheboygan", "St. Croix",
  "Mason", "Eau Claire", "Price", "Dakota", "Oceana", "Anoka", "DuPage", "Rock Island", "Itasca", "Waseca", "Menominee", "Nicollet", "Allen", "Schoolcraft", "Sauk", "Kandiyohi", "Audubon", "Scott", "Stearns", "Morris", "3E.6", "4E.3", "4E.4", "4E.5", "5E.10", "5E.11", "6E.17", "5E.3", "6E.17", "6E.17", "5E.4", "5E.5", "5E.6", "5E.7", "5E.8", "5E.9", "6E.1", "6E.10", "6E.11", "6E.12", "6E.13", "6E.14", "6E.15", "6E.15", "6E.16", "6E.2", "6E.4", "6E.5", "6E.6", "6E.7", "6E.8", "6E.9", "7E.1", "7E.2", "7E.3", "7E.4", "7E.5", "7E.6", "Macomb", "Oscoda", "St. Clair", "Bergen", "Chautauqua", "Herkimer", "Jefferson", "Oneida", "Otsego", "Saratoga", "Cuyahoga", "Erie", "Clinton", "Huron", "Monroe", "Essex", "Sullivan", "Lucas", "Putnam", "Clearfield", "Monroe", "Wayne", "Niagara", "Clarion", "Cattaraugus", "Orange", "Ulster", "Cameron", "Oswego", "Chenango", "Presque Isle", "Northumberland", "Warren", "Ottawa", "Ontario", "Orleans", "Schuyler", "Tioga", "Wyoming", "Ashtabula", "Bay", "Montmorency",
  "Sussex", "Huron", "Shiawassee", "Franklin", "Livingston", "Montgomery", "Onondaga", "Trumbull", "Butler", "Forest", "Lawrence", "McKean", "Potter", "Susquehanna", "Venango", "Alcona", "Arenac", "Genesee", "Lapeer", "Lenawee", "Livingston", "Allegany", "Broome", "Cayuga", "Henry", "Chemung", "Lake", "Mahoning", "Greene", "Medina", "Hamilton", "Schenectady", "Schoharie", "Seneca", "Tompkins", "Portage", "Sandusky", "Seneca", "Summit", "Columbia", "Elk", "Jefferson", "Lackawanna", "Luzerne", "Lycoming", "Tioga", "Union", "Warren", "Bradford", "Ashland", "St. Lawrence", "Oakland", "Sullivan", "Carbon", "Ogemaw", "Sanilac", "Washtenaw", "Alpena", "Tuscola", "Genesee", "Lewis", "Hancock", "Crawford", "Mercer", "Monroe", "Steuben", "Cortland", "Rockland", "Wayne", "Iosco", "Wood", "Fulton", "Albany", "Montour", "Wyoming", "Fulton", "Geauga", "Lorain", "Saginaw", "Wayne", "Delaware", "Warren", "Erie", "Centre", "Passaic", "Erie", "Madison", "Yates", "Pike", "0E.1", "3E.1", "3W.4", "4W.1", "5E.1", "Paulding", "Ingham", "Hillsdale", "Gratiot", "1E.3", "3E.2",
  "3W.5", "5S.2", "5E.13", "Mackinac", "Jackson", "Williams", "Midland", "2E.3", "3W.3", "3W.3", "4S.6", "4E.1", "4E.1", "Defiance", "Gladwin", "Crawford", "Cheboygan", "2E.1", "3W.2", "4S.5", "Lake of the Woods", "3E.5", "Clinton", "Roscommon", "Otsego", "Chippewa", "Chippewa", "Chippewa", "Southeast", "Highrock", "Mountain", "Mountain", "Dauphin", "Riding Mountain", "Spruce Woods/Tu", "Spruce Woods/Tu", "Spruce Woods/Tu", "Spruce Woods/Tu", "Poplar River", "Lake Winnipeg E", "Nelson River", "Interlake", "Churchill River", "Hayes River", "Saskatchewan Ri", "ED.284", "ED.285", "ED.286", "ED.440", "ED.421", "ED.429", "ED.397", "ED.398", "ED.430", "ED.401", "ED.414", "ED.415", "ED.431", "ED.416", "ED.417", "ED.408", "ED.419", "ED.409", "ED.420", "ED.422", "ED.423", "ED.424", "ED.425", "ED.426", "ED.541", "ED.413", "ED.542", "ED.543", "ED.544", "ED.546", "ED.1031", "ED.441", "ED.428", "ED.418", "ED.287", "ED.437", "ED.540", "ED.1030", "ED.439", "ED.433"
],

    },
    "files": [
        {
            "name": "WoodUtilization",
            "pattern": r"WoodUtilization\.csv$",
            "required_columns": ["HARVEST_YEAR","MANAGEMENT_UNIT_CODE","MANAGEMENT_UNIT_NAME","LICENSEE_NAME","DESTINATION_CODE","DESTINATION_NAME","HARVEST_TYPE","PRODUCT","SPECIES_CODE","SPECIES_NAME","TOTAL_VOLUME"],
            "unique_key": [],
            "column_types": {
                "HARVEST_YEAR": "str",
                "MANAGEMENT_UNIT_CODE": "number>0",
                "MANAGEMENT_UNIT_NAME": "str",
                "LICENSEE_NAME": "str",
                "DESTINATION_CODE": "number>0",
                "DESTINATION_NAME": "str",
                "HARVEST_TYPE": "str",
                "PRODUCT": "str",
                "SPECIES_CODE": "number>0",
                "SPECIES_NAME": "str",
                "TOTAL_VOLUME": "number>=0",
            },
            "column_rules": {
                "HARVEST_TYPE": {"in": "domains.HARVEST_TYPE"},
            },
        },
        {
            "name": "RenewalSupport",
            "pattern": r"RenewalSupport\.csv$",
            "required_columns": ["category","species","geoarea","sourcesc","quantity"],
            "unique_key": [],
            "column_types": {
                "category": "str",
                "species": "str",
                "geoarea": "str",
                "sourcesc": "str",
                "quantity": "number>0",
            },
            "column_rules": {
                "category": {"in": "domains.category"},
                "species": {"in": "domains.SPECIES_CODE"},
                "geoarea": {"in": "domains.geo_area", "level": "WARN"},
                "sourcesc": {"in": "domains.sourcesc"},
            },
        },
        {
            "name": "Expenditures",
            "pattern": r"Expenditures\.csv$",
            "required_columns": ["account","activity","expenditure"],
            "unique_key": [],
            "column_types": {
                "account": "str",
                "activity": "str",
                "expenditure": "number>=0",
            },
            "column_rules": {
                "account": {"in": "domains.account"},
                "activity": {"in": "domains.activity"},
            },
        },
        {
            "name": "Pesticide",
            "pattern": r"Pesticide\.csv$",
            "required_columns": ["type","purpose","pesticide","concentrate","operator","operator licence","regional office","permit number","spray start","spray end","obm","block","number of applications","application rate","proposed size","actual size","quantity","exterminator name","exterminator number","aircraft number","complaint","reference number"],
            "unique_key": [],
            "column_types": {
                "type": "str",
                "purpose": "str",
                "pesticide": "str",
                "concentrate": "number>=0",
                "operator": "str",
                "operator licence": "str",
                "regional office": "str",
                "permit number": "str",
                "spray start": "str",
                "spray end": "str",
                "obm": "str",
                "block": "str",
                "number of applications": "number>=0",
                "application rate": "number>=0",
                "proposed size": "number>0",
                "actual size": "number>=0",
                "quantity": "number>=0",
                "exterminator name": "str",
                "exterminator number": "str",
                "aircraft number": "str",
                "complaint": "str",
                "reference number": "str",
            },
            "column_rules": {
                "type": {"in": "domains.type"},
                "purpose": {"in": "domains.purpose"},
                "regional office": {"in": "domains.regional_office"},
                "spray start": {"date": {"format": "%Y-%m-%d", "month_between": [5, 10], "year_equals": "2025"}},
                "spray end": {"date": {"format": "%Y-%m-%d", "month_between": [5, 10], "year_equals": "2025"}},
                "obm": {"obm": {"z_between": [15, 18], "e_between": [25, 75], "n_between": [460, 640]}},
                "complaint": {"in": "domains.Y_N"},
            },
        },
        {
            "name": "Compliance",
            "pattern": r"Compliance\.csv$",
            "required_columns": ["operation type","inspector","status","number"],
            "unique_key": [],
            "column_types": {
                "operation type": "str",
                "inspector": "str",
                "status": "str",
                "number": "number>=0",
            },
            "column_rules": {
                "operation type": {"in": "domains.operation_type"},
                "inspector": {"in": "domains.inspector"},
                "status": {"in": "domains.status"},
            },
        },
        {
            "name": "Remedies",
            "pattern": r"Remedies\.csv$",
            "required_columns": ["operation type","activity","remedy","number"],
            "unique_key": [],
            "column_types": {
                "operation type": "str",
                "activity": "str",
                "remedy": "str",
                "number": "number>=0",
            },
            "column_rules": {
                "operation type": {"in": "domains.operation_type"},
                "activity": {"in": "domains.activity_remedies"},
                "remedy": {"in": "domains.remedy"},
            },
        },
        {
            "name": "HarvestArea",
            "pattern": r"HarvestArea\.csv$",
            "required_columns": ["forest unit","category","term","area"],
            "unique_key": [],
            "column_types": {
                "forest unit": "str",
                "category": "str",
                "term": "str",
                "area": "number>=0",
            },
            "column_rules": {
                "category": {"in": "domains.category_harvest"},
            },
        },
        {
            "name": "HarvestVolume",
            "pattern": r"HarvestVolume\.csv$",
            "required_columns": ["species","category","term","volume"],
            "unique_key": [],
            "column_types": {
                "species": "str",
                "category": "str",
                "term": "str",
                "volume": "number>=0",
            },
            "column_rules": {
                "species": {"in": "domains.SPECIES_CODE"},
                "category": {"in": "domains.category_harvest"}
            },
        },
        {
            "name": "Renewal",
            "pattern": r"Renewal\.csv$",
            "required_columns": ["activity","treatment method","category","term","area"],
            "unique_key": [],
            "column_types": {
                "activity": "str",
                "treatment method": "str",
                "category": "str",
                "term": "str",
                "area": "number>=0",
            },
            "column_rules": {
                "activity": {"in": "domains.activity_renewal"},
                "treatment method": {"in": "domains.treatment_method"},
                "category": {"in": "domains.category_harvest"},
            },
        },
        {
            "name": "ForestCondition",
            "pattern": r"ForestCondition\.csv$",
            "required_columns": ["forest unit","age class","category","term","area"],
            "unique_key": [],
            "column_types": {
                "forest unit": "str",
                "age class": "str",
                "category": "str",
                "term": "str",
                "area": "number>=0",
            },
            "column_rules": {
                "category": {"in": "domains.category_harvest"},
                "age class": {"in": "domains.age_class_allowed"},
            },
        },
        {
            "name": "Wildlife",
            "pattern": r"Wildlife\.csv$",
            "required_columns": ["wildlife","category","term","area"],
            "unique_key": [],
            "column_types": {
                "wildlife": "str",
                "category": "str",
                "term": "str",
                "area": "number>=0",
            },
            "column_rules": {
                "category": {"in": "domains.category_harvest"},
            },
        },
        {
            "name": "SilviculturalObjectives",
            "pattern": r"SilviculturalObjectives\.csv$",
            "required_columns": ["target fu","target yield","sgr code","category","area"],
            "unique_key": [],
            "column_types": {
                "target fu": "str",
                "target yield": "str",
                "sgr code": "str",
                "category": "str",
                "area": "number>=0",
            },
            "column_rules": {
                "category": {"in": "domains.category_silvobjectives"},
            },
        },
    ],
}


# ---------------------------- Age Class Domain Builders -------------------------
def _make_age_class_labels_by_endpoints(step_end: int, end_max: int, plus_start: int):
    """
    Build exact labels using inclusive endpoints:
    e.g., step_end=10, end_max=250 -> 000-010, 011-020, ..., 241-250, then plus_start+'+'
    """
    labels = []
    low = 0
    for hi in range(step_end, end_max + 1, step_end):
        labels.append(f"{low:03d}-{hi:03d}")
        low = hi + 1
    labels.append(f"{plus_start:03d}+")
    return labels


def generate_age_class_domains():
    """
    Returns dict {'AC5': [...], 'AC10': [...], 'AC20': [...]}
    AC5/AC10 enumerate to 250 then '251+'
    AC20 enumerates to 260 then '261+'
    """
    return {
        "AC5": _make_age_class_labels_by_endpoints(5, 250, 251),
        "AC10": _make_age_class_labels_by_endpoints(10, 250, 251),
        "AC20": _make_age_class_labels_by_endpoints(20, 260, 261),
    }


# --------------------------------------------------------------------------------
# 2) VALIDATOR IMPLEMENTATION
# --------------------------------------------------------------------------------
@dataclass
class Finding:
    file: str
    row: Optional[int]      # 1-based CSV row index (incl header offset) used in non-aggregated mode
    level: str              # 'ERROR' | 'WARN' | 'INFO'
    code: str
    message: str
    rows_text: Optional[str] = None          # compact list for the Findings "Rows" column
    rows_all: Optional[List[int]] = None     # full list for CSV export


@dataclass
class FileResult:
    file: str
    matched_rule: Optional[str] = None
    rows: int = 0
    columns: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)


def validate_filename(fname: str) -> Tuple[bool, List[str], Dict[str, str]]:
    messages, parts = [], {}
    m = FILENAME_REGEX.match(fname)
    if not m:
        messages.append("Filename does not match required pattern: MU000_2028_AR_TBL_DESCRIPTION.csv")
        return False, messages, parts
    mu, num3, year, program, tbl, description = m.groups()
    parts = {"mu": mu.upper(), "num3": num3, "year": year, "program": program.upper(), "tbl": tbl.upper(), "description": description}
    if parts["mu"] != "MU":
        messages.append("Prefix must be 'MU'.")
    try:
        if int(parts["year"]) < MIN_YEAR:
            messages.append(f"Year must be {MIN_YEAR} or greater; got {parts['year']}.")
    except ValueError:
        messages.append("Year is not a valid number.")
    if parts["tbl"] != "TBL":
        messages.append("Segment after program must be 'TBL'.")
    return len(messages) == 0, messages, parts


def normalize_columns(df: pd.DataFrame, case_insensitive: bool, trim: bool) -> pd.DataFrame:
    cols = list(df.columns)
    new_cols = []
    for c in cols:
        c2 = c.strip() if trim else c
        if case_insensitive:
             c2 = c2.lower()
        new_cols.append(c2)
    df.columns = new_cols
    if trim:
        for c in df.select_dtypes(include=['object']).columns:
            df[c] = df[c].astype(str).str.strip()
    return df


def resolve_rule_value(rule_expr: str, context: Dict[str, Any]) -> Any:
    if "+" in rule_expr:
        parts = [p.strip() for p in rule_expr.split("+")]
        result: List[Any] = []
        for p in parts:
            val = resolve_rule_value(p, context)
            if isinstance(val, list):
                result += val
            else:
                result.append(val)
        return result
    cur = context
    for tok in rule_expr.split('.'):
        tok = tok.strip()
        if tok not in cur:
            raise KeyError(f"Cannot resolve '{rule_expr}' at '{tok}'")
        cur = cur[tok]
    return cur


def type_check(series: pd.Series, type_spec: str, trim: bool = False) -> Tuple[pd.Series, Optional[str]]:
    """Returns (mask of bad rows [True means bad], message)."""
    if type_spec == 'str':
        # treat NaN or "" (and whitespace-only if trim) as invalid
        s = series.astype(str)
        if trim:
            s = s.str.strip()
        mask = series.isna() | s.str.len().eq(0)
        return mask, "value must be a non-empty string"

    if type_spec.startswith('number'):
        lower = None
        if '>=' in type_spec:
            try:
                lower = float(type_spec.split('>=')[1])
            except Exception:
                pass
        if '>' in type_spec and '>=' not in type_spec:
            try:
                lower = float(type_spec.split('>')[1])
            except Exception:
                pass

        def to_num(x):
            try:
                return float(str(x).replace(',', ''))
            except Exception:
                return None

        nums = series.apply(to_num)
        bad = nums.isna()
        if '>=' in type_spec and lower is not None:
            bad |= nums.lt(lower, fill_value=False)
        elif '>' in type_spec and lower is not None:
            bad |= ~(nums > lower)
        msg = "value must be numeric" + (f" and >= {lower:g}" if lower is not None and '>=' in type_spec
                                         else (f" and > {lower:g}" if lower is not None and '>' in type_spec else ""))
        return bad, msg

    return pd.Series([False]*len(series), index=series.index), None


def apply_column_rules(series: pd.Series, rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[pd.Series, str]:
    """Apply per-column rules; honors context['options']['case_insensitive_values'] and 'trim_strings'."""
    options = context.get('options', {})
    cis = bool(options.get('case_insensitive_values', False))
    trim = bool(options.get('trim_strings', False))

    if 'in' in rule:
        allowed = resolve_rule_value(rule['in'], context)
        if cis:
            allowed_norm = set(str(x).lower() for x in allowed)
            s = series.astype(str)
            if trim:
                s = s.str.strip()
            s = s.str.lower()
            bad = ~s.isin(allowed_norm)
        else:
            # assume normalize_columns handled trimming if requested
            bad = ~series.isin(set(allowed))
        return bad, f"value not in allowed set ({sorted(list(set(allowed)))[:10]}...)"

    if 'regex' in rule:
        pattern = resolve_rule_value(rule['regex'], context)
        flags = re.IGNORECASE if cis else 0
        regex = re.compile(pattern, flags=flags)
        s = series.astype(str)
        if trim:
            s = s.str.strip()
        bad = ~s.str.match(regex)
        return bad, f"value does not match pattern {pattern}"

    # Structured date validation (format, month range, and year equals)
    if 'date' in rule:
        opts = rule['date']
        fmt = opts.get('format', '%Y-%m-%d')
        month_between = opts.get('month_between')  # e.g., [5, 10]
        year_equals = opts.get('year_equals')      # int or context key like "ar_year"

        if isinstance(year_equals, str) and year_equals in context:
            year_equals = context[year_equals]

        def is_bad(val) -> bool:
            s = str(val).strip()
            try:
                d = dt.datetime.strptime(s, fmt)
            except Exception:
                return True  # parse failure
            if month_between:
                lo, hi = int(month_between[0]), int(month_between[1])
                if not (lo <= d.month <= hi):
                    return True
            if year_equals is not None:
                try:
                    if d.year != int(year_equals):
                        return True
                except Exception:
                    return True
            return False

        bad = series.apply(is_bad)
        parts = [f"format {fmt}"]
        if month_between:
            parts.append(f"month between {month_between[0]:02d}-{month_between[1]:02d}")
        if year_equals is not None:
            parts.append(f"year == {year_equals}")
        msg = "value must be a date with " + ", ".join(parts)
        return bad, msg

    # OBM grid rule  "ZZ-EE-NNN" with numeric ranges for each part
    if 'obm' in rule:
        opts = rule['obm'] or {}
        z_lo, z_hi = map(int, opts.get('z_between', [15, 18]))
        e_lo, e_hi = map(int, opts.get('e_between', [25, 75]))
        n_lo, n_hi = map(int, opts.get('n_between', [460, 640]))

        pattern = re.compile(r'^(\d{2})-(\d{2})-(\d{3})$')

        def is_bad(val) -> bool:
            s = str(val).strip()
            m = pattern.match(s)
            if not m:
                return True
            try:
                zz, ee, nnn = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                return True
            if not (z_lo <= zz <= z_hi):
                return True
            if not (e_lo <= ee <= e_hi):
                return True
            if not (n_lo <= nnn <= n_hi):
                return True
            return False

        bad = series.apply(is_bad)
        msg = (f'value must be "ZZ-EE-NNN" with '
               f'ZZ in [{z_lo}-{z_hi}], EE in [{e_lo}-{e_hi}], NNN in [{n_lo}-{n_hi}]')
        return bad, msg

    return pd.Series([False]*len(series), index=series.index), ""


def validate_file(path: str, rule_def: Dict[str, Any], options: Dict[str, Any], context: Dict[str, Any]) -> FileResult:
    fr = FileResult(file=os.path.basename(path), matched_rule=rule_def.get('name'))
    try:
        df = pd.read_csv(path)
    except Exception as e:
        fr.findings.append(Finding(fr.file, None, 'ERROR', 'READ_ERROR', f"Cannot read CSV: {e}", rows_text="", rows_all=[]))
        return fr

    df = normalize_columns(df, options.get('case_insensitive_columns', True), options.get('trim_strings', True))
    fr.rows = len(df)
    fr.columns = list(df.columns)

    required = [c for c in rule_def.get('required_columns', [])]
    missing = [c for c in required if c not in df.columns]
    if missing:
        fr.findings.append(Finding(fr.file, None, 'ERROR', 'MISSING_COLUMNS', f"Missing columns: {missing}", rows_text="", rows_all=""))
        if options.get('fail_fast'):
            return fr

    extra = [c for c in df.columns if c not in required]
    if extra:
        lvl = 'WARN' if options.get('warn_on_extra_columns', True) else 'INFO'
        fr.findings.append(Finding(fr.file, None, lvl, 'EXTRA_COLUMNS', f"Extra columns present: {extra}", rows_text="", rows_all=[]))

    # Helper to append one aggregated line per file/column
    def _append_agg(code: str, col: Optional[str], base_msg: str, bad_index: pd.Index, level: str = 'ERROR'):
        if len(bad_index) == 0:
            return
        rows = sorted([int(i) + 2 for i in bad_index])  # 1-based CSV rows (+ header)
        rows_text = ", ".join(map(str, rows[:100])) + ("…" if len(rows) > 100 else "")
        col_txt = f"Column '{col}': " if col else ""
        msg = f"{col_txt}{base_msg}. Count: {len(rows)}"
        fr.findings.append(Finding(fr.file, None, level, code, msg, rows_text=rows_text, rows_all=rows))

    # --- PESTICIDE-specific: group all related issues into a single finding per data row ---
    is_pesticide = (rule_def.get('name', '').lower() == 'pesticide')
    row_issues: Dict[int, List[str]] = {}

    # Predefine Pesticide exception sets
    P_NUM = ['number of applications', 'application rate', 'actual size', 'quantity']
    P_STR = ['spray start', 'spray end', 'exterminator name', 'exterminator number', 'aircraft number', 'complaint']
    P_ALL = P_NUM + P_STR
    P_ALL_PLUS_REF = set(P_ALL + ['reference number'])

    # Normalized presence of columns
    def _has(col: str) -> bool:
        return col in df.columns

    # Helpers
    
    def _is_blank(x, allow_zero=True):
        if pd.isna(x):
            return True
        s = str(x).strip().upper()
        if s in ('', 'NA'):
            return True
        if allow_zero and s in ('0', '0.0'):
            return True
        return False


    def _to_float_or_none(x) -> Optional[float]:
        try:
            return float(str(x).replace(',', '').strip())
        except Exception:
            return None

    def _num_is_zero(x) -> bool:
        f = _to_float_or_none(x)
        return f is not None and f == 0.0

    def _num_lt_zero(x) -> bool:
        f = _to_float_or_none(x)
        return f is not None and f < 0

    def _is_Y(val: Any) -> bool:
        return str(val).strip().upper() == 'Y'

    def _is_YN(val: Any) -> bool:
        v = str(val).strip().upper()
        return v in ('Y', 'N')

    # Date rule options from RULES (if present)
    start_date_opts = rule_def.get('column_rules', {}).get('spray start', {}).get('date', {}) if is_pesticide else {}
    end_date_opts   = rule_def.get('column_rules', {}).get('spray end', {}).get('date', {}) if is_pesticide else {}
    ar_year = context.get('ar_year', None)

    def _date_bad_msg(opts: Dict[str, Any]) -> str:
        parts = [f"format {opts.get('format', '%Y-%m-%d')}"]
        if 'month_between' in opts and opts['month_between']:
            parts.append(f"month between {int(opts['month_between'][0]):02d}-{int(opts['month_between'][1]):02d}")
        year_equals = opts.get('year_equals', None)
        if isinstance(year_equals, str) and year_equals in context:
            year_equals = context[year_equals]
        if year_equals is not None:
            parts.append(f"year == {int(year_equals)}")
        return "must be a date with " + ", ".join(parts)

    def _date_is_valid(val: Any, opts: Dict[str, Any]) -> bool:
        fmt = opts.get('format', '%Y-%m-%d')
        s = str(val).strip()
        try:
            d = dt.datetime.strptime(s, fmt)
        except Exception:
            return False
        # month range
        if 'month_between' in opts and opts['month_between']:
            lo, hi = int(opts['month_between'][0]), int(opts['month_between'][1])
            if not (lo <= d.month <= hi):
                return False
        # year equals
        year_equals = opts.get('year_equals', None)
        if isinstance(year_equals, str) and year_equals in context:
            year_equals = context[year_equals]
        if year_equals is not None:
            try:
                if d.year != int(year_equals):
                    return False
            except Exception:
                return False
        return True

    # ---------- Standard checks for non-Pesticide or non-exception Pesticide columns ----------
    # Type checks
    for col, spec in rule_def.get('column_types', {}).items():
        coln = col.lower()
        if coln not in df.columns:
            continue

        # Skip Pesticide exception columns here
        if is_pesticide and coln in P_ALL_PLUS_REF:
            continue

        bad_mask, msg = type_check(df[coln], spec, trim=options.get('trim_strings', False))
        bad_index = df.index[bad_mask]
        if options.get('aggregate_per_file', True):
            _append_agg('BAD_TYPE', col, msg or 'invalid value', bad_index, level='ERROR')
        else:
            for idx in bad_index:
                row_no = int(idx) + 2
                fr.findings.append(Finding(fr.file, row_no, 'ERROR', 'BAD_TYPE', f"Column '{col}': {msg}", rows_text=str(row_no), rows_all=[row_no]))
        if options.get('fail_fast') and len(bad_index) > 0:
            return fr

    # Column rules (non-exception columns only)
    for col, r in rule_def.get('column_rules', {}).items():
        coln = col.lower()
        if coln not in df.columns:
            continue

        # Skip these for Pesticide
        if is_pesticide and coln in ['spray start', 'spray end', 'actual size', 'application rate', 'number of applications', 'quantity', 'reference number', 'complaint']:
            continue

        bad_mask, msg = apply_column_rules(df[coln], r, context)
        bad_index = df.index[bad_mask]
        if options.get('aggregate_per_file', True):
            # Allow column rule to override error level (default ERROR, but can set 'level': 'WARN' in rule)
            rule_level = r.get('level', 'ERROR').upper()
            _append_agg('RULE_VIOLATION', col, msg or 'rule violation', bad_index, level=rule_level)
        else:
            for idx in bad_index:
                row_no = int(idx) + 2
                fr.findings.append(Finding(fr.file, row_no, 'ERROR', 'RULE_VIOLATION', f"Column '{col}': {msg}", rows_text=str(row_no), rows_all=[row_no]))
        if options.get('fail_fast') and len(bad_index) > 0:
            return fr

    # Duplicate key checks (unchanged)
    ukey = [c.lower() for c in rule_def.get('unique_key', [])]
    if all(c in df.columns for c in ukey) and ukey:
        dups = df.duplicated(subset=ukey, keep=False)
        if dups.any():
            if options.get('aggregate_per_file', True):
                dup_idx = df.index[dups]
                rows_all = sorted([int(i) + 2 for i in dup_idx])
                total_dup_rows = len(rows_all)
                ddf = df.loc[dup_idx, ukey].copy()
                ddf['__row__'] = rows_all
                groups = ddf.groupby(ukey)['__row__'].apply(lambda s: sorted(s.tolist()))
                num_keys = len(groups)
                msg = f"Duplicate by key {ukey}: {total_dup_rows} duplicate rows across {num_keys} key value(s)"
                rows_text = ", ".join(map(str, rows_all[:100])) + ("…" if len(rows_all) > 100 else "")
                fr.findings.append(Finding(fr.file, None, 'WARN', 'DUPLICATE_KEY', msg, rows_text=rows_text, rows_all=rows_all))
            else:
                for idx in df.index[dups]:
                    row_no = int(idx) + 2
                    keyvals = {k: df.loc[idx, k] for k in ukey}
                    fr.findings.append(Finding(fr.file, row_no, 'WARN', 'DUPLICATE_KEY', f"Duplicate by key {ukey}: {keyvals}", rows_text=str(row_no), rows_all=[row_no]))

    # ---------- Row-wise Pesticide validation & error summary by type ----------
    if is_pesticide:
        # Build "treatment present" mask:
        # spray start/end must both be non-blank (not empty, null, or "NA")
        # Build "treatment present" mask:
# spray start/end must both be non-blank (empty/NA/0 treated as blank for dates)
        def __is_blank_date(val: object) -> bool:
            if pd.isna(val):
                return True
            s = str(val).strip()
            up = s.upper()
            return (s == '' or up == 'NA' or s in ('0','0.0'))

        s_present = df['spray start'].apply(lambda v: not __is_blank_date(v)) if _has('spray start') else pd.Series(False, index=df.index)
        e_present = df['spray end'  ].apply(lambda v: not __is_blank_date(v)) if _has('spray end')   else pd.Series(False, index=df.index)
        treatment_present = s_present & e_present

        # Dictionary to collect errors by error message (error type)
        error_summary: Dict[str, List[int]] = {}

        # Per-row evaluation to gather all issues
        for idx in df.index:
            issues: List[str] = []

            # Fetch values safely (default to None)
            row = df.loc[idx]
            def gv(c):  # get value
                return row[c] if _has(c) else None

            present = bool(treatment_present.loc[idx])

            # --- If treatment present: all P_ALL must be filled/valid ---
            if present:
                # Numeric fields: must be numeric and > 0
                for c in P_NUM:
                    if not _has(c):
                        continue
                    v = gv(c)
                    f = _to_float_or_none(v)
                    if f is None:
                        issues.append(f"{c}: must be numeric and > 0 when treatment is provided")
                    elif f <= 0:
                        issues.append(f"{c}: must be > 0 when treatment is provided")

                # String required fields
                for c in ['exterminator name', 'exterminator number', 'aircraft number']:
                    if not _has(c):
                        continue
                    if _is_blank(gv(c)):
                        issues.append(f"{c}: required when treatment is provided")

                # Complaint required and must be Y/N
                if _has('complaint'):
                    comp = gv('complaint')
                    if _is_blank(comp):
                        issues.append("complaint: required when treatment is provided")
                    elif not _is_YN(comp):
                        issues.append("complaint: must be 'Y' or 'N'")

                # Dates required + must satisfy date constraints
                if _has('spray start'):
                    v = gv('spray start')
                    if _is_blank(v):
                        issues.append("spray start: required when treatment is provided")
                    else:
                        if not _date_is_valid(v, start_date_opts):
                            issues.append(f"spray start: {_date_bad_msg(start_date_opts)}")
                if _has('spray end'):
                    v = gv('spray end')
                    if _is_blank(v):
                        issues.append("spray end: required when treatment is provided")
                    else:
                        if not _date_is_valid(v, end_date_opts):
                            issues.append(f"spray end: {_date_bad_msg(end_date_opts)}")

            # --- If treatment NOT present: allow blanks/zeros, but still fail on negatives and invalid complaint values supplied ---
            else:
                # If user supplied a negative number or a non-numeric string in a numeric field (neither blank nor zero), flag it.
                for c in P_NUM:
                    if not _has(c):
                        continue
                    v = gv(c)
                    if _is_blank(v):
                        continue
                    f = _to_float_or_none(v)
                    if f is None:
                        issues.append(f"{c}: must be numeric (blank or 0 is allowed when no treatment)")
                    elif f < 0:
                        issues.append(f"{c}: must be >= 0 (blank or 0 is allowed when no treatment)")

            # --- Reference number when complaint = Y ---
            if _has('complaint') and _has('reference number'):
                comp = gv('complaint')
                if _is_Y(comp):
                    refv = gv('reference number')
                    if _is_blank(refv) or _num_is_zero(refv):
                        issues.append("reference number: required and non-zero when complaint = 'Y'")

            # Collect errors by type
            if issues:
                row_no = int(idx) + 2
                for issue_msg in issues:
                    if issue_msg not in error_summary:
                        error_summary[issue_msg] = []
                    error_summary[issue_msg].append(row_no)

        # Create one finding per error type
        if error_summary:
            for error_msg in sorted(error_summary.keys()):
                rows = sorted(error_summary[error_msg])
                rows_text = ", ".join(map(str, rows[:50])) + ("…" if len(rows) > 50 else "")
                msg = f"Pesticide: {error_msg}. Count: {len(rows)}"
                fr.findings.append(Finding(fr.file, None, 'ERROR', 'PESTICIDE_ERROR', msg, rows_text=rows_text, rows_all=rows))


    return fr


def build_domains_from_sources(csv_files: List[str], rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build domains using only the provided CSV file list (works for single file or folder sets).
    """
    domains = dict(rules.get('domains', {}))

    # Derive age classes: union of AC5/AC10/AC20 + ALLAGED
    ac = generate_age_class_domains()
    age_master = set(ac['AC5']) | set(ac['AC10']) | set(ac['AC20']) | {'ALLAGED'}
    domains['age_class_allowed'] = sorted(age_master)

    return domains


def run_validation(csv_files: List[str], rules: Dict[str, Any]) -> Tuple[List[FileResult], Dict[str, Any]]:
    """
    Validate a provided list of csv file paths using the provided rules.
    """
    options = rules.get('options', {})
    domains = build_domains_from_sources(csv_files, rules)  # use only the files provided
    # include options in context so column rule evaluators can read case_insensitive_values / trim_strings
    context = {'domains': domains, 'options': options}
    results: List[FileResult] = []

    file_rules = rules.get('files', [])

    for full in csv_files:
        f = os.path.basename(full)
        if not f.lower().endswith('.csv'):
            continue

        # filename validation first
        ok, msgs, parts = validate_filename(f)
        if not ok:
            fr = FileResult(file=f)
            for m in msgs:
                fr.findings.append(Finding(f, None, 'ERROR', 'BAD_FILENAME', m, rows_text="", rows_all=[]))
            results.append(fr)
            continue

        matched = None
        for r in file_rules:
            if re.search(r['pattern'], f, flags=re.IGNORECASE):
                matched = r
                break

        if matched is None:
            fr = FileResult(file=f)
            fr.findings.append(Finding(f, None, 'INFO', 'SKIPPED_FILE', 'No rule matched this CSV', rows_text="", rows_all=[]))
            results.append(fr)
            continue

        # Build a file-specific context that includes the AR year from the filename
        try:
            ar_year = int(parts.get("year", 0))
        except Exception:
            ar_year = None

        file_context = dict(context)
        file_context['ar_year'] = ar_year

        fr = validate_file(full, matched, options, file_context)
        results.append(fr)

    return results, context


# --------------------------------------------------------------------------------
# 3) HTML DASHBOARD REPORT
# --------------------------------------------------------------------------------
def html_escape(s: Any) -> str:
    import html
    return html.escape("" if s is None else str(s))


def dataframe_to_html_table(df: pd.DataFrame, table_id: str, escape: bool = True) -> str:
    if df is None or df.empty:
        return f'<table id="{table_id}" class="grid"><thead><tr><th>(no data)</th></tr></thead><tbody></tbody></table>'
    if escape:
        return df.to_html(index=False, table_id=table_id, classes="grid", border=0, escape=True)
    else:
        return df.to_html(index=False, table_id=table_id, classes="grid", border=0, escape=False)


def write_report_html(output_folder: str, results: List[FileResult], context: Dict[str, Any]) -> str:
    # Flatten findings
    rows_out = []
    for fr in results:
        for g in fr.findings:
            rows_full_csv = ",".join(map(str, g.rows_all)) if g.rows_all else ""
            btn_html = ""
            if rows_full_csv:
                svg = (
                    '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false">'
                    '<path fill="#2c7bd9" d="M14,3H6A2,2 0 0,0 4,5V19A2,2 0 0,0 6,21H18A2,2 0 0,0 20,19V9L14,3Z" />'
                    '<path fill="#fff" d="M9 13h6v2H9v-2zm0 3h6v2H9v-2zM9 10h6v2H9v-2z"/>'
                    '</svg>'
                )
                btn_html = (
                    f'<button class="csv-btn" title="Export affected rows" '
                    f'onclick="exportRowsCSV(this)" '
                    f'data-rows="{html_escape(rows_full_csv)}" '
                    f'data-file="{html_escape(g.file)}" '
                    f'data-code="{html_escape(g.code)}">{svg}</button>'
                )

            rows_out.append({
                'file': g.file,
                'Rows': g.rows_text or (str(g.row) if g.row is not None else ""),
                'level': g.level,  # keep as 3rd visible column (index 2)
                'code': g.code,
                'message': g.message,
                'Export': btn_html,  # put Export at the end to keep 'level' index stable
            })

    if rows_out:
        df_findings = pd.DataFrame(rows_out, columns=['file','Rows','level','code','message','Export'])
    else:
        df_findings = pd.DataFrame(
            [{'file':'(none)','Rows':'','level':'INFO','code':'NO_ISSUES','message':'No issues found','Export':''}],
            columns=['file','Rows','level','code','message','Export']
        )

    # Summary per file
    summary = []
    for fr in results:
        counts = pd.Series([g.level for g in fr.findings]).value_counts() if fr.findings else pd.Series(dtype=int)
        summary.append({
            'file': fr.file,
            'matched_rule': fr.matched_rule,
            'rows': fr.rows,
            'columns': ", ".join(fr.columns),
            'errors': int(counts.get('ERROR', 0)),
            'warnings': int(counts.get('WARN', 0)),
            'info': int(counts.get('INFO', 0)),
        })
    df_summary = pd.DataFrame(summary).sort_values(['errors','warnings'], ascending=[False, False])

    # Render level (after counts computed)
    def level_badge(x: str) -> str:
        lvl = html_escape(x)
        return f'<span class="pill {lvl}">{lvl}</span>'
    df_findings_render = df_findings.copy()
    if not df_findings_render.empty:
        df_findings_render['level'] = df_findings_render['level'].apply(level_badge)

    # HTML shell
    ts = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    title = "CSV Validation Dashboard"

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    out_html = os.path.join(output_folder, f'Validation_Dashboard_{dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.html')

    css = """
    body { font-family: Segoe UI, Roboto, Arial, sans-serif; margin: 24px; color: #1b1b1b; }
    h1, h2 { margin: 0 0 12px 0; }
    h1 { font-size: 22px; }
    h2 { font-size: 18px; margin-top: 28px; }
    .meta { color: #555; margin-bottom: 16px; }
    .flex { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .pill { padding: 2px 8px; border-radius: 999px; font-size: 12px; color: white; }
    .ERROR { background: #d92c2c; }
    .WARN { background: #f5a524; color: #222; }
    .INFO { background: #2c7bd9; }
    .grid { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .grid thead th { position: sticky; top: 0; background: #f4f6f8; z-index: 1; }
    .grid th, .grid td { border: 1px solid #e2e7ea; padding: 6px 8px; vertical-align: top; }
    .grid tbody tr:nth-child(even) { background: #fafbfc; }
    input[type="text"] { padding: 6px 8px; border: 1px solid #c8d1da; border-radius: 4px; width: 280px; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 8px; font-size: 12px; background: #eef2f6; color: #334; }
    .small { font-size: 12px; color: #555; }
    .mt8 { margin-top: 8px; }
    .mt16 { margin-top: 16px; }
    .mt24 { margin-top: 24px; }
    .controls { margin: 8px 0 12px; }
    .counts { margin: 0 8px; }
    .counts span { margin-right: 8px; }
    /* widen first column for long names */
    #summary-table th:first-child,
    #summary-table td:first-child,
    #findings-table th:first-child,
    #findings-table td:first-child {
      width: 28%;
      min-width: 260px;
      word-break: break-word;
      overflow-wrap: anywhere;
      white-space: normal;
    }
    /* CSV export button */
    .csv-btn { padding: 2px 6px; border: 1px solid #c8d1da; border-radius: 4px; background: #fff; cursor: pointer; }
    .csv-btn:hover { background: #f4f6f8; }
    .csv-btn:active { transform: translateY(1px); }
    """

    js = """
    function textFilter(input, tableId) {
      const query = input.value.toLowerCase();
      const tbl = document.getElementById(tableId);
      if (!tbl) return;
      const rows = tbl.tBodies[0].rows;
      for (let i=0; i<rows.length; i++) {
        const txt = rows[i].innerText.toLowerCase();
        rows[i].style.display = txt.includes(query) ? '' : 'none';
      }
    }
    function filterFindings() {
      const search = document.getElementById('findings-search').value.toLowerCase();
      const checks = Array.from(document.querySelectorAll('input[name="levelFilter"]:checked')).map(x => x.value);
      const tbl = document.getElementById('findings-table');
      if (!tbl) return;
      const rows = tbl.tBodies[0].rows;
      for (let i=0; i<i<rows.length; i++) {}
      for (let i=0; i<rows.length; i++) {
        const row = rows[i];
        const textOk = row.innerText.toLowerCase().includes(search);
        const levelCell = row.cells[2]; // 'level' is the 3rd visible column
        const levelText = levelCell ? levelCell.innerText.trim() : '';
        const levelOk = checks.includes(levelText);
        row.style.display = (textOk && levelOk) ? '' : 'none';
      }
      updateCounts();
    }
    function updateCounts() {
      const tbl = document.getElementById('findings-table');
      if (!tbl) return;
      const rows = Array.from(tbl.tBodies[0].rows).filter(r => r.style.display !== 'none');
      let e=0,w=0,i=0;
      rows.forEach(r => {
        const lvl = (r.cells[2] ? r.cells[2].innerText.trim() : '');
        if (lvl==='ERROR') e++; else if (lvl==='WARN') w++; else i++;
      });
      document.getElementById('count-err').innerText = e;
      document.getElementById('count-warn').innerText = w;
      document.getElementById('count-info').innerText = i;
      document.getElementById('count-shown').innerText = rows.length;
    }
    // Sanitize a suggested filename
    function safeFileName(s) {
      return (s || '').replace(/[^A-Za-z0-9_\\-\\.]/g, '_');
    }
    // Main: export rows as CSV
    function exportRowsCSV(btn) {
      try {
        const rowsCSV = (btn.getAttribute('data-rows') || '').trim();
        if (!rowsCSV) return;

        const file = safeFileName(btn.getAttribute('data-file') || 'rows');
        const code = safeFileName(btn.getAttribute('data-code') || 'FINDING');
        const ts = new Date().toISOString().replace(/[:T]/g, '-').split('.')[0];
        const name = `${file}_${code}_rows_${ts}.csv`;

        const header = '\\ufeffrow\\n'; // BOM for Excel + header
        const body = rowsCSV.split(',').map(s => s.trim()).filter(Boolean).join('\\n') + '\\n';
        const csv = header + body;

        // Prefer Blob + object URL
        if (window.Blob && window.URL && window.URL.createObjectURL) {
          const blob = new Blob([csv], {type: 'text/csv;charset=utf-8;'});
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = name;
          a.style.display = 'none';
          document.body.appendChild(a);
          a.click();
          setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 500);
          return;
        }

        // Fallback: data URL
        const a = document.createElement('a');
        a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
        a.download = name;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        a.remove();
      } catch (err) {
        console.error('Export failed', err);
        alert('Sorry — export failed. Check the browser console for details.');
      }
    }
    // Backup: delegated handler (in case inline onclick is blocked by CSP)
    document.addEventListener('click', function(e){
      const btn = e.target.closest && e.target.closest('.csv-btn');
      if (btn) exportRowsCSV(btn);
    });
    window.addEventListener('DOMContentLoaded', () => { updateCounts(); });
    """

    summary_html = dataframe_to_html_table(df_summary, "summary-table", escape=True)
    # IMPORTANT: escape=False so the Export button HTML renders
    findings_html = dataframe_to_html_table(df_findings_render, "findings-table", escape=False)

    # Totals for meta header (use plain 'df_findings' before pill rendering)
    total_err = int((df_findings['level'].str.upper() == 'ERROR').sum()) if not df_findings.empty else 0
    total_warn = int((df_findings['level'].str.upper() == 'WARN').sum()) if not df_findings.empty else 0
    total_info = int((df_findings['level'].str.upper() == 'INFO').sum()) if not df_findings.empty else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html_escape(title)}</title>
<style>{css}</style>
</head>
<body>
  <h1>{html_escape(title)}</h1>
  <div class="meta">
    Generated: {html_escape(ts)} — Output Folder: <span class="small">{html_escape(output_folder)}</span>
    <div class="mt8 small">Totals — Errors: <span class="pill ERROR">{total_err}</span>,
    Warnings: <span class="pill WARN">{total_warn}</span>,
    Info: <span class="pill INFO">{total_info}</span></div>
  </div>

  <h2>Summary</h2>
  <div class="controls">
    <input type="text" placeholder="Search summary..." oninput="textFilter(this,'summary-table')" />
  </div>
  {summary_html}

  <h2 class="mt24">Findings</h2>
  <div class="controls flex">
    <input id="findings-search" type="text" placeholder="Search findings..." oninput="filterFindings()" />
    <label><input type="checkbox" name="levelFilter" value="ERROR" checked onchange="filterFindings()"> <span class="pill ERROR">ERROR</span></label>
    <label><input type="checkbox" name="levelFilter" value="WARN" checked onchange="filterFindings()"> <span class="pill WARN">WARN</span></label>
    <label><input type="checkbox" name="levelFilter" value="INFO" checked onchange="filterFindings()"> <span class="pill INFO">INFO</span></label>
    <span class="counts small">Shown: <strong id="count-shown">0</strong>
      <span class="pill ERROR" id="count-err">0</span>
      <span class="pill WARN" id="count-warn">0</span>
      <span class="pill INFO" id="count-info">0</span>
    </span>
  </div>
  {findings_html}
  <script>{js}</script>
</body>
</html>"""
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return out_html


# --------------------------------------------------------------------------------
# 4) ENTRY POINTS (ArcGIS Pro tool_exec, CLI main)
# --------------------------------------------------------------------------------
def _log(msg: str, level: str = "INFO"):
    if arcpy:
        if level == "ERROR":
            arcpy.AddError(msg)
        elif level == "WARN":
            arcpy.AddWarning(msg)
        else:
            arcpy.AddMessage(msg)
    else:
        print(f"{level}: {msg}")


def _enumerate_csvs(input_path: str) -> Tuple[List[str], str]:
    """
    Return (list_of_csv_paths, output_folder_base).
    If input is a CSV file, list contains that file, output folder = its parent.
    If input is a folder, list contains all *.csv inside, output folder = that folder.
    """
    if not input_path:
        raise ValueError("Input path is empty.")
    input_path = os.path.abspath(input_path)
    if os.path.isfile(input_path):
        if not input_path.lower().endswith(".csv"):
            raise ValueError("Input file is not a CSV.")
        return [input_path], os.path.dirname(input_path)
    if os.path.isdir(input_path):
        csvs = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.lower().endswith(".csv")]
        return csvs, input_path
    raise ValueError(f"Path does not exist: {input_path}")


def tool_exec(input_path: str) -> str:
    """
    Execute the validator for ArcGIS Pro or scripted use.
    - input_path: CSV file or folder
    Returns the path to the HTML dashboard.
    """
    csv_files, output_folder = _enumerate_csvs(input_path)
    if not csv_files:
        raise ValueError("No CSV files found to validate.")
    _log(f"Validating {len(csv_files)} CSV(s)...")
    results, context = run_validation(csv_files, RULES)
    # Write HTML
    html_path = write_report_html(output_folder, results, context)
    return html_path


# ---------------------------- CLI and ArcGIS Pro Bridge -------------------------
def _main_cli(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python validate_csvs_arcgis_AR_modified.py <csv_or_folder>")
        return 2
    input_path = argv[1]
    try:
        html_path = tool_exec(input_path)
    except Exception as e:
        _log(str(e), "ERROR")
        return 1
    _log(f"Dashboard written: {html_path}")
    return 0


if __name__ == "__main__":
    # If called from ArcGIS Pro script tool, arcpy.GetParameterAsText is available.
    if arcpy and hasattr(sys, "stdin") and sys.stdin and hasattr(sys.stdin, "isatty") and not sys.stdin.isatty():
        # Script Tool mode
        in_path = arcpy.GetParameterAsText(0)
        try:
            result_html = tool_exec(in_path)
            # ensure the HTML path is returned to the tool
            _log(f"Dashboard written: {result_html}")
        except Exception as ex:
            _log(str(ex), "ERROR")
            raise
    else:
        # CLI mode
        sys.exit(_main_cli(sys.argv))