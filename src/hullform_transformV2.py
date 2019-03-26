# This code transforms an input hullform. It allows variation of: main dimensions, Cp, LCB. Methods taken from Computational ship design by Roh
# the coordinate system used is x is along the length, y is across the beam and z is from keel up
# the origin is at the aft perpendicular (??????) check if this is the convention
import numpy as np
import pandas as pd
from scipy.integrate import simps
from scipy import interpolate
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import plot
# TODO should really not import it as a pandas df if i'm not going to continue using this. Is there a way to import using numpy directly?

np.set_printoptions(threshold=np.inf)

# Importing offsets
offsets = pd.read_csv('..\src\static\data\VLCC offsets from Roh 2017.csv',
                      encoding='UTF-8',
                      sep=',',
                      header=0)
# offsets[:].apply(pd.to_numeric)
# print(offsets)

# Setting station and waterline spacing (mm)
stn_spacing = 10000.0
wl_spacing = 1000.0

# extracts the waterline numbers
wl = offsets.columns.tolist()
wl = wl[1:-1]  # excluding weird bits that pandas adds, could this lead to errors later?

# Converting waterline strings to floats... is there a quicker/cleaner way to do this?
waterlines = []

for item in wl:
    waterlines.append(float(item))

np.array(waterlines)

# converting waterlines from number to z axis coordinates
z = [float(waterline) * float(wl_spacing) for waterline in waterlines]

# extracts the station numbers
stations = np.array(offsets.iloc[:, 0]) * stn_spacing

# TODO this is not strictly correct, but how to correct it for the real waterline at current displacement?
lwl = max(stations)
print('lwl is')
print(lwl)
# converting the station numbers to x axis coordinates
x = [float(station) for station in stations]

offsets_clean_2 = offsets.iloc[:, 1:-1]

num_wl = offsets_clean_2.shape[1]
num_stn = offsets_clean_2.shape[0]

# This flattens the datafram to read along the station so: [stn1, wl1], [stn1, wl2], [stn1, wl3] etc.
Y = -1 * offsets_clean_2.values.flatten()

X, Z = np.meshgrid(x, z)

# reshaping the offsets to ensure they correspond to the waterlines and stations
Y = np.array(Y).reshape(27, 24)
Y = Y.T
# creating the second half of the hull surface
Y2 = Y * -1

colours = np.ones_like(Z)

plotly.tools.set_credentials_file(username='ucemcfr', api_key='MCDb7tRLz1VlwGB40a6M')
# Great! Simple to display a hullform using plotly, below important settings are aspectmode='data', could do with improving resolution, removing
data = [
    # plotting one half of the vessel
    go.Surface(
        x=X,
        y=Y,
        z=Z,
        surfacecolor=colours,
        showscale=False
    ),
    # plotting the other half
    go.Surface(
        x=X,
        y=Y2,
        z=Z,
        surfacecolor=colours,
        showscale=False
    )
]

layout = go.Layout(
    title='Offsets with plotly2',
    scene=dict(aspectmode='data')
)

fig = go.Figure(data=data, layout=layout)
plot(fig)

# calculating hydrostatics
# the below should be done using scipy.integrate.simps
# 1. integrate across offsets (below water level!) This needs a waterline defined as the DWL
#  1.1 submerged = z<=draft #boolean mask
#      submerged_inds = z[submerged] #returns the indices of submerged z values
#      y_sub = y[submerged_inds]
#      x_sub = x[submerged_inds] # think this should work, google boolean masks to find out more
# 2. do this for each station, saving results into a list called something like "section areas"
#   2.1 the key is how to index and iterate through this....
# 3. integrate across the list of section areas to get displaced volume
draft = 30000

# three one dimensional arrays - data structure of hull points
x_1d = X.flatten()
y_1d = Y.flatten()
z_1d = Z.flatten()

# list of tuples - data structure of hull points
zipped_coords = zip(x_1d, y_1d, z_1d)
#print(list(zipped_coords))


