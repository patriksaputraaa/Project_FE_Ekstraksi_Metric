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

def calculate_wmcnamm_type(class_declaration):
    """
    Calculate WMCNAMM_type (Weighted Methods per Class for Non-Accessor/Mutator Methods)
    This metric calculates the sum of cyclomatic complexity of non-accessor/non-mutator methods in a class
    """
    if class_declaration.body is None:
        return 0
    
    total_cc = 0
    
    # Identifikasi semua properti/atribut kelas untuk menentukan accessor/mutator methods
    class_properties = set()
    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration) or isinstance(member, node.VariableDeclaration):
            if hasattr(member, 'name'):
                class_properties.add(member.name)
    
    # Iterasi melalui semua metode kelas
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Skip jika metode tidak memiliki body
            if member.body is None:
                continue
            
            function_name = member.name
            function_body = str(member.body)
            
            # Cek apakah metode adalah accessor/mutator
            is_accessor_mutator = False
            
            # Pola nama untuk accessor/mutator: get*, set*, is*, has*
            if (function_name.startswith("get") or function_name.startswith("set") or 
                function_name.startswith("is") or function_name.startswith("has")):
                
                # Cek lebih lanjut berdasarkan konten dan nama properti
                property_name = ""
                if function_name.startswith("get"):
                    property_name = function_name[3:].lower()
                elif function_name.startswith("set"):
                    property_name = function_name[3:].lower()
                elif function_name.startswith("is"):
                    property_name = function_name[2:].lower()
                elif function_name.startswith("has"):
                    property_name = function_name[3:].lower()
                
                # Cari properti yang sesuai (case insensitive)
                for prop in class_properties:
                    if prop.lower() == property_name:
                        # Periksa apakah body metode sederhana (hanya return atau assignment)
                        # Ini adalah heuristik sederhana untuk menentukan accessor/mutator
                        body_lines = function_body.strip().split("\n")
                        is_simple = len(body_lines) <= 3  # Metode sederhana biasanya 1-3 baris
                        
                        if is_simple:
                            # Cek pola return/assignment
                            has_return_or_assign = any("return" in line or "=" in line for line in body_lines)
                            if has_return_or_assign:
                                is_accessor_mutator = True
                                break
            
            # Jika bukan accessor/mutator, hitung kompleksitasnya
            if not is_accessor_mutator:
                # Hitung kompleksitas siklomat metode
                cc_value = count_cc_manual(function_body)
                total_cc += cc_value
    
    return total_cc

def calculate_amw_type(class_declaration):
    """
    Calculate AMW_type (Average Method Weight)
    This metric calculates the average cyclomatic complexity of methods in a class
    """
    if class_declaration.body is None:
        return 0
    
    method_cc_values = []
    
    # Iterasi melalui semua metode kelas
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Skip jika metode tidak memiliki body
            if member.body is None:
                continue
            
            # Hitung kompleksitas siklomat metode
            function_body = str(member.body)
            cc_value = count_cc_manual(function_body)
            method_cc_values.append(cc_value)
    
    # Hitung rata-rata kompleksitas
    if method_cc_values:
        return sum(method_cc_values) / len(method_cc_values)
    else:
        return 0  # Jika tidak ada metode, kembalikan 0

def count_nocs_package(directory):
    """
    Calculate NOCS_package (Number of Classes in a Package)
    This metric counts the number of classes in each package
    
    Returns a dictionary mapping package names to their class counts
    """
    # Dictionary untuk menyimpan jumlah kelas per package
    package_class_counts = {}
    
    # Temukan semua file Kotlin dalam direktori
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) 
                  for f in files if f.endswith(".kt") or f.endswith(".kts")]
    
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            
            # Dapatkan nama paket
            package_name = result.package.name if result.package else "default"
            
            # Hitung jumlah kelas dalam file ini
            class_count = sum(1 for decl in result.declarations if isinstance(decl, node.ClassDeclaration))
            
            # Update jumlah kelas untuk paket ini
            if package_name in package_class_counts:
                package_class_counts[package_name] += class_count
            else:
                package_class_counts[package_name] = class_count
                
        except Exception:
            # Jika file tidak dapat di-parse, lanjutkan ke file berikutnya
            continue
    
    return package_class_counts

