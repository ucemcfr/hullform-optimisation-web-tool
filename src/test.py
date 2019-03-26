from src.models.Ship import Ship
from src.database import Database



ship1 = Ship(35, 200, 210, 30, 35, 10, 35000, 0, 0.7, 0.8, 0)

motion = ship1.calculate_motions()
res = ship1.calculate_resistance()
stab = ship1.calculate_stability()


print("Resistance is  " + str(round(ship1.total_resistance/1000)) + "  kN")
print("Max. vertical acceleration is  "+ str(round(ship1.max_vert_acceleration, 4)) + "  m/s/s")
print("KM is  " + str(round(ship1.km)) + "  m")

Database.initialize()
ship1.save_to_mongo()

# next thing is to code html for adding ships