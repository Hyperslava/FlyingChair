"""Shared fixtures and assertions."""

import re
import unittest

from flying_chair import (
    BatteryEmpty,
    CrazyVehicleError,
    FlyingChair,
    FlyingChairCannotMoveOnGround,
    FlyingChairError,
)


DEFAULTS = dict(
    name="Царь", mass_kg=80.0, vert_engine_power=82.0,
    horizont_engine_power=50.0, max_speed_kmh=150.0, battery=100.0,
)
ATTRIBUTES = (*DEFAULTS, "position_km", "is_flying")
NUMERIC_PARAMETERS = tuple(key for key in DEFAULTS if key != "name")


def make_chair(**overrides):
    return FlyingChair(**(DEFAULTS | overrides))


def snapshot(chair):
    return {name: getattr(chair, name) for name in ATTRIBUTES}


class ChairTestCase(unittest.TestCase):
    def assert_state(self, chair, position, battery, flying):
        self.assertAlmostEqual(chair.position_km, position, delta=1e-9)
        self.assertAlmostEqual(chair.battery, battery, delta=1e-9)
        self.assertIs(chair.is_flying, flying)

    def assert_time(self, value, expected):
        self.assertIs(type(value), float)
        self.assertAlmostEqual(value, expected, delta=1e-9)

    def assert_error(self, error, expected_type, message):
        self.assertIs(type(error), expected_type)
        self.assertEqual(str(error), message)

    def assert_battery_error(self, error, required, available):
        self.assertIs(type(error), BatteryEmpty)
        # SPEC fixes the values, but not the choice of 60 versus 60.0.
        match = re.fullmatch(
            r"not enough battery: required ([0-9]+(?:\.[0-9]+)?), "
            r"have ([0-9]+(?:\.[0-9]+)?)", str(error),
        )
        self.assertIsNotNone(match, str(error))
        self.assertAlmostEqual(float(match[1]), required, delta=1e-9)
        self.assertAlmostEqual(float(match[2]), available, delta=1e-9)
