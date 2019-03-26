from src.database import Database
from src.models.Ship import Ship
import numpy as np
from pprint import pprint
import time
# generate 1000 random ships i.e. lwl, loa=x*lwl, bwl, boa=x*bwl, draft, vol_disp, lcb, c_m, c_wp, heading
# velocity, lwl, loa, bwl, boa, draft, vol_disp, lcb, c_m, c_wp, heading

Database.initialize()

l_b_ratio = np.ndarray.tolist(np.random.randint(50, 60, 1000) / 10)
b_t_ratio = np.ndarray.tolist(np.random.randint(21, 29, 1000) / 10)
l_overhang = np.ndarray.tolist(np.random.randint(100, 150, 1000) / 1000)
b_overhang = np.ndarray.tolist(np.random.randint(20, 80, 1000) / 1000)
c_b = np.ndarray.tolist(np.random.randint(65, 75, 1000) / 100)
lwl = np.ndarray.tolist(np.random.randint(1000, 1200, 1000) / 10)
c_m = np.ndarray.tolist(np.random.randint(75, 86, 1000) / 100)
c_wp = np.ndarray.tolist(np.random.randint(66, 80, 1000) / 100)
velocity = np.ndarray.tolist(np.random.randint(110, 180, 1000) / 10)
lcb = np.ndarray.tolist(np.random.randint(100, 500, 1000) / 100)

loa = [None] * 100
bwl = [None] * 100
boa = [None] * 100
draft = [None] * 100
vol_disp = [None] * 100
heading = [0] * 100

for i in range(0, 100):
    bwl[i] = lwl[i] / l_b_ratio[i]
    loa[i] = lwl[i] * 1 + l_overhang[i]
    boa[i] = bwl[i] * 1 + b_overhang[i]
    draft[i] = bwl[i] / b_t_ratio[i]
    vol_disp[i] = lwl[i] * bwl[i] * draft[i] * c_b[i]

# print('loa is ' + str(loa))
# print(lwl)
# print('bwl is' + str(bwl))
# print(c_m)
# print(boa)
# print(vol_disp)
# print(draft)


for j in range(0, 100):
    vel_ = velocity[j]
    lwl_ = lwl[j]
    loa_ = loa[j]
    bwl_ = bwl[j]
    boa_ = boa[j]
    draft_ = draft[j]
    vol_disp_ = vol_disp[j]
    lcb_ = lcb[j]
    c_m_ = c_m[j]
    c_wp_ = c_wp[j]
    heading_ = heading[j]

    shippyship = Ship(vel_, lwl_, loa_, bwl_, boa_, draft_, vol_disp_, lcb_, c_m_, c_wp_, heading_)
    pprint(vars(shippyship))
    # time.sleep(0.5)
    if shippyship.total_resistance is None:
        continue

# print(new_ship)
    shippyship.save_to_mongo()

# print(new_ship[10].lwl)
# velocity, lwl, loa, bwl, boa, draft, vol_disp, lcb, c_m, c_wp, heading=None, vcb=None, total_resistance=None, km=None, max_vert_acceleration=None
