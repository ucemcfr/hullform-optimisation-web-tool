
import csv
import numpy as np
from deap import algorithms, creator, tools, base
#import matplotlib.pyplot as plt
#import tkinter
#import itertools




#
# # input length range (m)
# loLWL = 200
# hiLWL = 210
#
# # input beam range (m)
# loB = 30
# hiB = 35
#
# # input draft range (m)
# loT = 8
# hiT = 12
#
# # input volume range (m^3)
# loVolDisp = 35000
# hiVolDisp = 40000
#
# input midship area coefficient
Cm = 0.9
#
# # input waterplane area coefficient
# loCwp = 0.6
# hiCwp = 0.9
#
# input LCB as % of LWL forward of 0.5 LWL
Lcb = -2
#
# input speed (m/s)
V = 25 * 0.51444
#
# # Assumptions:
# #
# # Normal stern section shape
# # C2 is taken as zero if there is no bulbous bow. Is this correct? Reference? NB if true, this would make Rw = 0
# # No immersed transom area OR transom immersion has no influence on resistance. Are these one and the same?
# # Tf = T i.e. forward draft is the same as the mean draft
# # Appendages are currently ignored
#
# # top = tkinter.Tk()
# # label1 = tkinter.Label(top, text="Upper LWL Limit")
# # label1.pack(side="left")
# # a = tkinter.Entry(top,bd=5)
# # a.pack(side="right")
# # hiLWLtest=a.get()
# # top.mainloop()
#
# GA parameters
#popsize = 100
#originalPopsize = popsize
#maxgen = 50
crossprob = 0.5
mutprob = 0.2
#
# constants
kinVisc = 1.19 * (10 ** -6)  # saltwater at 15 deg C
rho = 1.025  # kg/m^3
g = 9.81  # m/s^2


# c2 = 1 # is this correct? or is it zero?

def nonDimParams(LWL, Velocity):
    Fn = Velocity / np.sqrt(9.807 * LWL)
    Rn = (Velocity * LWL) / kinVisc
    return Fn, Rn


def formParams(LWL, B, T, Cm, VolDisp):
    Am = B * T * Cm
    Cb = VolDisp / (LWL * B * T)
    Cp = VolDisp / (Am * LWL)
    return Cb, Cp


def CfCalc(Rn, Fn):
    # calculates model and ship scale Cf using the ITTC '57 formula and model specs from NPL cat series
    Cf = 0.075 / ((np.log10(Rn) - 2) ** 2)
    return Cf


# def formFactorCalc(LWL, B, T, Lcb, Cm, VolDisp):
#    Cb, Cp = formParams(LWL, B, T, Cm, VolDisp)
#    Cstern = 10 # Assuming normal section shape in stern
#    c13 = 1 + 0.003*Cstern
#    if T/LWL>0.05:
#        c12 = (T/LWL)**0.2228446
#    elif T/LWL>0.0201 and T/LWL<0.05:
#        c12 = 48.2 * (T/LWL - 0.02)**2.078 + 0.479948
#    else:
#        c12 = 0.479948
#    print('c12 = ', c12)
#    Lr = LWL * ((1 - Cp) + 0.06 * Cp * Lcb / ((4 * Cp) - 1))
#    print('Lr = ', Lr)
#    formFactor = c13*(0.93 + c12*((B/Lr)**0.92497) * ((0.95-Cp)**-0.521448) * ((1-Cp + 0.0225*Lcb)**0.6906))
#    #print('c13 = ', c13)
#    print('formfactor= ', formFactor)
#    print(T/LWL)
#    return formFactor, Lr


