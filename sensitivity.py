# Martijn Dortmond 2018
# Wrapper for doing sobel sensitivity analysis from a Vensim model file.

import gui
import pysd
from SALib.sample import saltelli
from SALib.analyze import sobol
import numpy as np
from tkinter import *



def find_parameters(model_components):
    """Generate a list with all parameters / initial conditions of stocksself,
    as these can be used for sensitivity analysis. """

    constants_candidate = []
    constants = []
    stocks = []
    flows = []
    eqn = ""

    # Loop over all python component variables and select type
    for component in model_components:
        attribute = model.components._namespace[component]
        docstring = getattr(model.components, attribute).__doc__

        #Generate the type (component or constant)
        lines = docstring.split('\n')
        thetype = lines[5].replace("Type:", "").strip()
        if thetype == "constant":
            constants_candidate.append(component)
        elif 'INTEG' in lines[2]:
            stocks.append(component)
            eqn += lines[2]
        else:
            flows.append(component)
            
    # Check for already present initial condition
    for constant in constants_candidate:
        if constant in eqn:
            continue
        else:
            constants.append(constant)
            
                   
    # Sorted to preserve order in the GUI
    return sorted(constants), sorted(stocks), sorted(flows)

class Analyze:
    def __init__(self, model):
        self.model = model

    def generate_samples(self):
        problem = {
            'num_vars': len(self.constants_included) + len(self.initial_included),
            'names': self.constants_included + self.initial_included,
            'bounds': self.bounds
        }

        #(N * (D+2)) samples
        SA_param_values = saltelli.sample(problem, 1000)
        return SA_param_values

    def run_simulation(self):
        output_variable = self.output.get()

        Y = np.zeros([self.samples.shape[0]])
        
        for i, X in enumerate(self.samples):
            print ("\r{} of {}".format(i, len(self.samples)), end = '\r', flush=True)

            # Creating paramter set for this run
            parameterset = dict(zip(self.constants_included, X[0:len(self.constants_included)]))

            # Creating initial_condition
            initialset = dict(zip(self.initial_included, X[len(self.constants_included):]))
            
            if not initialset:
                model_output = self.model.run(return_columns=[output_variable],
                                params=parameterset, return_timestamps = [self.model.components.final_time()])
            else:
                # Reload the model from the python file. Setting the initial condition will
                # cause stocks to not reset to its initial value.
                model = pysd.load(sys.argv[1].split('.')[0] + ".py")
                model_output = model.run(return_columns=[output_variable], initial_condition=(self.model.components.initial_time(), initialset),
                                params=parameterset, return_timestamps = [self.model.components.final_time()])

            Y[i] = model_output.iloc[0][0]
            
            # If model fails somehow due to overflow, stop directly.
            if np.isnan(Y[i]):
                print ("Calculation is overflowing")
                break
          
        return Y

    def analyze(self, output_simulation):
        problem = {
            'num_vars': len(self.constants_included) + len(self.initial_included),
            'names': self.constants_included + self.initial_included,
            'bounds': self.bounds
        }

        #Do the sobel analysis
        Si = sobol.analyze(problem, output_simulation)
        print (self.constants_included, self.initial_included)
        print("Sobel first index: {}".format(Si['S1']))
        print("Sobel total index: {}".format(Si['ST']))
        # Sobel analysis interaction between variable 1 and 2.
        #print("Sobel second index: {}.format(Si['S2'][0,1])")


    def start_simulation(self, event):
        self.samples = self.generate_samples()
        output_simulation = self.run_simulation()
        self.analyze(output_simulation)


if __name__ == "__main__":
    # Find all the possible stocks and flows of the model.
    Vensim_file = sys.argv[1]
    model = pysd.read_vensim(Vensim_file)
    all_components =  (model.components._namespace).keys()
    system_components = ["INITIAL TIME", "FINAL TIME", "SAVEPER", "Time", "TIME", "TIME STEP"]
    model_components = [x for x in all_components if x not in system_components]

    constants, stocks, flows = find_parameters(model_components)

    analyzer = Analyze(model)
    root = Tk()
    root.title("Sensitivity analysis")
    frame=Frame(root)
    frame.grid(row=2, column=0, pady=(5, 0), sticky='nw')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    frame.grid_propagate(False)
    canvas=Canvas(frame)
    canvas.grid(row=0, column=0, sticky="news")
    vsb = Scrollbar(frame, orient="vertical", command=canvas.yview)
    vsb.grid(row=0, column=1, sticky='ns')
    canvas.configure(yscrollcommand=vsb.set)
    
    frame_gui = Frame(canvas)
    canvas.create_window((0, 0), window=frame_gui, anchor='nw')
    
    my_gui = gui.GUI(frame_gui, constants, stocks, flows, analyzer)
    
    frame_gui.update_idletasks()
    
    frame.config(width=700, height=600)
    
    canvas.config(scrollregion=canvas.bbox("all"))


    root.mainloop()
