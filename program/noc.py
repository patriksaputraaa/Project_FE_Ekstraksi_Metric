# fungsi ini tidak menghitung class external, yang menghitung external class ada di controller.py

from kopyt import Parser
from kopyt.node import ClassDeclaration, InterfaceDeclaration

code = """
open class Vehicle
class Car : Vehicle()
interface Engine
class Motorcycle : Vehicle(), Engine
"""

parser = Parser(code)
ast = parser.parse()

for decl in ast.declarations:
    if isinstance(decl, ClassDeclaration):
        print(f"Class: {decl.name}")
        
        # Process supertypes to find inheritance relationships
        if decl.supertypes:
            extends = []
            implements = []
            
            for supertype in decl.supertypes:
                # Extract the name from the supertype structure
                # For constructor invocations (class inheritance with parentheses)
                if hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'invoker'):
                    if hasattr(supertype.delegate.invoker, 'sequence') and supertype.delegate.invoker.sequence:
                        name = supertype.delegate.invoker.sequence[0].name
                        extends.append(name)
                # For direct type references (interface implementation)
                elif hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'sequence'):
                    if supertype.delegate.sequence:
                        name = supertype.delegate.sequence[0].name
                        implements.append(name)
            
            if extends:
                print(f"  Extends: {extends}")
            if implements:
                print(f"  Implements: {implements}")
    
    elif isinstance(decl, InterfaceDeclaration):
        print(f"Interface: {decl.name}")