def calculate_lcom5(class_declaration):
    """
    Calculate LCOM5 (Lack of Cohesion in Methods) 
    Uses a simplified approach based on method body similarity
    """
    if class_declaration.body is None:
        return 0
    
    # Collect all methods with bodies
    methods = []
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration) and member.body is not None:
            methods.append(member)
    
    # Need at least 2 methods for LCOM5 calculation
    if len(methods) < 2:
        return 0
    
    # Calculate method pairs and their similarity
    total_pairs = 0
    cohesive_pairs = 0
    
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            total_pairs += 1
            
            # Get method bodies as strings (same way as your other metrics)
            body1 = str(methods[i].body) if methods[i].body else ""
            body2 = str(methods[j].body) if methods[j].body else ""
            
            if body1 and body2:
                # Split into tokens and find common meaningful tokens
                tokens1 = set(body1.split())
                tokens2 = set(body2.split())
                
                # Remove common programming constructs
                common_keywords = {
                    'if', 'else', 'for', 'while', 'return', 'var', 'val', 'fun', 
                    'this', 'null', 'true', 'false', 'it', 'when', 'is', 'as',
                    '{', '}', '(', ')', '[', ']', ';', ',', '.', '=', '+', '-', 
                    '*', '/', '&&', '||', '!', '<', '>', '<=', '>=', '==', '!=',
                    'private', 'public', 'protected', 'internal', 'override'
                }
                
                # Filter out keywords and short tokens
                meaningful_tokens1 = {token for token in tokens1 
                                    if token not in common_keywords and len(token) > 2}
                meaningful_tokens2 = {token for token in tokens2 
                                    if token not in common_keywords and len(token) > 2}
                
                # Check if methods share meaningful tokens (indicating shared attributes/functionality)
                shared_tokens = meaningful_tokens1 & meaningful_tokens2
                if len(shared_tokens) > 0:
                    cohesive_pairs += 1
    
    if total_pairs == 0:
        return 0
    
    # LCOM5 = 1 - (cohesive pairs / total pairs)
    # Higher values indicate lower cohesion
    lcom5 = 1 - (cohesive_pairs / total_pairs)
    
    # Ensure result is between 0 and 1
    return max(0.0, min(1.0, lcom5))

def extracted_method(file_path, noi_count, nom_count, nomnamm_count, nocs_package_counts):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"
        
        # Dapatkan NOCS_package untuk paket ini
        nocs_package = nocs_package_counts.get(package_name, 0)
        
        if not result.declarations:
            return [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, "Max Nesting": 0, 
                    "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, 
                    "NOC_type": 0, "WMC_type": 0, "LCOM5": 0, "WMCNAMM_type": 0, "AMW_type": 0,
                    "NOCS_package": nocs_package, "Error": "No class declaration found"}]
        
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
            # Calculate LCOM5 for this class
            lcom5_value = calculate_lcom5(class_declaration)
            # Calculate WMCNAMM_type for this class
            wmcnamm_type = calculate_wmcnamm_type(class_declaration)
            # Calculate AMW_type for this class
            amw_type = calculate_amw_type(class_declaration)
            
            if class_declaration.body is None:
                datas.append({"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, 
                            "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                            "NOMNAMM": nomnamm_count, "NOC_type": noc_type, "WMC_type": wmc_type, 
                            "LCOM5": lcom5_value, "WMCNAMM_type": wmcnamm_type, "AMW_type": amw_type,
                            "NOCS_package": nocs_package, "Error": "Class has no body"})
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
                             "NOC_type": noc_type, "WMC_type": wmc_type, "LCOM5": lcom5_value, 
                             "WMCNAMM_type": wmcnamm_type, "AMW_type": amw_type, "NOCS_package": nocs_package})
                
            if not method_function:
                datas.append({"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, 
                            "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                            "NOMNAMM": nomnamm_count, "NOC_type": noc_type, "WMC_type": wmc_type, 
                            "LCOM5": lcom5_value, "WMCNAMM_type": wmcnamm_type, "AMW_type": amw_type,
                            "NOCS_package": nocs_package, "Error": "No functions found"})
                
        return datas if datas else [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, 
                                   "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                                   "NOMNAMM": nomnamm_count, "NOC_type": 0, "WMC_type": 0, "LCOM5": 0, 
                                   "WMCNAMM_type": 0, "AMW_type": 0, "NOCS_package": nocs_package,
                                   "Error": "No class declarations found"}]
    except Exception as e:
        return [{"Package": "Error", "Class": "Error", "Method": "Error", "LOC": "Error", 
                "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                "NOMNAMM": nomnamm_count, "NOC_type": 0, "WMC_type": 0, "LCOM5": 0, 
                "WMCNAMM_type": 0, "AMW_type": 0, "NOCS_package": 0, "Error": str(e)}]

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
            
            # Hitung NOCS_package
            nocs_package_counts = count_nocs_package(temp_dir)
            
            results = []
            for kotlin_file in [os.path.join(root, f) for root, _, files in os.walk(temp_dir) 
                              for f in files if f.endswith(".kt") or f.endswith(".kts")]:
                file_results = extracted_method(kotlin_file, noi_count, nom_count, nomnamm_count, nocs_package_counts)
                results.extend(file_results)
            return pd.DataFrame(results)
        except Exception as e:
            return str(e)