sub_bool = Z<=draft #boolean mask
#print(sub_bool)
#submerged_inds = z[sub_bool] #returns the indices of submerged z values
#print(submerged_inds)
y_sub = Y[sub_bool]
x_sub = X[sub_bool] # think this should work, google boolean masks to find out more
z_sub = Z[sub_bool]

# print(Y.shape)
# print(y_sub.shape)
# print(x_sub.shape)
# print(z_sub.shape)
# print(sub_bool.shape)

section_areas = []
for i in range(0, len(stations)):
    #filter z and y values based on stn value
    bool_mask = x_sub == stations[i]
    z_for_integration = z_sub[bool_mask]
    y_for_integration = y_sub[bool_mask]
    # check that that the values to be integrated aren't zero
    if z_for_integration.size > 0 and y_for_integration.size > 0:
        # integrate and add section area to list of section areas
        sect_area = simps(y_for_integration, z_for_integration, even='avg')
        section_areas.append(sect_area * -1)
    # add section area as zero if offsets are zero (makes sure section areas list is same length as sections list)
    else:
        section_areas.append(0)


def calc_hydrostatics(section_areas, stations, lwl):
    # integrating the section areas along length to get the volume
    displacement_mm = simps(section_areas, stations)

    # initialising an empty list for area moments
    area_moments = []

    # for each station, calculating the area moment and appending to the area moments list
    for i in range(0,len(stations)):
        moment = section_areas[i] * stations[i]
        area_moments.append(moment)

    # calculating the longitudinal centre of buoyancy
    lcb_mm = sum(area_moments)/sum(section_areas)
    lcb_pct = lcb_mm / lwl

    Cp = displacement_mm / (max(section_areas)*lwl)

    # # calculating length of parallel mid body TODO check this
    # parallel_mid_bod_x = x_1d[y_1d == max(y_1d)] # TODO this is wrong and causing problems
    # parallel_mid_bod_extents = [min(parallel_mid_bod_x), max(parallel_mid_bod_x)]
    # length_parallel_mid_bod = parallel_mid_bod_extents[1] - parallel_mid_bod_extents[0]

    #print(stations)

    return displacement_mm, lcb_mm, lcb_pct, Cp #, parallel_mid_bod_extents, length_parallel_mid_bod

