import bisect
import math
import random

from itertools import chain
from operator import attrgetter, itemgetter
from collections import defaultdict

######################################
# Non-Dominated Sorting   (NSGA-II)  #
######################################

def selNSGA2(individuals, k, nd='standard'):
    """Apply NSGA-II selection operator on the *individuals*. Usually, the
    size of *individuals* will be larger than *k* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *k* will have no effect other
    than sorting the population according to their front rank. The
    list returned contains references to the input *individuals*. For more
    details on the NSGA-II operator see [Deb2002]_.
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param nd: Specify the non-dominated algorithm to use: 'standard' or 'log'.
    :returns: A list of selected individuals.
    .. [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
       non-dominated sorting genetic algorithm for multi-objective
       optimization: NSGA-II", 2002.
    """
    if nd == 'standard':
        pareto_fronts = sortNondominated(individuals, k)
    elif nd == 'log':
        pareto_fronts = sortLogNondominated(individuals, k)
    else:
        raise Exception('selNSGA2: The choice of non-dominated sorting '
                        'method "{0}" is invalid.'.format(nd))

    for front in pareto_fronts:
        assignCrowdingDist(front)

    chosen = list(chain(*pareto_fronts[:-1]))
    k = k - len(chosen)
    if k > 0:
        sorted_front = sorted(pareto_fronts[-1], key=attrgetter("fitness.crowding_dist"), reverse=True)
        chosen.extend(sorted_front[:k])

    return chosen

def sortNondominated(individuals, k, first_front_only=False):
    """Sort the first *k* *individuals* into different nondomination levels
    using the "Fast Nondominated Sorting Approach" proposed by Deb et al.,
    see [Deb2002]_. This algorithm has a time complexity of :math:`O(MN^2)`,
    where :math:`M` is the number of objectives and :math:`N` the number of
    individuals.
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param first_front_only: If :obj:`True` sort only the first front and
                             exit.
    :returns: A list of Pareto fronts (lists), the first list includes
              nondominated individuals.
    .. [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
       non-dominated sorting genetic algorithm for multi-objective
       optimization: NSGA-II", 2002.
    """
    if k == 0:
        return []

    map_fit_ind = defaultdict(list)
    for ind in individuals:
        map_fit_ind[ind.fitness].append(ind)
    fits = map_fit_ind.keys()

    current_front = []
    next_front = []
    dominating_fits = defaultdict(int)
    dominated_fits = defaultdict(list)

    # Rank first Pareto front
    for i, fit_i in enumerate(fits):
        for fit_j in fits[i+1:]:
            if fit_i.dominates(fit_j):
                dominating_fits[fit_j] += 1
                dominated_fits[fit_i].append(fit_j)
            elif fit_j.dominates(fit_i):
                dominating_fits[fit_i] += 1
                dominated_fits[fit_j].append(fit_i)
        if dominating_fits[fit_i] == 0:
            current_front.append(fit_i)

    fronts = [[]]
    for fit in current_front:
        fronts[-1].extend(map_fit_ind[fit])
    pareto_sorted = len(fronts[-1])

    # Rank the next front until all individuals are sorted or
    # the given number of individual are sorted.
    if not first_front_only:
        N = min(len(individuals), k)
        while pareto_sorted < N:
            fronts.append([])
            for fit_p in current_front:
                for fit_d in dominated_fits[fit_p]:
                    dominating_fits[fit_d] -= 1
                    if dominating_fits[fit_d] == 0:
                        next_front.append(fit_d)
                        pareto_sorted += len(map_fit_ind[fit_d])
                        fronts[-1].extend(map_fit_ind[fit_d])
            current_front = next_front
            next_front = []

    return fronts

def assignCrowdingDist(individuals):
    """Assign a crowding distance to each individual's fitness. The
    crowding distance can be retrieve via the :attr:`crowding_dist`
    attribute of each individual's fitness.
    """
    if len(individuals) == 0:
        return

    distances = [0.0] * len(individuals)
    crowd = [(ind.fitness.values, i) for i, ind in enumerate(individuals)]

    nobj = len(individuals[0].fitness.values)

    for i in xrange(nobj):
        crowd.sort(key=lambda element: element[0][i])
        distances[crowd[0][1]] = float("inf")
        distances[crowd[-1][1]] = float("inf")
        if crowd[-1][0][i] == crowd[0][0][i]:
            continue
        norm = nobj * float(crowd[-1][0][i] - crowd[0][0][i])
        for prev, cur, next in zip(crowd[:-2], crowd[1:-1], crowd[2:]):
            distances[cur[1]] += (next[0][i] - prev[0][i]) / norm

    for i, dist in enumerate(distances):
        individuals[i].fitness.crowding_dist = dist

