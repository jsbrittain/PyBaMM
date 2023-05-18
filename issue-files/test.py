import pybamm
import numpy as np
import importlib

# check for loading errors
idaklu_spec = importlib.util.find_spec("pybamm.solvers.idaklu")
idaklu = importlib.util.module_from_spec(idaklu_spec)
idaklu_spec.loader.exec_module(idaklu)

# construct model
# pybamm.set_logging_level("INFO")
model = pybamm.lithium_ion.DFN()
geometry = model.default_geometry
param = model.default_parameter_values
param.process_model(model)
param.process_geometry(geometry)
n = 50  # control the complexity of the geometry (increases number of solver states)
var_pts = {"x_n": n, "x_s": n, "x_p": n, "r_n": 10, "r_p": 10}
mesh = pybamm.Mesh(geometry, model.default_submesh_types, var_pts)
disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
disc.process_model(model)
t_eval = np.linspace(0, 3600, 100)

options = {'linear_solver': 'SUNLinSol_Dense', 'jacobian': 'dense'}
#options = {'linear_solver': 'SUNLinSol_SuperLUDIST'}
klu_sol = pybamm.IDAKLUSolver(atol=1e-8, rtol=1e-8, options=options).solve(model, t_eval)
print(f"Solve time: {klu_sol.solve_time.value*1000} msecs")

# solve using IDAKLU
#options = {'num_threads': 1}
#for _ in range(5):
#    klu_sol = pybamm.IDAKLUSolver(atol=1e-8, rtol=1e-8, options=options).solve(model, t_eval)
#    print(f"Solve time: {klu_sol.solve_time.value*1000} msecs [{options['num_threads']} threads]")
#options = {'num_threads': 4}
#for _ in range(5):
#    klu_sol = pybamm.IDAKLUSolver(atol=1e-8, rtol=1e-8, options=options).solve(model, t_eval)
#    print(f"Solve time: {klu_sol.solve_time.value*1000} msecs [{options['num_threads']} threads]")