##############
# Lackenby transform
def stn_shift(dCp, Lcb, dLcb, Cp, section_areas, stations_x, lwl, parallel_mid_bod_extents):
    ###### NB if there are issues check that all the sign conventions are correct i.e. are +ve and -ve x values the same throughout

    #### TODO non-dimensionalise all the non-dimensional things
    # TODO check the length of the lists being returned right at the end, has something gone wrong?

    midships = lwl/2

    #interpolate midship area from given section areas
    interpolated_areas = interpolate.interp1d(stations_x, section_areas, kind='cubic') # TODO is cubic the best spline to interpolate with?
    midship_area = interpolated_areas(midships)

    # split section areas into those forward and aft of midships

    #creating boolean masks for filtering
    forebody_mask = (stations_x > midships)
    aftbody_mask = (stations_x < midships)

    # making inputs into numpy arrays
    section_areas = np.array(section_areas)
    stations_x = np.array(stations_x)
    # applying boolean masks
    fore_areas = section_areas[forebody_mask] # this will be ordered from aft most to fwd most I think
    aft_areas = section_areas[aftbody_mask] # this will be ordered from aft most to fwd most I think
    aft_stations = stations_x[aftbody_mask]
    fore_stations = stations_x[forebody_mask]
    print('aft_stations before append = ', aft_stations)
    print('midships = ', midships)

    # add in interpolated midships station and area to the lists - TODO this assumes that these lists are ordered from aft most to fwd most - check
    aft_areas = np.append(aft_areas, midship_area)
    aft_stations = np.append(aft_stations, midships)
    fore_areas = np.insert(fore_areas, 0, midship_area)
    fore_stations = np.insert(fore_stations, 0, midships)
    print('aft_stations after append = ', aft_stations)

    # non-dimensionalising all inputs
    # sign conventions:
    # midship is zero
    # aft is negative, forward is positive

    section_areas_nondim = section_areas / midship_area
    stations_x_nondim = (np.array(stations_x) - lwl/2) / (lwl/2) # NB takes zero as midships, positive forwards
    aft_areas_nondim = aft_areas / midship_area
    fore_areas_nondim = fore_areas / midship_area
    aft_stations_nondim = (aft_stations - lwl/2)/(lwl/2)
    aft_stations_nondim = aft_stations_nondim # TODO this is making them non negative, check this is correct!
    print('aft_stations_nondim =  ', aft_stations_nondim)
    fore_stations_nondim = (fore_stations - lwl/2) / (lwl/2)

    # calculate centroid (x bar) for fore and aft parts
    # calculate area moments
    aft_area_moments_nondim = []
    aft_area_second_moments_nondim = []

    # TODO should this not be to the CENTRE of each strip not the actual section poisition? check
    for j in range(0, len(aft_stations_nondim)):
        aft_moment_nondim = aft_areas_nondim[j] * aft_stations_nondim[j]
        aft_area_moments_nondim.append(aft_moment_nondim)
        aft_second_moment_nondim = aft_areas_nondim[j] * aft_stations_nondim[j] ** 2 # TODO check this is correct
        aft_area_second_moments_nondim.append(aft_second_moment_nondim)

    # calculates the centroid as mm from baseline
    x_bar_a = sum(aft_area_moments_nondim) / sum(aft_areas_nondim) * -1 # TODO this -1 is here to correct the fact I have been using inconsistent coordinate systems
    I_a = sum(aft_area_second_moments_nondim)
    S_a = sum(aft_areas_nondim) # TODO check the units of this
    k_a = I_a / S_a

    fore_area_moments_nondim = []
    fore_area_second_moments_nondim = []

    for j in range(0, len(fore_stations_nondim)):
        fore_moment_nondim = fore_areas_nondim[j] * fore_stations_nondim[j]
        fore_area_moments_nondim.append(fore_moment_nondim)
        fore_second_moment_nondim = fore_areas_nondim[j] * fore_stations_nondim[j] ** 2 # TODO check this is correct
        fore_area_second_moments_nondim.append(fore_second_moment_nondim)

    # calculates the centroid as mm from baseline
    x_bar_f = sum(fore_area_moments_nondim) / sum(fore_areas_nondim)
    print('x_bar_f = ', x_bar_f)
    print('x_bar_a = ', x_bar_a)
    I_f = sum(fore_area_second_moments_nondim)
    S_f = sum(fore_areas_nondim) # TODO check the units of this
    k_f = I_f / S_f


    #calculates the centroid as fraction from midships
    # TODO need to think about sign conventions here i.e. is -ve backwards as is usual?
    # TODO by "fractional" is this fraction of LWL? or fraction of LWL/2? this is not clear
    # NB assuming fraction of half lwl
    # NB sign convention is fwd of midships is +ve, aft of midships is -ve
    #TODO I think these lines were an error so commented out, check
    # x_bar_a = - (x_bar_a / (lwl/2))
    # x_bar_f = x_bar_f / (lwl/2)

    # calculate cp
    # calculating forward volume
    vol_f = simps(fore_areas_nondim, fore_stations_nondim, even='avg')
    #calculating fwd cp
    Cp_f = vol_f / (max(fore_areas_nondim) * 1) # TODO not multiplied by length as the non dimensional length of the fore section is 1
    # calculating aft volume
    vol_a = simps(aft_areas_nondim, aft_stations_nondim, even='avg')
    print('vol_a, vol_f = ')
    print(vol_a)
    print(vol_f)
    # calculating aft cp
    Cp_a = vol_a / (max(aft_areas_nondim) * 1) # TODO these Cp figures seem really high - check - is this a mistake with the integration of section areas? Do I need midships in there?
    print('Cp aft, Cp fore =')
    print(Cp_a)
    print(Cp_f)

    print('Parallel mid bod extents = ', parallel_mid_bod_extents)
    # calculate length of parallel mid body
    Lp_f = 0
    print('Lp_f = ', Lp_f)
    Lp_a = 0 #TODO this was causing problems so set to zero
    # this function calculates the longitudinal shift for each section (fore [f] or aft [a]) as dx_fa
    # the fractional distance of the transverse section from the midship in the fore or aft body
    # TODO split these into calculations for foreship and calculations for aftship, otherwise the coefficients may get confused

    A_f = Cp_f * (1 - 2 * x_bar_f) - Lp_f * (1 - Cp_f)
    A_a = Cp_a * (1 - 2 * x_bar_a) - Lp_a * (1 - Cp_a)

    B_f = (Cp_f * (2 * x_bar_f - 3 * k_f ** 2 - Lp_f * (1 - x_bar_f))) / A_f
    B_a = (Cp_a * (2 * x_bar_a - 3 * k_a ** 2 - Lp_a * (1 - x_bar_a))) / A_a

    print('B_f, B_a = ')
    print(B_f)
    print(B_a)
    print('Lp_f, Lp_a = ')
    print(Lp_f, Lp_a)

    C_f = (B_f * (1 - Cp_f) - Cp_f * (1 - 2 * x_bar_f)) / (1 - Lp_f)
    C_a = (B_a * (1 - Cp_a) - Cp_a * (1 - 2 * x_bar_a)) / (1 - Lp_a)

    dCp_f = (2*(dCp*(B_a + Lcb) + dLcb * (Cp+dCp)) + C_f * dLp_f - C_a * dLp_a) / (B_f + B_a)
    dCp_a = (2*(dCp*(B_f - Lcb) - dLcb * (Cp+dCp)) - C_f * dLp_f + C_a * dLp_a) / (B_f + B_a)

    print('dCp_f =   ', dCp_f)
    print('dCp_a =   ', dCp_a)
    #dLp_f = (dCp_f / (1 - Cp_f)) * (1 - Lp_f)
    #dLp_a = (dCp_a / (1 - Cp_a)) * (1 - Lp_a) # TODO check this is the correct usage of this equation - is it just a proof?



