import os
import tempfile
import logging
import patoolib
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from kopyt import Parser, node

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def manual_max_nesting(body_str: str) -> int:
    """
    Calculate the maximum nesting depth of control structures in a method body.
    
    Args:
        body_str: The method body as a string
        
    Returns:
        Maximum nesting depth found
    """
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

def count_cc_manual(method_code: str) -> int:
    """
    Calculate cyclomatic complexity of a method.
    
    Args:
        method_code: The method code as a string
        
    Returns:
        Cyclomatic complexity score
    """
    cc = 1
    control_keywords = ["if", "for", "while", "when", "catch", "case", "&&", "||"]
    lines = method_code.split("\n")
    for line in lines:
        stripped = line.strip()
        for keyword in control_keywords:
            if keyword in ["&&", "||"]:
                cc += stripped.count(keyword)
            elif stripped.startswith(keyword):
                cc += 1
    return cc

def count_woc(cc_values: List[int]) -> List[float]:
    """
    Calculate Weight of Class for each method.
    
    Args:
        cc_values: List of cyclomatic complexities for all methods in a class
        
    Returns:
        List of WOC values for each method
    """
    total_CC = sum(cc_values)
    return [cc / total_CC if total_CC else 0 for cc in cc_values]

def scan_kotlin_files(directory: str) -> Dict[str, str]:
    """
    Scan directory for Kotlin files and return their contents.
    
    Args:
        directory: Path to directory to scan
        
    Returns:
        Dictionary mapping file paths to their contents
    """
    kotlin_files = {}
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith((".kt", ".kts")):
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        kotlin_files[file_path] = file.read()
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
    return kotlin_files

def count_interface_declarations(code: str) -> int:
    """
    Count interface declarations in Kotlin code.
    
    Args:
        code: Kotlin code to analyze
        
    Returns:
        Number of interface declarations
    """
    try:
        parser = Parser(code)
        result = parser.parse()
        return sum(1 for decl in result.declarations 
                 if isinstance(decl, node.InterfaceDeclaration))
    except Exception as e:
        logger.error(f"Error counting interfaces: {e}")
        return 0

def count_method_declarations(code: str, exclude_accessors: bool = False) -> int:
    """
    Count method declarations in Kotlin code.
    
    Args:
        code: Kotlin code to analyze
        exclude_accessors: Whether to exclude getter/setter methods
        
    Returns:
        Number of method declarations
    """
    try:
        parser = Parser(code)
        result = parser.parse()
        count = 0
        
        for declaration in result.declarations:
            if hasattr(declaration, "body") and declaration.body:
                for member in declaration.body.members:
                    if isinstance(member, node.FunctionDeclaration):
                        if exclude_accessors:
                            if not (member.name.startswith("get") or 
                                   member.name.startswith("set")):
                                count += 1
                        else:
                            count += 1
        return count
    except Exception as e:
        logger.error(f"Error counting methods: {e}")
        return 0

def analyze_file_metrics(file_path: str, code: str, 
                        noi_count: int, nom_count: int, 
                        nomnamm_count: int) -> List[Dict]:
    """
    Analyze metrics for all methods in a Kotlin file.
    
    Args:
        file_path: Path to Kotlin file
        code: Contents of the file
        noi_count: Number of interfaces in project
        nom_count: Number of methods in project
        nomnamm_count: Number of non-accessor methods in project
        
    Returns:
        List of metric dictionaries for each method
    """
    try:
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"
        
        all_metrics = []
        
        for declaration in result.declarations:
            if not hasattr(declaration, "body") or not declaration.body:
                continue
                
            class_name = getattr(declaration, "name", "Anonymous")
            class_metrics = analyze_class_body(
                declaration.body,
                package_name,
                class_name,
                noi_count,
                nom_count,
                nomnamm_count
            )
            all_metrics.extend(class_metrics)
            
        return all_metrics if all_metrics else [
            create_empty_metrics(package_name, "Unknown", noi_count, nom_count, nomnamm_count)
        ]
        
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        return [
            create_error_metrics(noi_count, nom_count, nomnamm_count, str(e))
        ]

