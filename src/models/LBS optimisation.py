import csv
import numpy as np
from deap import algorithms, creator, tools, base
from src.models.resistance import calculate_holtrop_resistance
from src.models.motions import calculate_jensen_acceleration
import pandas as pd

# # Assumptions:
# # Normal stern section shape
# # C2 is taken as zero if there is no bulbous bow. Is this correct? Reference? NB if true, this would make Rw = 0
# # No immersed transom area OR transom immersion has no influence on resistance. Are these one and the same?
# # Tf = T i.e. forward draft is the same as the mean draft
# # Appendages are currently ignored

crossprob = 0.5
mutprob = 0.2
kinVisc = 1.19 * (10 ** -6)  # saltwater at 15 deg C
rho = 1.025  # kg/m^3
g = 9.81  # m/s^2

Cm = 0.9  # TODO why is this not a free variable in the optimisation?
loLWL = 80
loB = 18
loT = 8
loVolDisp = 100000
loCwp = 0.6
hiLWL = 120
hiB = 28
hiT = 15
hiVolDisp = 1500000
hiCwp = 0.8
LCB = 0
V = 10
popsize = 10
maxgen = 5
originalPopsize = popsize


def evaluate(individual):
    LWL, B, T, VolDisp, Cwp = individual
    Rt = calculate_holtrop_resistance(LWL, B, T, LCB, VolDisp, V, Cm,
                                      Cwp)  # TODO check ...lwl, bwl, draft, lcb, vol_disp, velocity, r_n, f_n, c_b, c_p, c_m, c_wp, rho, g
    KM = calculate_jensen_acceleration(LWL, B, T, VolDisp, V, heading=0, wave_amplitude=1,
                                       long_position=0)  # TODO change this so the heading and velocity can be passed in by the user along with wave amplitude, longitudinal position etc. Also change from KM to proper variable name.

    return (Rt, KM)


# TODO not sure this is quite correct, is this really checking validity in terms of constraints? or is this just marking if they're already evaluated for fitness?
def valid(individual):
    LWL, B, T, VolDisp, Cwp = individual

    if LWL > hiLWL or LWL < loLWL or B > hiB or B < loB or T > hiT or T < loT or VolDisp > hiVolDisp or VolDisp < loVolDisp or Cwp > hiCwp or Cwp < loCwp or Cwp > 1:
        return False
    elif isinstance(evaluate(individual)[0], complex):
        return False
    else:
        return True


# TODO is this the best way to handle constraints?
def valid_initial(individual):
    LWL, B, T, VolDisp, Cwp = individual

    if LWL > hiLWL or LWL < loLWL or B > hiB or B < loB or T > hiT or T < loT or VolDisp > hiVolDisp or VolDisp < loVolDisp or Cwp > hiCwp or Cwp < loCwp or Cwp > 1:
        return False
    elif isinstance(evaluate(individual)[0], complex):
        return False
    else:
        return True


# Set individuals to minimise the function
# TODO is this correct, should I be minimising both?
creator.create("FitnessMinMax", base.Fitness, weights=(-1.0, +1.0))
creator.create("Individual", list, fitness=creator.FitnessMinMax)
# Setting random values for parameters within the correct ranges (for the first generation)
toolbox = base.Toolbox()
toolbox.register("attributeLWL", np.random.uniform, loLWL, hiLWL)
toolbox.register("attributeBeam", np.random.uniform, loB, hiB)
toolbox.register("attributeDraft", np.random.uniform, loT, hiT)
toolbox.register("attributeVolDisp", np.random.uniform, loVolDisp, hiVolDisp)
toolbox.register("attributeCwp", np.random.uniform, loCwp, hiCwp)
# Registering individuals and population in the toolbox
toolbox.register("individual", tools.initCycle, creator.Individual,
                 (toolbox.attributeLWL,
                  toolbox.attributeBeam,
                  toolbox.attributeDraft,
                  toolbox.attributeVolDisp,
                  toolbox.attributeCwp,
                  # TODO need to add more variables into the individual so that it can be checked if the Holtrop method is valid also where is LCB coming from?
                  ),
                 n=1)
toolbox.register("population", tools.initRepeat, list, toolbox.individual, n=popsize)
# Register evolutionary operators in the toolbox
toolbox.register("mate", tools.cxSimulatedBinaryBounded, eta=0.5, low=[loLWL, loB, loT, loVolDisp, loCwp],
                 up=[hiLWL, hiB, hiT, hiVolDisp, hiCwp])
toolbox.register("mutate", tools.mutPolynomialBounded, eta=0.5, low=[loLWL, loB, loT, loVolDisp, loCwp],
                 up=[hiLWL, hiB, hiT, hiVolDisp, hiCwp], indpb=mutprob)
toolbox.register("select", tools.selLBS, z_v=[1000000000, 1000000000], z_r=[0, 0], v=[100000000, 10000000000])  ## This final value of "k" may be wrong, this is a pure guess
toolbox.register("evaluate", evaluate)
# Registering statistics recording in the toolbox
stats = tools.Statistics(key=lambda ind: ind.fitness.values)
stats.register("avg", np.mean)
stats.register("std", np.std)
stats.register("min", np.min)
stats.register("max", np.max)
# Creating first generation

pop = toolbox.population()

pop = list(filter(valid_initial, pop))
#    pop = list(filter(valid2, pop)) # TODO do this valid2 function so that it filters out those with complex resistance values maybe this should be for the offspring really

while len(pop) < originalPopsize:
    popsize = originalPopsize - len(pop)
    newpop = toolbox.population()
    [pop.append(item) for item in newpop]
    pop = list(filter(valid_initial, pop))
    # print("popsize = " + popsize)

