import ast

class SafetyError(Exception):
    pass

class ASTScanner(ast.NodeVisitor):
    def __init__(self):
        self.blocked_modules = {'os', 'subprocess', 'sys', 'shutil'}
        self.blocked_functions = {'eval', 'exec', 'open', '__import__'}
        self.errors = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.blocked_modules:
                self.errors.append(f"Blocked import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in self.blocked_modules:
            self.errors.append(f"Blocked import from: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.blocked_functions:
                self.errors.append(f"Blocked function call: {node.func.id}")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.blocked_functions:
                self.errors.append(f"Blocked attribute call: {node.func.attr}")
        self.generic_visit(node)

def check_code_safety(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SafetyError(f"Syntax Error in generated code: {e}")
    
    scanner = ASTScanner()
    scanner.visit(tree)
    
    if scanner.errors:
        raise SafetyError(f"Safety violations found:\n" + "\n".join(scanner.errors))
    
    return True

def pre_check_prompt_injection(user_input: str) -> bool:
    # A simple check for XML tags to ensure they aren't trying to break out
    if "</user_input>" in user_input or "<system>" in user_input:
        return False
    return True