####################################################
## Add a validity check for displacement, form params etc. Can Cb, Cp go negative with the ranges currently allowed?
def formFactorCalc84(LWL, B, T, Lcb, Cm, VolDisp):
    Cb, Cp = formParams(LWL, B, T, Cm, VolDisp)
    print('Cb ', Cb)
    print('Cp ', Cp)
    cStern = 0  # Normal section shape
    c14 = 1 + 0.011 * cStern
    Lr = LWL * (1 - Cp + 0.06 * Cp * Lcb / (4 * Cp - 1))
    # formFactor = 0.93 + 0.487118 * c14 * ((B/LWL)**1.06806) * ((T/LWL)**0.46106) * ((LWL/Lr)**0.121563*(LWL**3/VolDisp)**0.36486) * ((1-Cp)**-0.604247)
    formFactor2 = 0.93 + 0.487118 * c14 * ((B / LWL) ** 1.06806) * ((T / LWL) ** 0.46106) * ((LWL / Lr) ** 0.121563) * (
            ((LWL ** 3) / VolDisp) ** 0.36486) * ((1 - Cp) ** -0.604247)
    print(formFactor2)
    return formFactor2, Lr


def wettedAreaCalc(LWL, B, T, Cm, Cwp, VolDisp):
    Cb, Cp = formParams(LWL, B, T, Cm, VolDisp)
    WSA = LWL * (2 * T + B) * (Cm ** 0.5) * (0.453 + 0.4425 * Cb - 0.2862 * Cm - 0.003467 * (
            B / T) + 0.3696 * Cwp)  # if bulb were being taken into account also include the following term: (+ 2.38 * Abt / Cb)
    # print('WSA= ', WSA)
    return WSA


def RvCalc(LWL, B, T, Lcb, Cm, Cwp, VolDisp, Velocity):
    Fn, Rn = nonDimParams(LWL, Velocity)
    # print('Fn = ',Fn, '\nRn = ', Rn)
    Cf = CfCalc(Rn, Fn)
    # print('Cf = ', Cf)
    WSA = wettedAreaCalc(LWL, B, T, Cm, Cwp, VolDisp)
    # print('WSA = ', WSA)
    formFactor, Lr = formFactorCalc84(LWL, B, T, Lcb, Cm, VolDisp)
    # print('Cv = ', Cf*formFactor)
    Rf = 0.5 * rho * WSA * (Velocity ** 2) * Cf
    Rv = Rf * formFactor
    # print('Rf = ', Rf)
    # print('(1+k) = ', formFactor)
    # print('LR = ', Lr)
    return Rv


def RwCalc(LWL, B, T, VolDisp, Velocity, Cwp, Cm):
    Abt = 0
    At = 0
    hb = 0
    Tf = T
    Ta = T

    formFactor, Lr = formFactorCalc84(LWL, B, T, Lcb, Cm, VolDisp)
    Cb, Cp = formParams(LWL, B, T, Cm, VolDisp)
    Fn, Rn = nonDimParams(LWL, Velocity)

    iE = 1 + 89 * np.exp(-((LWL / B) ** 0.80856) * ((1 - Cwp) ** 0.30484) * ((1 - Cp - 0.0225 * Lcb) ** 0.6367) * (
            (Lr / B) ** 0.34574) * ((100 * VolDisp / LWL ** 3) ** 0.16302))
    print('iE ', iE)
    d = -0.9
    c3 = 0.56 * Abt ** 1.5 / (B * T * (0.31 * Abt ** (1 / 2) + Tf - hb))
    c2 = np.exp(-1.89 * (c3 ** (1 / 2)))
    c5 = (1 - 0.8 * At / (B * T * Cm))
    c17 = 6919.3 * Cm ** (-1.3346) * (VolDisp / LWL ** 3) ** 2.00977 * (LWL / B - 2) ** (1.40692)
    m3 = -7.2035 * (B / LWL) ** 0.326869 * (T / B) ** 0.605375

    if LWL / B < 12:
        lambda_ = 1.446 * Cp - 0.03 * LWL / B

    else:
        lambda_ = 1.446 * Cp - 0.36

    if LWL ** 3 / VolDisp < 512:
        c15 = -1.69385

    elif 512 < LWL ** 3 / VolDisp < 1726.91:
        c15 = -1.69385 + (LWL / VolDisp ** (1 / 3) - 8) / 2.36

    else:
        c15 = 0

    m4 = c15 * 0.4 * np.exp(-0.034 * Fn ** (-3.29))

    Rw_b = c17 * c2 * c5 * VolDisp * rho * g * np.exp(m3 * Fn ** (d) + m4 * np.cos(lambda_ * Fn ** (-2)))

    if B / LWL < 0.11:
        c7 = 0.229577 * (B / LWL) ** 0.33333

    elif 0.11 < B / LWL < 0.25:
        c7 = B / LWL

    else:
        c7 = 0.5 - 0.0625 * LWL / B

    c1 = 2223105 * c7 ** (3.78613) * (T / B) ** (1.07961) * (90 - iE) ** (-1.37565)

    if Cp < 0.8:
        c16 = 8.07981 * Cp - 13.8673 * Cp ** 2 + 6.984388 * Cp ** 3

    else:
        c16 = 1.73014 - 0.7067 * Cp

    m1 = 0.0140407 * LWL / T - 1.75254 * VolDisp ** (1 / 3) / LWL - 4.79323 * B / LWL - c16

    Rw_a = c1 * c2 * c5 * VolDisp * rho * g * np.exp(m1 * Fn ** d + m4 * np.cos(lambda_ * Fn ** (-2)))

    if Fn < 0.4:
        Rw = Rw_a

    elif Fn > 0.55:
        Rw = Rw_b

    else:
        Rw = Rw_a + (10 * Fn - 4) * (Rw_b - Rw_a) / 1.5

    print('Fn ', Fn)
    print('Rw_a', Rw_a)
    print('Rw_b', Rw_b)
    print('Rw', Rw)
    print('c5 ', c5)

    return Rw


