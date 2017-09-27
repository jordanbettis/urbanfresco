
import imp

def load_module(fqname):
    """
    Given a fully-qualified module name in dot notation (ex "os.path"),
    load and return the module.
    """
    components = fqname.split(".")
    path = None
    for component in components:
        spec = imp.find_module(component, path)
        path = [spec[1]]
    return imp.load_module(components[-1:][0], *spec)

def load_object(fqname):
    """
    Given a fully-qualified module-level object, ("mod1.mod2.ThisObject"),
    """
    components = fqname.split(".")
    object_name = components[-1:][0]
    module = load_module(".".join(components[:-1]))
    return module.__dict__[object_name]