#####################################################################

    def sortNondominated2(individuals, k, first_front_only=False):
        """Sort the first *k* *individuals* into different nondomination levels
        using the "Fast Nondominated Sorting Approach" proposed by Deb et al.,
        see [Deb2002]_. This algorithm has a time complexity of :math:`O(MN^2)`,
        where :math:`M` is the number of objectives and :math:`N` the number of
        individuals.
        :param individuals: A list of individuals to select from.
        :param k: The number of individuals to select.
        :param first_front_only: If :obj:`True` sort only the first front and
                                 exit.
        :returns: A list of Pareto fronts (lists), the first list includes
                  nondominated individuals.
        .. [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
           non-dominated sorting genetic algorithm for multi-objective
           optimization: NSGA-II", 2002.
        """
        if k == 0:
            return []

        map_fit_ind = defaultdict(list)
        for ind in individuals:
            map_fit_ind[ind.fitness].append(ind)
        fits = map_fit_ind.keys()

        current_front = []
        next_front = []
        dominating_fits = defaultdict(int)
        dominated_fits = defaultdict(list)

        # Rank first Pareto front
        for i, fit_i in enumerate(fits):
            for fit_j in fits[i + 1:]:
                if fit_i.dominates(fit_j):
                    dominating_fits[fit_j] += 1
                    dominated_fits[fit_i].append(fit_j)
                elif fit_j.dominates(fit_i):
                    dominating_fits[fit_i] += 1
                    dominated_fits[fit_j].append(fit_i)
            if dominating_fits[fit_i] == 0:
                current_front.append(fit_i)

        fronts = [[]]
        for fit in current_front:
            fronts[-1].extend(map_fit_ind[fit])
        pareto_sorted = len(fronts[-1])

        # Rank the next front until all individuals are sorted or
        # the given number of individual are sorted.
        if not first_front_only:
            N = min(len(individuals), k)
            while pareto_sorted < N:
                fronts.append([])
                for fit_p in current_front:
                    for fit_d in dominated_fits[fit_p]:
                        dominating_fits[fit_d] -= 1
                        if dominating_fits[fit_d] == 0:
                            next_front.append(fit_d)
                            pareto_sorted += len(map_fit_ind[fit_d])
                            fronts[-1].extend(map_fit_ind[fit_d])
                current_front = next_front
                next_front = []

        return fronts

    def assignCrowdingDist2(individuals):
        """Assign a crowding distance to each individual's fitness. The
        crowding distance can be retrieve via the :attr:`crowding_dist`
        attribute of each individual's fitness.
        """
        if len(individuals) == 0:
            return

        distances = [0.0] * len(individuals)
        # TODO I think this just lists the individuls in tuples with with one value of tuple being the individual object and the other being 0, 1, 2 etc.
        crowd = [(ind.fitness.values, i) for i, ind in enumerate(individuals)]
        print(crowd) # TODO remove before finishing
        # so I think crowd looks like ([[ind 1 objective 1, ind 1 objective 2, ind 1 objective 3], i=0],[[ind 2 objective 1, ind 2 objective 2, ind 3 objective 3], i=1]])

        # sets nobj to the number of objectives in fitness.values
        nobj = len(individuals[0].fitness.values)

    for i in range(nobj):
        # This sorts the crowd list by the i'th objective, so sorted by a different objective on each iteration of the for loop
        # crowd[0] is the list of fitness values, how many levels is there in crowd tho? later crowd[0][0][i] is used.
        crowd.sort(key=lambda element: element[0][i])

        # what does this do?
        # sets element in distances list to that which is indexed by the value of crowd[0][1] which is the i (or index assigned in the list comprehension in line 214) of the lowest current fitness (as it is sorted for objective i in line 224)
        # this is just the standard nsga2 crowding distance procedure, assign solutions at each end of the front a crowding distance of infinite
        distances[crowd[0][1]] = float("inf")
        # same as above but for the worst fitness value

        distances[crowd[-1][1]] = float("inf")

        # skips the loop if the ith fitness value of the last item in the sorted crowd list is the same as that of the first item
        if crowd[-1][0][i] == crowd[0][0][i]:
            continue

        # not sure what this is for
        # it looks like this multiples the difference between the best and worst fitness value by the number of objectives. Not sure why this is done.
        norm = nobj * float(crowd[-1][0][i] - crowd[0][0][i])

        # this is confusing....

        for prev, cur, next in zip(crowd[:-2], crowd[1:-1], crowd[2:]):
            print('prev', prev)
            print('cur', cur)
            print('next', next)
            distances[cur[1]] += (next[0][i] - prev[0][i]) / norm


    for i, dist in enumerate(distances):
        individuals[i].fitness.crowding_dist = dist