def RaCalc(LWL, B, T, Cb, Cm, Cwp, VolDisp, Velocity):
    Tf = T  # This isn't strictly true
    WSA = wettedAreaCalc(LWL, B, T, Cm, Cwp, VolDisp)

    if Tf / LWL <= 0.04:
        c4 = Tf / LWL
    else:
        c4 = 0.04

    # print('c4 = ', c4)

    ##################################################################
    # This is just added to get it working, check correct c2 value in holtrop paper
    c2 = 1
    #####################################################################

    Ca = 0.006 * (LWL + 100) ** -0.16 - 0.00205 + 0.003 * (LWL / 7.5) ** 0.5 * Cb ** 4 * c2 * (0.04 - c4)

    # print('Ca = ', Ca)

    Ra = 0.5 * rho * Velocity ** 2 * WSA * Ca
    return Ca, Ra


def RtCalc(LWL, B, T, Lcb, Cm, Cwp, VolDisp, Velocity):
    Cb, Cp = formParams(LWL, B, T, Cm, VolDisp)
    # print('Cp = ', Cp)
    Rv = RvCalc(LWL, B, T, Lcb, Cm, Cwp, VolDisp, Velocity)
    Rw = RwCalc(LWL, B, T, VolDisp, Velocity, Cwp, Cm)
    Ca, Ra = RaCalc(LWL, B, T, Cb, Cm, Cwp, VolDisp, Velocity)
    Rt = Rv + Rw + Ra
    return Rt


#################################################################################
## up to here checked against H&M paper and all numbers correct except Rw, Ra, Cv. Although Cf is correct and (1+k) is correct.
## When taking into account the value of c2 used by H&M, Rw comes very close to their answer
## Ra is also close, this may be down ot a different value of density and/or viscosity used.
## New formfactor not checked

def propCoefficients(LWL, B, D, T, Ta, S, Cb, Cp, Cm, Lcb, formFactor, Cf, Ca):
    Cstern = 0  # For normal section shape in stern

    if B / Ta < 5:
        c8 = B * S / (LWL * D * Ta)
    else:
        c8 = S * ((7 * B / Ta) - 25) / (LWL * D * (B / Ta - 3))

    if c8 < 28:
        c9 = c8
    else:
        c9 = 32 - 16 / (c8 - 24)

    if Ta / D < 2:
        c11 = Ta / D
    else:
        c11 = 0.0833333 * (Ta / D) ** 2 + 1.33333

    if Cp < 0.7:
        c19 = 0.12997 / (0.95 - Cb) - 0.11056 / (0.95 - Cp)
    else:
        c19 = 0.18567 / (1.3571 - Cm) - 0.71276 + 0.38648 * Cp

    c20 = 1 + 0.015 * Cstern

    Cp1 = 1.45 * Cp - 0.315 - 0.0225 * Lcb

    Cv = formFactor * Cf + Ca

    w = c9 * c20 * Cv * LWL / Ta * (0.050776 + 0.93405 * c11 * (Cv / (1 - Cp1))) + 0.27915 * c20 * (
            B / (LWL * (1 - Cp1))) ** 0.5 + c19 * c20

    t = (0.25014 * (B / LWL) ** 0.28956 * (((B * T) ** 0.5) / D) ** 0.2624) / (
            ((1 - Cp + 0.225 * Lcb) ** 0.01762) + 0.0015 * Cstern)

    etaR = 0.9922 - 0.05908 * Ae / Ao + 0.07424(Cp - 0.0225 * Lcb)

    return w, t, etaR


