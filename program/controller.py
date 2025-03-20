import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node

def manual_max_nesting(body_str):
    indent_levels = []
    max_depth = 0
    for line in body_str.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("if", "try", "for", "catch", "else", "when")):
            indent_levels.append(stripped)
            max_depth = max(max_depth, len(indent_levels))
        elif stripped == "}":
            if indent_levels:
                indent_levels.pop()
    return max_depth

def count_cc_manual(method_code):
    cc = 1
    control_keywords = ["if", "for", "while", "when", "catch", "case"]
    lines = method_code.split("\n")
    for line in lines:
        stripped = line.strip()
        for keyword in control_keywords:
            if stripped.startswith(keyword):
                cc += 1
    return cc

def count_woc(cc_values):
    total_CC = sum(cc_values)
    return [cc / total_CC if total_CC else 0 for cc in cc_values]

def count_noi(directory):
    noi_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if isinstance(declaration, node.InterfaceDeclaration):
                    noi_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return noi_count

def count_nom(directory):
    nom_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if hasattr(declaration, "body") and declaration.body:
                    for member in declaration.body.members:
                        if isinstance(member, node.FunctionDeclaration):
                            nom_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return nom_count

def count_nomnamm(directory):
    nomnamm_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if hasattr(declaration, "body") and declaration.body:
                    for member in declaration.body.members:
                        if isinstance(member, node.FunctionDeclaration):
                            if not (member.name.startswith("get") or member.name.startswith("set")):
                                nomnamm_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return nomnamm_count

def extracted_method(file_path, noi_count, nom_count, nomnamm_count):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"
        if not result.declarations:
            return [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, "Error": "No class declaration found"}]
        class_declaration = result.declarations[0]
        class_name = class_declaration.name
        if class_declaration.body is None:
            return [{"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, "Error": "Class has no body"}]
        datas = []
        method_function = {}
        for member in class_declaration.body.members:
            if isinstance(member, node.FunctionDeclaration):
                function_names = member.name
                loc_count = str(member.body).count("\n") + 1 if member.body else 0
                maxnesting = manual_max_nesting(str(member.body)) if member.body else 0
                cc_value = count_cc_manual(str(member.body)) if member.body else 0
                method_function[function_names] = (cc_value, loc_count, maxnesting)
        cc_values = [cc for cc, _, _ in method_function.values()]
        woc_values = count_woc(cc_values)
        for (function_names, (cc_value, loc_count, maxnesting)), woc in zip(method_function.items(), woc_values):
            datas.append({"Package": package_name, "Class": class_name, "Method": function_names, "LOC": loc_count, "Max Nesting": maxnesting, "CC": cc_value, "WOC": woc, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count})
        return datas if datas else [{"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, "Error": "No functions found"}]
    except Exception as e:
        return [{"Package": "Error", "Class": "Error", "Method": "Error", "LOC": "Error", "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, "Error": str(e)}]

def extract_and_parse(file):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            noi_count = count_noi(temp_dir)
            nom_count = count_nom(temp_dir)
            nomnamm_count = count_nomnamm(temp_dir)
            results = []
            for kotlin_file in [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt") or f.endswith(".kts")]:
                results.extend(extracted_method(kotlin_file, noi_count, nom_count, nomnamm_count))
            return pd.DataFrame(results)
        except Exception as e:
            return str(e)
