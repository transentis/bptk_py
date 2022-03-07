class Module():
    """
    The Module class is used to structure SD DSL models into individual modules. 
    Modules can be nested. If you create model elements such as stocks, flows and
    converters via the module, the elments are added to the model, but the element
    names are turned into fully qualified names of the form 
    `parent_module_name.module_name.name`. The fully qualfied name is used as the equation
    name in the Model class and is needed when making calls to `bptk.run_scenario` or 
    `bptk.plot_scenario`.

    Check our `Beer Distribution Game <https://github.com/transentis/beergame/blob/master/beergame_sd_dsl.ipynb>`_ model to see how to use the Module class
    """
    def __init__(self, model, name, parent=None):
        """
        Override the ___init___ method in your subclass and declare all expported
        model elements there. Be sure to call super().___init___ 

        Args:
            model: Model
                The Model class.
            name: String
                The name of the module.
            parent: Module (Optional)
                The parent of the module.
        """
        self.name = name
        self.model = model
        self.parent = parent
    
    def fqn(self,name):
        """
        Given a name this returns the fully qualified name, i.e. name prefixed
        by the module namespace.

        Args:
            name: String
                The name that is to be converted into a fully qualified name.
        
        Returns the fully qualified name, i.e. namespace.name. The namespace is defined
        by the names of all the parent modules, e.g. parent_module_name.module_name
        """
        if self.parent:
            return self.parent.fqn(self.name)+"."+name
        else:
            return self.name + "." + name

    def stock(self,name):
        """
        Add a stock to the model. The name of the stock will be a fully qualified name
        consisting of all nested module names plus the actual element name using dot
        notation, i.e. namespace.name
        """
        return self.model.stock(self.fqn(name))
    
    def flow(self,name):
        """
        Add a flow to the model. The name of the flow will be a fully qualified name
        consisting of all nested module names plus the actual element name using dot
        notation, i.e. namespace.name
        """
        return self.model.flow(self.fqn(name))

    def biflow(self,name):
        """
        Add a biflow to the model. The name of the biflow will be a fully qualified name
        consisting of all nested module names plus the actual element name using dot
        notation, i.e. namespace.name
        """
        return self.model.biflow(self.fqn(name))


    def converter(self,name):
        """
        Add a converter to the model. The name of the converter will be a fully qualified name
        consisting of all nested module names plus the actual element name using dot
        notation, i.e. namespace.name
        """
        return self.model.converter(self.fqn(name))
 
    def constant(self,name):
        """
        Add a constanst to the model. The name of the constant will be a fully qualified name
        consisting of all nested module names plus the actual element name using dot
        notation, i.e. namespace.name
        """
 
        return self.model.constant(self.fqn(name))

    @property
    def points(self):
        return self.model.points

    def initialize(self):
        """
        Override this method in concrete Module subclasses. All elements that 
        are internal to the module should be declared here and the equations
        for both the exported elements as well as the internal elements should
        be defined here.
        """
        pass

 