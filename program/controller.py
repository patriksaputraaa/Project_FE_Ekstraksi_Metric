import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node
from kopyt.node import ClassDeclaration  # Perhatikan perubahan di sini

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

def count_noc_type(directory, include_external_classes=True):
    import os
    from kopyt import Parser
    from kopyt.node import ClassDeclaration, InterfaceDeclaration
    
    classes = {}  # {class_name: [superclasses]}
    all_classes = set()
    external_classes = set()  # For tracking external superclasses

    kotlin_files = [
        os.path.join(root, f) 
        for root, _, files in os.walk(directory) 
        for f in files if f.endswith(".kt") or f.endswith(".kts")
    ]

    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            parser = Parser(code)
            kotlin_file = parser.parse()
            
            for decl in kotlin_file.declarations:
                if isinstance(decl, ClassDeclaration) or isinstance(decl, InterfaceDeclaration):
                    class_name = decl.name
                    all_classes.add(class_name)
                    
                    super_types = []
                    
                    # Process supertypes to find inheritance relationships
                    if hasattr(decl, 'supertypes') and decl.supertypes:
                        for supertype in decl.supertypes:
                            super_name = None
                            
                            # Extract the name from the supertype structure
                            # For constructor invocations (class inheritance with parentheses)
                            if hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'invoker'):
                                if hasattr(supertype.delegate.invoker, 'sequence') and supertype.delegate.invoker.sequence:
                                    super_name = supertype.delegate.invoker.sequence[0].name
                            
                            # For direct type references (interface implementation)
                            elif hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'sequence'):
                                if supertype.delegate.sequence:
                                    super_name = supertype.delegate.sequence[0].name
                            
                            if super_name:
                                super_types.append(super_name)
                                print(f"Found inheritance relationship: {class_name} extends/implements {super_name}")
                                
                                # Track external superclasses (not declared in your code)
                                if super_name not in all_classes:
                                    external_classes.add(super_name)
                    
                    classes[class_name] = super_types
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")

    # Add external classes to tracking if requested
    if include_external_classes:
        for ext_class in external_classes:
            all_classes.add(ext_class)

    # Initialize NOC count
    class_hierarchy = {cls: 0 for cls in all_classes}

    # Count subclass relationships
    for class_name, super_types in classes.items():
        for super_type in super_types:
            simple_super_type = super_type.split('.')[-1]  # Handle qualified names
            
            if simple_super_type in class_hierarchy:
                class_hierarchy[simple_super_type] += 1
                print(f"Inheritance counted: {simple_super_type} now has {class_hierarchy[simple_super_type]} children")
            else:
                print(f"Warning: Superclass '{simple_super_type}' not found in tracked classes")

    return class_hierarchy

# Function to calculate WMC for a single class
def calculate_wmc_for_class(class_declaration):
    """Calculate WMC (Weighted Methods per Class) for a single class declaration"""
    if class_declaration.body is None:
        return 0
        
    wmc_value = 0
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Calculate complexity for this function
            cc_value = count_cc_manual(str(member.body)) if member.body else 0
            wmc_value += cc_value
            
    return wmc_value

def extracted_method(file_path, noi_count, nom_count, nomnamm_count):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"
        if not result.declarations:
            return [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, "Max Nesting": 0, 
                    "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, 
                    "NOC_type": 0, "WMC_type": 0, "Error": "No class declaration found"}]
        
        # Get NOC_type mapping for the directory
        directory = os.path.dirname(file_path)
        noc_type_mapping = count_noc_type(directory)
        
        datas = []
        for class_declaration in result.declarations:
            if not isinstance(class_declaration, node.ClassDeclaration):
                continue
                
            class_name = class_declaration.name
            noc_type = noc_type_mapping.get(class_name, 0)
            # Calculate WMC for this class
            wmc_type = calculate_wmc_for_class(class_declaration)
            
            if class_declaration.body is None:
                datas.append({"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, 
                            "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                            "NOMNAMM": nomnamm_count, "NOC_type": noc_type, "WMC_type": wmc_type, 
                            "Error": "Class has no body"})
                continue
                
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
                datas.append({"Package": package_name, "Class": class_name, "Method": function_names, 
                             "LOC": loc_count, "Max Nesting": maxnesting, "CC": cc_value, "WOC": woc, 
                             "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, 
                             "NOC_type": noc_type, "WMC_type": wmc_type})
                
            if not method_function:
                datas.append({"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, 
                            "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                            "NOMNAMM": nomnamm_count, "NOC_type": noc_type, "WMC_type": wmc_type, 
                            "Error": "No functions found"})
                
        return datas if datas else [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, 
                                   "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                                   "NOMNAMM": nomnamm_count, "NOC_type": 0, "WMC_type": 0, 
                                   "Error": "No class declarations found"}]
    except Exception as e:
        return [{"Package": "Error", "Class": "Error", "Method": "Error", "LOC": "Error", 
                "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                "NOMNAMM": nomnamm_count, "NOC_type": 0, "WMC_type": 0, "Error": str(e)}]
    
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
            for kotlin_file in [os.path.join(root, f) for root, _, files in os.walk(temp_dir) 
                              for f in files if f.endswith(".kt") or f.endswith(".kts")]:
                results.extend(extracted_method(kotlin_file, noi_count, nom_count, nomnamm_count))
            return pd.DataFrame(results)
        except Exception as e:
            return str(e)