def analyze_class_body(class_body: node.ClassBody, 
                      package_name: str, 
                      class_name: str,
                      noi_count: int,
                      nom_count: int,
                      nomnamm_count: int) -> List[Dict]:
    """
    Analyze metrics for all methods in a class body.
    
    Args:
        class_body: The class body AST node
        package_name: Name of the package
        class_name: Name of the class
        noi_count: Number of interfaces in project
        nom_count: Number of methods in project
        nomnamm_count: Number of non-accessor methods in project
        
    Returns:
        List of metric dictionaries for each method
    """
    methods = [m for m in class_body.members 
              if isinstance(m, node.FunctionDeclaration)]
    
    if not methods:
        return [
            create_empty_metrics(package_name, class_name, noi_count, nom_count, nomnamm_count)
        ]
    
    method_metrics = []
    cc_values = []
    
    # First pass: collect basic metrics and CC values
    for method in methods:
        method_name = method.name
        body_str = str(method.body) if method.body else ""
        
        metrics = {
            "loc": body_str.count("\n") + 1 if method.body else 0,
            "max_nesting": manual_max_nesting(body_str),
            "cc": count_cc_manual(body_str),
            "name": method_name
        }
        method_metrics.append(metrics)
        cc_values.append(metrics["cc"])
    
    # Calculate WOC values
    woc_values = count_woc(cc_values)
    
    # Prepare final results
    results = []
    for metrics, woc in zip(method_metrics, woc_values):
        results.append({
            "Package": package_name,
            "Class": class_name,
            "Method": metrics["name"],
            "LOC": metrics["loc"],
            "Max Nesting": metrics["max_nesting"],
            "CC": metrics["cc"],
            "WOC": woc,
            "NOI": noi_count,
            "NOM": nom_count,
            "NOMNAMM": nomnamm_count
        })
    
    return results

def create_empty_metrics(package: str, class_name: str,
                       noi_count: int, nom_count: int,
                       nomnamm_count: int) -> Dict:
    """Create metrics dictionary for empty classes."""
    return {
        "Package": package,
        "Class": class_name,
        "Method": "None",
        "LOC": 0,
        "Max Nesting": 0,
        "CC": 0,
        "WOC": 0,
        "NOI": noi_count,
        "NOM": nom_count,
        "NOMNAMM": nomnamm_count,
        "Error": "No methods found"
    }

def create_error_metrics(noi_count: int, nom_count: int,
                       nomnamm_count: int, error_msg: str) -> Dict:
    """Create metrics dictionary for error cases."""
    return {
        "Package": "Error",
        "Class": "Error",
        "Method": "Error",
        "LOC": "Error",
        "Max Nesting": 0,
        "CC": 0,
        "WOC": 0,
        "NOI": noi_count,
        "NOM": nom_count,
        "NOMNAMM": nomnamm_count,
        "Error": error_msg
    }

def analyze_project(directory: str) -> pd.DataFrame:
    """
    Analyze all Kotlin files in a project directory.
    
    Args:
        directory: Path to project directory
        
    Returns:
        DataFrame containing all collected metrics
    """
    kotlin_files = scan_kotlin_files(directory)
    
    # Count project-level metrics
    noi_count = sum(count_interface_declarations(code) for code in kotlin_files.values())
    nom_count = sum(count_method_declarations(code) for code in kotlin_files.values())
    nomnamm_count = sum(count_method_declarations(code, True) for code in kotlin_files.values())
    
    # Analyze each file
    all_results = []
    for file_path, code in kotlin_files.items():
        file_results = analyze_file_metrics(
            file_path, code, noi_count, nom_count, nomnamm_count
        )
        all_results.extend(file_results)
    
    return pd.DataFrame(all_results)

def extract_and_parse(file) -> Union[pd.DataFrame, str]:
    """
    Extract and analyze a compressed archive containing Kotlin code.
    
    Args:
        file: File-like object containing the archive
        
    Returns:
        DataFrame with metrics or error message
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        
        try:
            # Save the uploaded file
            with open(temp_file_path, "wb") as f:
                f.write(file.getbuffer())
            
            # Extract archive
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            
            # Analyze the project
            return analyze_project(temp_dir)
            
        except Exception as e:
            logger.error(f"Error processing archive: {e}")
            return str(e)