# Initialising best_inds list
best_inds = []
worst_inds = []
all_inds = []
all_fits = []
pareto_res = []
pareto_stab = []
all_indi = []
allres = []
allstab = []
# Creating logbook for statistics
logbook = tools.Logbook()

for gen in range(maxgen):
    print("Current generation is:   ", gen)
    offspring = []

    elite = tools.selBest(pop, 1)
    # Select and clone next generation individuals
    offspring = map(toolbox.clone, toolbox.select(pop, popsize - 1))

    # Apply crossover and mutation on the offspring
    offspring = algorithms.varAnd(offspring, toolbox, crossprob, mutprob)

    # Filtering out individuals that violate Fn and Length/Disp constraints
    offspring = list(filter(valid, offspring))

    # Increasing
    while len(offspring) < originalPopsize:
        popsize = originalPopsize - len(offspring)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual, n=popsize)
        newpop = toolbox.population()  # TODO how are the resistance results stored by DEAP? How can I access them for use in the validity check?
        [offspring.append(item) for item in newpop]
        offspring = list(filter(valid, offspring))

        # Evaluate individuals with invalid fitness
    invalid_ind = [ind for ind in offspring if not ind.fitness.valid]  # TODO I don't get what this is doing, why am I evaluating the invalid ones? -- NB this has been changed from "if not" to "if"
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind,
                        fitnesses):  # TODO what exactly am i doing with these invalid individuals? I don't want to appent them to the list of individuals do I? Especially if the validity check is now checking for out of bounds Holtrop results
        ind.fitness.values = fit
        #     # Append all fitnesses from current generation to all_fits
        all_fits.append(fit)
        # Append all individuals from current generation to all_inds
        all_inds.append(ind)
        # print(all_fits)

    # TODO this may not be the right thing in the right place
    if gen == 0:
        df0 = pd.DataFrame(all_fits, columns=['res', 'accel'])  # This is a df of all the fitnesses
        # cdf0 = pd.DataFrame(columns=['gen', 'avg_res', 'min_res', 'avg_accel', 'min_accel']) # this is an empty dataframe to store the convergence statistics
        # need to append things to this empty df
        cdf0 = pd.DataFrame(
            [{
                'gen': gen,
                'avg_res': np.mean(df0['res']),
                'min_res': min(df0['res']),
                'avg_accel': np.mean(df0['accel']),
                'min_accel': min(df0['accel'])
            }]
        )
        # cdf0['gen'] = gen # adding columns to convergence df with stats computed from the fitness df
        # cdf0['avg_res'] = np.mean(df0['res'])
        # cdf0['min_res'] = min(df0['res'])
        # cdf0['avg_accel'] = np.mean(df0['accel'])
        # cdf0['min_accel'] = min(df0['accel'])
        cdf0.to_csv('../src/static/data/convergence.csv', index=False)  # saving convergence df
        print('initial df is     ')
        print(cdf0)
    else:
        df1 = pd.read_csv('../src/static/data/convergence.csv')
        df2 = pd.DataFrame(all_fits, columns=['res', 'accel'])  # TODO something is making the number of individuals saved in the CSV grow massively
        cdf2 = pd.DataFrame(
            [{
                'gen': gen,
                'avg_res': np.mean(df2['res']),
                'min_res': min(df2['res']),
                'avg_accel': np.mean(df2['accel']),
                'min_accel': min(df2['accel'])
            }]
        )
        print('df to be added is     ')
        print(cdf2)
        cdf3 = df1.append(cdf2, ignore_index=True)
        cdf3.to_csv('../src/static/data/convergence.csv', index=False)
        print('total dataframe to date is    ')
        print(cdf3)

pareto_ = tools.sortNondominated(offspring, len(all_inds), first_front_only=True)

paretoFits_ = list(
    map(lambda x: x.fitness.values, pareto_[0]))  # TODO this is returning a list index out of range error
pareto_res_ = [x[0] for x in paretoFits_]
pareto_stab_ = [x[1] for x in paretoFits_]
pareto_res.append(pareto_res_)
pareto_stab.append(pareto_stab_)

allinds_ = offspring
allfits_ = list(map(lambda x: x.fitness.values, allinds_))
allres_ = [x[0] for x in allfits_]
allstab_ = [x[1] for x in allfits_]
allres.append(allres_)
allstab.append(allstab_)

# Replace population with offspring
pop[:] = offspring[:]
# Record statistics for the current population
record = stats.compile(pop)
logbook.record(gen=gen, nevals=len(invalid_ind), **record)

# Plotting
resFitAll = [x[0] for x in all_fits]
stabFitAll = [x[1] for x in all_fits]
LWLAll = [x[0] for x in all_inds]
BeamAll = [x[1] for x in all_inds]
DraftAll = [x[2] for x in all_inds]
DispAll = [x[3] for x in all_inds]
CwpAll = [x[4] for x in all_inds]
# TODO how do I save all the other parameters?

number_of_runs = len(all_inds)
print('runs:    ', number_of_runs)


# return record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs


def deap_save(resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs):
    with open('static/data/design.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',',
                                quotechar='|',
                                quoting=csv.QUOTE_MINIMAL)

        csv_writer.writerow(['design_num',
                             'lwl',
                             'beam',
                             'draft',
                             'vol_disp',
                             'c_wp',
                             'resistance',
                             'vert_accel'])

        for run in range(number_of_runs):
            csv_writer.writerow([run,
                                 LWLAll[run],
                                 BeamAll[run],
                                 DraftAll[run],
                                 DispAll[run],
                                 CwpAll[run],
                                 resFitAll[run],
                                 stabFitAll[run]])