# TODO Nota bene: the only thing changing here is the x_fa, and then dx_fa. So what is the most efficient way of calculating these for each section?

    # now iterating over the fore stations list to calculate the station shift for each station
    station_deltas_fore = []
    transformed_fore_stns = np.zeros(len(fore_stations))
    trns_fore_stn2 = []

    for j in range(0, len(fore_stations_nondim)):
        stn_x = fore_stations_nondim[j]
        x_fa = stn_x
        dx_f = (1 - x_fa) * (dLp_f / (1 - Lp_f) + ((x_fa - Lp_f) / A_f) * (dCp_f - dLp_f * (1 - Cp_f) / (1 - Lp_f)))
        station_deltas_fore.append(dx_f)
        # adding the delta x to the non dimensional x postition and redimensionalising
        trns_fore_stn2.append(((dx_f + x_fa) * (lwl/2)) + (lwl/2))

    station_deltas_aft = []
    transformed_aft_stns = np.zeros(len(aft_stations))
    trns_aft_stn2 = []

    for j in range(0, len(aft_stations_nondim)):
        stn_x = aft_stations_nondim[j] * -1
        # this non dimensionalises the stations
        x_fa = stn_x
        dx_a = (1 - x_fa) * (dLp_a / (1 - Lp_a) + ((x_fa - Lp_a) / A_a) * (dCp_a - dLp_a * (1 - Cp_a) / (1 - Lp_a)))
        station_deltas_aft.append(dx_a)
        # redimensionalising station coordinates and adding the transform
        trns_aft_stn2.append(((dx_a + x_fa) * -1 * (lwl/2)) + (lwl/2))

    station_deltas_aft = station_deltas_aft[:-1]
    station_deltas_fore = station_deltas_fore[1:]

    # # TODO for these two loops, check that addition is the right thing!
    # for j in range(0, len(fore_stations)):
    #     transformed_fore_stns[j] = fore_stations[j] + station_deltas_fore[j]
    #
    # # TODO check what impact the changing of the sign convention / baseline had on this
    # for j in range(0, len(aft_stations)):
    #     transformed_aft_stns[j] = aft_stations[j] + station_deltas_aft[j]

    # concatenating the fore and aft stations but removing the duplicate midship section which was interpolated from other sections
    transformed_stns = np.concatenate((trns_aft_stn2[:-1], trns_fore_stn2[1:]))

    return transformed_stns, station_deltas_aft, station_deltas_fore


