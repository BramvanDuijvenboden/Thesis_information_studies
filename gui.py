# Martijn Dortmond 2018
# Graphical interface for doing sobel sensitivity analysis from a Vensim model file.

from tkinter import *
from tkinter import ttk



class GUI():
    def __init__(self, root, constants, stocks, flows, analyzer ):
        self.root = root
        #root.title("Sensitivity analysis")
        self.constants = constants
        self.stocks = stocks
        self.flows = flows
        self.analyzer = analyzer
        self.create_gui_elements()


    
    def parameter_gui(self, what, classifier_name):
        for name in what:
            self.row += 1
            Label(self.root, text=name).grid(row = self.row, column = 0)
            min = Entry(self.root)
            max = Entry(self.root)

            self.parameter_widgets[name] = [classifier_name , min, max]
            # Set widgets location
            min.grid(row = self.row, column = 2)
            max.grid(row = self.row, column = 3)


    def create_gui_elements(self):
        self.parameter_widgets = {}
        self.row = 0
            
        # Create column headers
        Label(self.root, text="All possible constants").grid(row = self.row)
        Label(self.root, text="min bound").grid(row = self.row, column = 2)
        Label(self.root, text="max bound").grid(row = self.row, column = 3)

        # Create a list with all possible paramters
        self.parameter_gui(self.constants, "constant")
        self.row += 1
        Label(self.root, text="All possible initial conditions").grid(row = self.row)
        self.parameter_gui(self.stocks, "initial")

        submitbutton = Button(self.root, text="set parameters")
        submitbutton.bind("<Button-1>", self.set_params)
        self.row +=1
        submitbutton.grid(row = self.row, column = 3)

        # Selective output box
        output = StringVar(self.root)
        self.analyzer.output = output
        output.set(self.stocks[0])
        self.row += 1
        Label(self.root, text = "Select output").grid(row = self.row, column = 0)
        OptionMenu(self.root, output, *(sorted(self.stocks + self.flows))).grid(row = self.row, column = 1)

        runbutton = Button(self.root, text="run sensitivity analysis")
        runbutton.bind("<Button-1>", self.analyzer.start_simulation)
        self.row +=1
        runbutton.grid(row = self.row)
             
           

    def set_params(self, event):
        bounds = []
        constants_included = []
        initial_included = []

        # loop over widgets and select the ones that have values
        for key, value in self.parameter_widgets.items():
            # if not empty then add it
            min = value[1].get()
            max = value[2].get()
            if (min == "" or max == ""):
                continue
            else:
                min = float(min)
                max = float(max)

            # Check for correctness of input, may create lot of overhead
            if max < min:
                 value[1].config({"background": "Red"})
                 value[2].config({"background": "Red"})
                 print ("Maximum value is smaller than minimum value!")
                 break
            else:
                 value[1].config({"background": "White"})
                 value[2].config({"background": "White"})

            if value[0] == "constant":
                constants_included.append(key)
            else:
                initial_included.append(key)

            bounds.append([min, max])

        # Set values in analyzer
        self.analyzer.bounds = bounds
        self.analyzer.constants_included = constants_included
        self.analyzer.initial_included = initial_included