def kmCalc(LWL, B, T, Cwp,
           VolDisp):  # This is taken from Stephen Wallis' notes from Solent YPD course (Marine Craft Design & Development)

    Cwi = 12 / (Cwp ** 2)  # NOTE THIS IS APPROXIMATE
    I = (LWL * B ** 3) / Cwi
    Awp = Cwp * LWL * B
    Vcb = (1 / 3) * ((T / 2) + (VolDisp / Awp))  # Using Morrish's rule. Distance measured FROM WATERLINE DOWNWARDS
    BM = I / VolDisp
    KB = T - Vcb
    KM = BM + KB

    return KM


def evaluate(individual):
    LWL, B, T, VolDisp, Cwp = individual
    Rt = RtCalc(LWL, B, T, Lcb, Cm, Cwp, VolDisp, V)
    KM = kmCalc(LWL, B, T, Cwp, VolDisp)

    return (Rt, KM)


def deap_evolve(loLWL, loB, loT, loVolDisp, loCwp, hiLWL, hiB, hiT, hiVolDisp, hiCwp, popsize, maxgen):
    originalPopsize = popsize

    def valid(individual):
        LWL, B, T, VolDisp, Cwp = individual

        if LWL > hiLWL or LWL < loLWL or B > hiB or B < loB or T > hiT or T < loT or VolDisp > hiVolDisp or VolDisp < loVolDisp or Cwp > hiCwp or Cwp < loCwp:
            return False
        else:
            return True

    # Set individuals to minimise the function
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
        toolbox.attributeCwp),
                     n=1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual, n=popsize)
    # Create population
    #pop = toolbox.population()
    # Register evolutionary operators in the toolbox
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, eta=0.5, low=[loLWL, loB, loT, loVolDisp, loCwp],
                     up=[hiLWL, hiB, hiT, hiVolDisp, hiCwp])
    toolbox.register("mutate", tools.mutPolynomialBounded, eta=0.5, low=[loLWL, loB, loT, loVolDisp, loCwp],
                     up=[hiLWL, hiB, hiT, hiVolDisp, hiCwp], indpb=mutprob)
    toolbox.register("select", tools.selNSGA2)  ## This final value of "k" may be wrong, this is a pure guess
    toolbox.register("evaluate", evaluate)
    # Registering statistics recording in the toolbox
    stats = tools.Statistics(key=lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)
    # Creating first generation

    pop = toolbox.population()

    pop = list(filter(valid, pop))

    while len(pop) < originalPopsize:
        popsize = originalPopsize - len(pop)
        newpop = toolbox.population()
        [pop.append(item) for item in newpop]
        pop = list(filter(valid, pop))
        #print("popsize = " + popsize)

    # Simple EA algorithm
    # pop, logbook = algorithms.eaSimple(pop, toolbox, CXPB, MUTPB, NGEN, stats=stats, halloffame=hof, verbose=True)

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

        # Add the elite individual to offspring
        # offspring = elite + offspring

        # Increasing
        while len(offspring) < originalPopsize:
            popsize = originalPopsize - len(offspring)
            toolbox.register("population", tools.initRepeat, list, toolbox.individual, n=popsize)
            newpop = toolbox.population()
            [offspring.append(item) for item in newpop]
            offspring = list(filter(valid, offspring))

        # Evaluate individuals with invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            # Append all fitnesses from current generation to all_fits
            all_fits.append(fit)
            # Append all individuals from current generation to all_inds
            all_inds.append(ind)
        # Append the best individual from current generation to best_inds
        # best_inds.append(tools.selBest(pop, 1))
        # worst_inds.append(tools.selWorst(pop,1))
        pareto_ = tools.sortNondominated(offspring, len(all_inds), first_front_only=True)

        paretoFits_ = list(map(lambda x: x.fitness.values, pareto_[0]))
        print('Gen is ', gen, 'Pareto fits is ', paretoFits_)
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
        print("Length of pop is:    ", len(pop))
        # Record statistics for the current population
        record = stats.compile(pop)
        # print("Length of Invalid_ind is:    ", len(invalid_ind))
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)

        ### Plotting
        resFitAll = [x[0] for x in all_fits]
        stabFitAll = [x[1] for x in all_fits]
        LWLAll = [x[0] for x in all_inds]
        BeamAll = [x[1] for x in all_inds]
        DraftAll = [x[2] for x in all_inds]
        DispAll = [x[3] for x in all_inds]
        CwpAll = [x[4] for x in all_inds]

        number_of_runs = len(all_inds)

        return record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs





