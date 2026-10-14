"""Обёртка-пилот"""


class Pilot:
    def __init__(self, chair):
        self._chair = chair

    def take_off(self, distance_km=1):
        return self._chair.move(distance_km, "air")

    def fly(self, distance_km):
        return self._chair.move(distance_km, "air")

    def dive(self, distance_km=1):
        return self._chair.move(distance_km, "water")

    def travel_on_ground(self, distance_km):
        return self._chair.move(distance_km, "ground")

    def check_obstacle(self, obstacle):
        return self._chair.can_overcome(obstacle)

    def estimate_energy(self, distance_km, terrain):
        return self._chair.calculate_energy(distance_km, terrain)

    def recharge(self, amount):
        return self._chair.recharge(amount)

    def status(self):
        return self._chair.get_status()
