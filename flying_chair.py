EPS = 1e-9


class CrazyVehicleError(RuntimeError):
    "Базовое доменное исключение транспорта."


class FlyingChairError(CrazyVehicleError):
    "Базовое исключение летающего кресла."


class BatteryEmpty(FlyingChairError):
    "Недостаточный заряд для перемещения."


class FlyingChairCannotMoveOnGround(FlyingChairError):
    "Попытка движения по земле."


def check_string(param_name, value):
    if not isinstance(value, str):
        raise TypeError(param_name + " must be a string")
    return value


def check_number(param_name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(param_name + " must be a number")
    return float(value)


def greater_than(value, threshold):
    return value - threshold > EPS


class FlyingChair:

    def __init__(self, name, mass_kg, vert_engine_power,
                 horizont_engine_power, max_speed_kmh, battery=100.0):
        self._name = check_string("name", name)
        if self._name == "":
            raise ValueError("name must not be empty")

        self._mass_kg = check_number("mass_kg", mass_kg)
        if self._mass_kg <= 0:
            raise ValueError("mass_kg must be positive")

        self._vert_engine_power = check_number(
            "vert_engine_power", vert_engine_power)
        if self._vert_engine_power <= 0:
            raise ValueError("vert_engine_power must be positive")

        self._horizont_engine_power = check_number(
            "horizont_engine_power", horizont_engine_power)
        if self._horizont_engine_power <= 0:
            raise ValueError("horizont_engine_power must be positive")

        self._max_speed_kmh = check_number("max_speed_kmh", max_speed_kmh)
        if self._max_speed_kmh <= 0:
            raise ValueError("max_speed_kmh must be positive")

        self._battery = check_number("battery", battery)
        if self._battery < 0 or self._battery > 100:
            raise ValueError("battery must be between 0 and 100")

        self._position_km = 0.0
        self._is_flying = False
        self._last_terrain = "ground"

    @property
    def name(self):
        return self._name

    @property
    def mass_kg(self):
        return self._mass_kg

    @property
    def vert_engine_power(self):
        return self._vert_engine_power

    @property
    def horizont_engine_power(self):
        return self._horizont_engine_power

    @property
    def max_speed_kmh(self):
        return self._max_speed_kmh

    @property
    def battery(self):
        return self._battery

    @property
    def position_km(self):
        return self._position_km

    @property
    def is_flying(self):
        return self._is_flying

    def _check_distance(self, distance_km):
        distance = check_number("distance_km", distance_km)
        if distance <= 0:
            raise ValueError("distance_km must be positive")
        return distance

    def _check_terrain(self, terrain):
        terrain = check_string("terrain", terrain)
        if terrain not in ("air", "water", "ground"):
            raise ValueError("unknown terrain: " + terrain)
        return terrain

    def _energy_cost(self, distance, terrain):
        if terrain == "air":
            return distance * 2.0
        if terrain == "water":
            return distance * 1.0
        raise FlyingChairCannotMoveOnGround(
            "flying chair cannot move on ground")

    def move(self, distance_km, terrain):
        distance = self._check_distance(distance_km)
        terrain = self._check_terrain(terrain)

        if terrain == "ground":
            raise FlyingChairCannotMoveOnGround(
                "flying chair cannot move on ground")

        required = self._energy_cost(distance, terrain)

        if self._battery + EPS < required:
            raise BatteryEmpty(
                "not enough battery: required " + str(required) +
                ", have " + str(self._battery))

        if terrain == "air":
            speed = self._max_speed_kmh
        else:
            speed = self._max_speed_kmh * 0.5
        time = distance / speed

        new_battery = self._battery - required
        if abs(new_battery) <= EPS:
            new_battery = 0.0

        self._position_km = self._position_km + distance
        self._battery = new_battery
        self._is_flying = (terrain == "air")
        self._last_terrain = terrain

        return float(time)

    def can_overcome(self, obstacle):
        obstacle = check_string("obstacle", obstacle)
        if obstacle not in ("wall", "river", "tree", "mountain"):
            raise ValueError("unknown obstacle: " + obstacle)

        if obstacle == "wall":
            return bool(self._is_flying)

        if obstacle == "river":
            if self._last_terrain == "water":
                return True
            return greater_than(self._battery, 20.0)

        diff = self._vert_engine_power - self._mass_kg

        if obstacle == "tree":
            return greater_than(diff, 1.0)

        return greater_than(diff, 1.3) and greater_than(self._battery, 50.0)

    def calculate_energy(self, distance_km, terrain):
        distance = self._check_distance(distance_km)
        terrain = self._check_terrain(terrain)

        if terrain == "ground":
            raise FlyingChairCannotMoveOnGround(
                "flying chair cannot move on ground")

        return float(self._energy_cost(distance, terrain))

    def recharge(self, amount):
        amount = check_number("amount", amount)
        if amount <= 0:
            raise ValueError("amount must be positive")

        new_battery = self._battery + amount
        if new_battery > 100.0 or abs(new_battery - 100.0) <= EPS:
            new_battery = 100.0
        self._battery = new_battery

    def get_status(self):
        return {
            "name": self._name,
            "mass_kg": self._mass_kg,
            "battery": self._battery,
            "position_km": self._position_km,
            "is_flying": self._is_flying,
            "vert_engine_power": self._vert_engine_power,
            "horizont_engine_power": self._horizont_engine_power,
            "max_speed_kmh": self._max_speed_kmh,
        }
    