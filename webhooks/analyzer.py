import ast
import logging

logger = logging.getLogger(__name__)

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.stats = {
            'functions': 0,
            'classes': 0,
            'loops': 0,
            'complexity': 1  # Base complexity is always 1
        }

    def visit_FunctionDef(self, node):
        self.stats['functions'] += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.stats['classes'] += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.stats['loops'] += 1
        self.stats['complexity'] += 1  # Loop = decision path (+1)
        self.generic_visit(node)

    def visit_While(self, node):
        self.stats['loops'] += 1
        self.stats['complexity'] += 1  # Loop = decision path (+1)
        self.generic_visit(node)

    def visit_If(self, node):
        self.stats['complexity'] += 1  # If statement = decision path (+1)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.stats['complexity'] += 1  # Try/Except = decision path (+1)
        self.generic_visit(node)
        
    def visit_ListComp(self, node):
        self.stats['complexity'] += 1  # List comprehension = hidden loop (+1)
        self.generic_visit(node)

def analyze_python_code(code_string):
    """
    Parses a string of Python code, builds the AST, and extracts structural metrics including Cyclomatic Complexity.
    """
    try:
        tree = ast.parse(code_string)
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        return analyzer.stats
    except SyntaxError as e:
        logger.error(f"Syntax error in downloaded code: {e}")
        return {"error": "Invalid Python syntax"}