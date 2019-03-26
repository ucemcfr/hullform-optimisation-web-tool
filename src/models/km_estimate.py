def km_calc(LWL, B, T, Cwp, VolDisp, Vcb=None):  # This is taken from Stephen Wallis' notes from Solent YPD course (Marine Craft Design & Development)

    Cwi = 12 / (Cwp ** 2)  # NOTE THIS IS APPROXIMATE
    I = (LWL * B ** 3) / Cwi
    Awp = Cwp * LWL * B
    if Vcb is None: Vcb = (1 / 3) * ((T / 2) + (VolDisp / Awp))  # Using Morrish's rule. Distance measured FROM WATERLINE DOWNWARDS
    BM = I / VolDisp
    KB = T - Vcb
    KM = BM + KB

    return KM
