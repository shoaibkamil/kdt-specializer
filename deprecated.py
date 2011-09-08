####
####
# This file is a temporary placeholder for (potentially) deprecated code taken from the specializer,
# mostly for when it couldn't support using the Asp infrastructure.
####
####



class IfNotDefined(cpp_ast.Generable):
    """
    A generable AST node for the 'if not defined' (#ifndef) directive.
    Accepts argument 'symbol', the token to check for defined status.
    """
    def __init__(self, symbol):
        self.symbol = symbol

    def generate(self):
        yield "#ifndef %s" % self.symbol

class EndIf(cpp_ast.Generable):
    """
    A generable AST node for the 'end if' (#endif) directive.
    """
    def generate(self):
        yield "#endif"


class CMakeModule(object):
    """
    This module is a (still somewhat hacky) mimic of the style of CodePy's Boost
    Python module in order to add support for including ASP-generated code in
    projects which use GNU make for a build system.
    Note that the compile() member method is specific to the pyCombBLAS project
    makefile that accepts a DYNFILE= command line argument, the filename of a
    dynamically generated file.
    Arguments:
    temp_dir - Directory to store dynamically generated cpp, header, and SWIG interface files.
    makefile_dir - Directory of the makefile.
    name - A name given to the generated files.
    namespace - A namespace to include all code generated in.
    include_files - A list of files to #include at the top of the header and cpp files.
    """
    def __init__(self, temp_dir, makefile_dir, name="module", namespace=None, include_files=[]):
        self.name = name
        self.preamble = []
        self.mod_body = []
        self.header_body = []
        self.namespace = namespace
        self.temp_dir = temp_dir
        self.makefile_dir = makefile_dir
        self.include_files = include_files

    def include_file(self, filepath):
        self.include_files.append(filepath)

    def add_to_preamble(self, pa):
        self.preamble.extend(pa)

    def add_to_module(self, body):
        self.mod_body.extend(body)

    def add_function(self, func):
        """*func* is a :class:`cgen.FunctionBody`."""

        self.mod_body.append(func)

        # Want the prototype for the function added to the header.
        self.header_body.append(func.fdecl)

    def add_struct(self, struct):
        self.mod_body.append(struct)

    def generate(self):
        source = []
        if self.namespace is not None:
            self.mod_body = [Namespace(self.namespace, cpp_ast.Block(self.mod_body))]

        print "Got to 1"
        self.preamble += [cpp_ast.Include(self.temp_dir+self.name+".h", system=False)]
        for include in self.include_files:
            self.preamble += [cpp_ast.Include(include, system=False)]
        print "Got to 2"
        source += self.preamble + [codepy.cgen.Line()] + self.mod_body
        print "Got to 3"
        return codepy.cgen.Module(source)

    def generate_header(self):
        header = []
            
        if self.namespace is not None:
            self.header_body = [Namespace(self.namespace, cpp_ast.Block(self.header_body))]

        header_top = [IfNotDefined(self.name+"_H"), cpp_ast.Define(self.name+"_H", "")]
        for include in self.include_files:
            header_top += [cpp_ast.Include(include, system=False)]
        
        header += header_top + self.header_body + [EndIf()]
        return codepy.cgen.Module(header)

    def generate_swig_interface(self):
        interface_string = "%module " + self.name + "\n"
        interface_string += "%{\n"
        interface_string += str(cpp_ast.Include(self.temp_dir+self.name+".h", system=False))
        interface_string += "\n"
        interface_string += "%}\n"
        interface_string += "".join([str(line) for line in self.header_body])
        return interface_string

    def compile(self):
        from os import getcwd, chdir
        from subprocess import call
        original_dir = getcwd()
        chdir(self.temp_dir)

        header_file = open(self.name + ".h", 'w')
        print >>header_file, self.generate_header()
        header_file.close()

        cpp_file = open(self.name + ".cpp", 'w')
        print >>cpp_file, self.generate()
        cpp_file.close()

        i_file = open(self.name + ".i", 'w')
        print >>i_file, self.generate_swig_interface()
        i_file.close()

        chdir(self.makefile_dir)
        args = ["make", "DYNFILE="+self.temp_dir+self.name]
        call(args)

        chdir(original_dir)

class Operator(object):
    """
    Class to represent the data associated with an operator.
    Used a class because empty fields are nicer than with NamedTuple.
    """
    def __init__(self, name, assoc=None, comm=None, src=None, ast=None):
        self.name = name
        self.src = src
        self.ast = ast
        self.assoc = assoc
        self.comm = comm
