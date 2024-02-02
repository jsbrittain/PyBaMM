import pybamm
import numpy as np

model = pybamm.lithium_ion.DFN()
geometry = model.default_geometry
param = model.default_parameter_values

# Create interpolant
current_interpolant = pybamm.Interpolant(
    np.linspace(0, 5000, 50000),
    np.ones(50000)*0.7,
    pybamm.t
    )

# Set drive cycle
param.update({"Current function [A]": current_interpolant})

# Solve
solver_idaklu = pybamm.IDAKLUSolver(
    rtol=1e-8, atol=1e-8)

sim = pybamm.Simulation(
    model, parameter_values=param, solver=solver_idaklu)
solution_idaklu = sim.solve(calc_esoh=False)