#####################################################################
################## NEW VERSION ######################################
    # TODO move ot the top of the module:
    from operator import attrgetter

    if len(individuals) == 0:
       return

    # TODO perhaps a dict structure is easier to understand, more readable

    ind_dict = dict()

    distances = [0.0] * len(individuals)

    # this creates a list of fitness values for all individuals, with an index referring to the original list of individuals so the crowding distance can later be assignme
    crowd = [(ind.fitness.values, i) for i, ind in enumerate(individuals)]
# TODO need to pass the aspiration point, reservation point, and veto points to this function

    # TODO calculate the weighting vector based on the aspiration and reservation points for each objective
    # TODO calculate "d" for all individuals in the current front
    # TODO store the individual with lowest d value as the central point
    # TODO calculate outranking relation for each point
    # TODO store outranking solutions
    # TODO

    z_v = [] # TODO this needs to be passed when the NSGALBS is called
    z_r = [] # TODO this needs to be passed when the NSGALBS is called

    lambda_list = []

    for i in range(nobj):
        lambda_list[i] = 1 / (z_v[i] – z_r[i])

    rho = 10**-6

    for i in range(0,len(individuals)):
        max_term = []
        sum_term = []
        for j in range(nobj):
            max_term[j] = lambda_list[j] * (crowd[i][0][j] - z_r[j])
            sum_term[j] = crowd[i][0][j] - z_r[j]



    # TODO check the below works! - and also why does deap standard code use a list that is then assigned to the correct individuals,  should this approach be stuck to
    # TODO this may not work due to the index not existing, not sure if this works like dictionaries where it just creates it if it doesn't exist
        # inserts a new level into the list with a d value in for each individual
        crowd[i][2] = max(max_term) + rho * sum(sum_term)

    # this sorts the crowd list by the d value which is index [2] in each individual [0] is objective values and [1] is i value
    crowd.sort(key=lambda ind:ind[2])

    # TODO not needed now....
    z_c = min(individuals, key=attrgetter('d'))

    for i in range(0,len(individuals)):
        for j in range(0, nobj):
            if ((individuals[i].fitness.values[j] - z_c.fitness.values[j]) >= z_v[j]):
                individuals[i].m_v += 1

    # for i in range(0,len(individuals)):
    #     for j in range(0, nobj):
    #         if ((individuals[i].fitness.values[j] - z_c.fitness.values[j]) >= z_v[j]):
    #             individuals[i].m_v += 1

    # TODO difference between crowding rank and crowding distance?

    for ind in individuals:
        if (ind.m_v == 0):
            delta_temp = []
            for j in range(0, nobj):
                delta_temp[j] = ind.fitness.values[j] - z_c.fitness.values[j]
            ind.delta = max(delta_temp)

    

    # TODO rank the individuals as z_c first, then outranking solutions ranked by delta, then others. Next assign a fitness to them by using a linear fitness assignment, trying a non linear fitness assignment would be a good extension











# TODO perhaps set the









    for i, dist in enumerate(distances):
        individuals[i].fitness.crowding_dist = dist
#####################################################################



def selTournamentDCD(individuals, k):
    """Tournament selection based on dominance (D) between two individuals, if
    the two individuals do not interdominate the selection is made
    based on crowding distance (CD). The *individuals* sequence length has to
    be a multiple of 4. Starting from the beginning of the selected
    individuals, two consecutive individuals will be different (assuming all
    individuals in the input list are unique). Each individual from the input
    list won't be selected more than twice.
    This selection requires the individuals to have a :attr:`crowding_dist`
    attribute, which can be set by the :func:`assignCrowdingDist` function.
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :returns: A list of selected individuals.
    """

    if len(individuals)%4 !=0:
        raise Exception("selTournamentDCD: individuals length must be a multiple of 4")

    def tourn(ind1, ind2):
        if ind1.fitness.dominates(ind2.fitness):
            return ind1
        elif ind2.fitness.dominates(ind1.fitness):
            return ind2

        if ind1.fitness.crowding_dist < ind2.fitness.crowding_dist:
            return ind2
        elif ind1.fitness.crowding_dist > ind2.fitness.crowding_dist:
            return ind1

        if random.random() <= 0.5:
            return ind1
        return ind2

    individuals_1 = random.sample(individuals, len(individuals))
    individuals_2 = random.sample(individuals, len(individuals))

    chosen = []
    for i in xrange(0, k, 4):
        chosen.append(tourn(individuals_1[i],   individuals_1[i+1]))
        chosen.append(tourn(individuals_1[i+2], individuals_1[i+3]))
        chosen.append(tourn(individuals_2[i],   individuals_2[i+1]))
        chosen.append(tourn(individuals_2[i+2], individuals_2[i+3]))

    return chosen