# ## WRONG best_res = [ y[0] for y in [x[0] for x in best_inds]]
# gen, avg, max_, min_ = logbook.select("gen", "avg", "max", "min")
#
# pareto = tools.sortNondominated(all_inds, len(all_inds), first_front_only=True)
# paretoFits = list(map(lambda x: x.fitness.values, pareto[0]))
# resFitNonDom = [x[0] for x in paretoFits]
# stabFitNonDom = [x[1] for x in paretoFits]
#
# plt.figure()
# axes = plt.gca()
# axes.set_xlim([0, max(resFitAll) * 1.1])
# axes.set_ylim([0, max(stabFitAll) * 1.1])
# plt.scatter(resFitAll, stabFitAll, color='blue', edgecolors='black')
# plt.scatter(resFitNonDom, stabFitNonDom, color='red', edgecolors='black')
# plt.title('All designs, with Pareto Optimal designs shown in red')
# plt.xlabel('Reistance (kN)')
# plt.ylabel('KM (m)')
# plt.show()
#
# plt.figure()
# plt.scatter(resFitNonDom, stabFitNonDom, color='red', edgecolors='black')
#
# number_of_runs = len(all_inds)

# for p in range(0, len(pareto_res)):
#     plt.figure()
#     pt_res = list(itertools.chain.from_iterable(allres[0:p + 1]))
#     pt_stab = list(itertools.chain.from_iterable(allstab[0:p + 1]))
#     par_res = pareto_res[p]
#     par_stab = pareto_stab[p]
#     print(par_res)
#     axes = plt.gca()
#     axes.set_xlim([0, 2500])
#     axes.set_ylim([0, 30])
#     plt.scatter(pt_res, pt_stab, color='blue')
#     plt.scatter(pareto_res[p], pareto_stab[p], color='red')
#     plt.title('All designs, with Pareto Optimal designs shown in red for generation ' + str(p))
#     plt.xlabel('Reistance (kN)')
#     plt.ylabel('KM (m)')
#     plt.show()



def deap_save(resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs):
    with open('static/data/design.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',',
                                quotechar='|',
                                quoting=csv.QUOTE_MINIMAL)

        csv_writer.writerow(['design number',
                             'LWL (m)',
                             'Beam (m)',
                             'Draft (m)',
                             'Vol Disp (m^3)',
                             'Waterplane coefficient',
                             'Resistance (kN)',
                             'KM (m)'])

        for run in range(number_of_runs):
            csv_writer.writerow([run,
                                 LWLAll[run],
                                 BeamAll[run],
                                 DraftAll[run],
                                 DispAll[run],
                                 CwpAll[run],
                                 resFitAll[run],
                                 stabFitAll[run]])

        return

#record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs = deap_evolve(loLWL, loB, loT, loVolDisp, loCwp, hiLWL, hiB, hiT, hiVolDisp, hiCwp, popsize)

#deap_save(resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs)

# if __name__ == '__main__':
#     app.run(debug=True)
