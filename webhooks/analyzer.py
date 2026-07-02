import ast
import logging

logger = logging.getLogger(__name__)

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        # We start our counters at zero
        self.stats = {
            'functions': 0,
            'classes': 0,
            'loops': 0
        }

    # Every time the AST finds a function, it triggers this method
    def visit_FunctionDef(self, node):
        self.stats['functions'] += 1
        self.generic_visit(node) # Keep searching inside the function

    # Triggers for classes
    def visit_ClassDef(self, node):
        self.stats['classes'] += 1
        self.generic_visit(node)

    # Triggers for 'for' loops
    def visit_For(self, node):
        self.stats['loops'] += 1
        self.generic_visit(node)

    # Triggers for 'while' loops
    def visit_While(self, node):
        self.stats['loops'] += 1
        self.generic_visit(node)

def analyze_python_code(code_string):
    """
    Parses a string of Python code, builds the AST, and extracts structural metrics.
    """
    try:
        # Convert the raw text into a structural tree
        tree = ast.parse(code_string)
        
        # Send our analyzer to walk through the tree
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        
        return analyzer.stats
    except SyntaxError as e:
        logger.error(f"Syntax error in downloaded code: {e}")
        return {"error": "Invalid Python syntax"}