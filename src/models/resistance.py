import numpy as np


def calculate_holtrop_resistance(lwl, bwl, draft, lcb, vol_disp, velocity, c_m, c_wp):
    rho = 1.025  # TODO check units
    g = 9.807
    kin_visc = 1.19 * (10 ** -6)  # saltwater at 15 deg C

    f_n = velocity / np.sqrt(g * lwl)

    r_n = (velocity * lwl) / kin_visc

    a_m = bwl * draft * c_m
    c_b = vol_disp / (lwl * bwl * draft)
    c_p = vol_disp / (a_m * lwl)

    c_f = 0.075 / ((np.log10(r_n) - 2) ** 2) # TODO returning error "invalid value encountered in log10"
# TODO how is lcb measured and used? In the Holtrop paper it is as % of lwl forward of midships
    c_stern = 0  # Normal section shape
    c14 = 1 + 0.011 * c_stern
    l_r = lwl * (1 - c_p + 0.06 * c_p * lcb / (4 * c_p - 1))
    # formFactor = 0.93 + 0.487118 * c14 * ((B/LWL)**1.06806) * ((T/LWL)**0.46106) * ((LWL/Lr)**0.121563*(
    # LWL**3/VolDisp)**0.36486) * ((1-Cp)**-0.604247)
    form_factor2 = 0.93 + 0.487118 * c14 * ((bwl / lwl) ** 1.06806) * ((draft / lwl) ** 0.46106) * (
                (lwl / l_r) ** 0.121563) * (((lwl ** 3) / vol_disp) ** 0.36486) * ((1 - c_p) ** -0.604247) # TODO also get invalid value encountered in double scalars here sometimes
    wsa = lwl * (2 * draft + bwl) * (c_m ** 0.5) * (0.453 + 0.4425 * c_b - 0.2862 * c_m - 0.003467 * (
                bwl / draft) + 0.3696 * c_wp)  # if bulb were being taken into account also include the following
    # term: (+ 2.38 * Abt / Cb)

    r_f = 0.5 * rho * wsa * (velocity ** 2) * c_f
    r_v = r_f * form_factor2

    a_bt = 0 # TODO look at these and correct them to be taken as inputs or to be estimated.
    a_t = 0
    h_b = 0
    t_f = draft  # TODO This isn't strictly true

    # TODO sometimes this gives two runtime warnings: overflow encountered in exp, and invalid value encountered in double scalars, add appropriate error handling
    i_e = 1 + 89 * np.exp(-((lwl / bwl) ** 0.80856) * ((1 - c_wp) ** 0.30484) * ((1 - c_p - 0.0225 * lcb) ** 0.6367) * ((l_r / bwl) ** 0.34574) * ((100 * vol_disp / lwl ** 3) ** 0.16302))
    print ('lwl:  ', lwl, 'bwl:  ', bwl, 'cwp:  ', c_wp, 'cp:  ', c_p, 'lcb:  ', lcb, 'l_r:  ', l_r, 'vol disp:  ', vol_disp)
    d = -0.9
    c3 = 0.56 * a_bt ** 1.5 / (bwl * draft * (0.31 * a_bt ** (1 / 2) + t_f - h_b))
    c2 = np.exp(-1.89 * (c3 ** (1 / 2)))
    c5 = (1 - 0.8 * a_t / (bwl * draft * c_m))
    c17 = 6919.3 * c_m ** (-1.3346) * (vol_disp / lwl ** 3) ** 2.00977 * (lwl / bwl - 2) ** 1.40692
    m3 = -7.2035 * (bwl / lwl) ** 0.326869 * (draft / bwl) ** 0.605375

    if lwl / bwl < 12:
        lambda_ = 1.446 * c_p - 0.03 * lwl / bwl

    else:
        lambda_ = 1.446 * c_p - 0.36

    if lwl ** 3 / vol_disp < 512:
        c15 = -1.69385

    elif 512 < lwl ** 3 / vol_disp < 1726.91:
        c15 = -1.69385 + (lwl / vol_disp ** (1 / 3) - 8) / 2.36

    else:
        c15 = 0

    m4 = c15 * 0.4 * np.exp(-0.034 * f_n ** (-3.29)) # TODO Returning error "invalid value encountered in double_scalars"

    r_wb = c17 * c2 * c5 * vol_disp * rho * g * np.exp(m3 * f_n ** d + m4 * np.cos(lambda_ * f_n ** (-2))) # TODO this is returning error "invalid value encountered in double_scalars"

    if bwl / lwl < 0.11:
        c7 = 0.229577 * (bwl / lwl) ** 0.33333

    elif 0.11 < bwl / lwl < 0.25:
        c7 = bwl / lwl

    else:
        c7 = 0.5 - 0.0625 * lwl / bwl

    c1 = 2223105 * c7 ** 3.78613 * (draft / bwl) ** 1.07961 * (90 - i_e) ** (-1.37565)

    if c_p < 0.8:
        c16 = 8.07981 * c_p - 13.8673 * c_p ** 2 + 6.984388 * c_p ** 3

    else:
        c16 = 1.73014 - 0.7067 * c_p

    m1 = 0.0140407 * lwl / draft - 1.75254 * vol_disp ** (1 / 3) / lwl - 4.79323 * bwl / lwl - c16

    r_wa = c1 * c2 * c5 * vol_disp * rho * g * np.exp(m1 * f_n ** d + m4 * np.cos(lambda_ * f_n ** (-2))) # TODO this is returning an error, why? Error: "invalid value encountered in double_scalars"

    if f_n < 0.4:
        r_w = r_wa
    elif f_n > 0.55:
        r_w = r_wb
    else:
        r_w = r_wa + (10 * f_n - 4) * (r_wb - r_wa) / 1.5

    if t_f / lwl <= 0.04:
        c4 = t_f / lwl
    else:
        c4 = 0.04

    ##################################################################
    # This is just added to get it working, check correct c2 value in holtrop paper
    c2 = 1
    #####################################################################

    c_a = 0.006 * (lwl + 100) ** -0.16 - 0.00205 + 0.003 * (lwl / 7.5) ** 0.5 * c_b ** 4 * c2 * (0.04 - c4)

    r_a = 0.5 * rho * velocity ** 2 * wsa * c_a

    r_t = r_v + r_w + r_a

    return r_t


#  TODO
#  Add contraints on dimensional ratios from Holtrop paper with a suitable error handling procedure and user popup