displacement_mm, lcb_mm, lcb_pct, Cp = calc_hydrostatics(section_areas, stations, lwl)
Lcb = 0
dLp_f = 0
dLp_a = 0
dCp = -0.05
dLcb = 0.1
stations_x = stations
trans_stn, stations_deltas_aft, stations_deltas_fore = stn_shift(dCp, Lcb, dLcb, Cp, section_areas, stations_x, lwl, [0,0]) # NB This is the new X location of the stations
print('transformed stations = ', trans_stn)


station_deltas_all = np.concatenate((stations_deltas_aft, stations_deltas_fore))
print('deltax for all strations = ', station_deltas_all)

# TODO why is the aft most station moving so much? what's gone wrong?

plt.plot(trans_stn, section_areas, 'g')
plt.plot(stations, section_areas, 'r')
plt.show()

plt.plot(station_deltas_all)
plt.show()

#test123 = (trans_stn - stations)
#print(test123)
##########################

data_sub = [
    # plotting one half of the vessel
    go.Surface(
        x=x_sub,
        y=y_sub,
        z=z_sub,
        surfacecolor=colours,
        showscale=False
    )
]

layout_sub = go.Layout(
    title='submerged hullform',
    scene=dict(aspectmode='data')
)

fig_submerged = go.Figure(data=data_sub, layout=layout_sub)
#plot(fig_submerged)


data2 = [
    # plotting one half of the vessel
    go.Surface(
        x=trans_stn,
        y=Y,
        z=Z,
        surfacecolor=colours,
        showscale=False
    ),
    # plotting the other half
    go.Surface(
        x=X,
        y=Y2,
        z=Z,
        surfacecolor=colours,
        showscale=False
    )
]

layout2 = go.Layout(
    title='Offsets with plotly2',
    scene=dict(aspectmode='data')
)

fig2 = go.Figure(data=data2, layout=layout2)
plot(fig2)

# TODO create classes - speak to research software services for help with this
# TODO overall structure of the tool - this needs to be nailed down now
# TODO



# Gross scaling

# this refers to overall length
# alpha = child_length / parent_length
#
# beta = child_beam / parent_beam
#
# gamma = child_depth / parent_depth
#
# delta = child_draft / parent_draft
#
# epsilon = (child_depth - child_draft) / (parent_depth / parent_draft)

# Coordinate system is taken as y is transverse, x is longiotudinal, and z is vertical. So y is across the beam, x is along the fore aft direction and z is towards the sky.
parent_x_offsets = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
parent_y_offsets = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
parent_z_offsets = np.array([-5, -4, -3, -2, -1, 0, 1, 2, 3, 4])

alpha = 1.5
beta = 2
gamma = 3
delta = 2.5
epsilon = 5

child_x_offsets = alpha * parent_x_offsets
child_y_offsets = beta * parent_y_offsets
child_z_offsets = np.concatenate((delta * parent_z_offsets[np.where(parent_z_offsets <= 0)], epsilon * parent_z_offsets[np.where(parent_z_offsets > 0)]))

# Lackenby tranform
