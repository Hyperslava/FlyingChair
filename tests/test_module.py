"""40 модульных тест-кейсов в формате Arrange / Act / Assert."""

from tests.support import (
    ATTRIBUTES, DEFAULTS, NUMERIC_PARAMETERS, BatteryEmpty, ChairTestCase,
    CrazyVehicleError, FlyingChair, FlyingChairCannotMoveOnGround,
    FlyingChairError, make_chair, snapshot,
)


class FlyingChairModuleTests(ChairTestCase):
    def test_TC_M_001_init_stores_parameters(self):
        """TC-M-001: создание кресла и начальное состояние."""
        # Arrange
        parameters = DEFAULTS.copy()
        # Act
        chair = FlyingChair(**parameters)
        # Assert
        self.assertIsInstance(chair, FlyingChair)
        for name, expected in parameters.items():
            self.assertEqual(getattr(chair, name), expected)
        self.assert_state(chair, 0, 100, False)

    def test_TC_M_002_init_empty_name_raises(self):
        """TC-M-002: пустое имя."""
        # Arrange
        parameters = DEFAULTS | {"name": ""}
        # Act
        with self.assertRaises(ValueError) as caught:
            FlyingChair(**parameters)
        # Assert
        self.assert_error(caught.exception, ValueError, "name must not be empty")

    def test_TC_M_003_init_nonpositive_parameters_raise(self):
        """TC-M-003: неположительные масса, мощность двигателей и скорость."""
        for name in NUMERIC_PARAMETERS[:-1]:
            for value in (0, -1):
                with self.subTest(parameter=name, value=value):
                    # Arrange
                    parameters = DEFAULTS | {name: value}
                    # Act
                    with self.assertRaises(ValueError) as caught:
                        FlyingChair(**parameters)
                    # Assert
                    self.assert_error(caught.exception, ValueError, f"{name} must be positive")

    def test_TC_M_004_init_battery_bounds(self):
        """TC-M-004: допустимые границы заряда и значения вне диапазона."""
        # Arrange
        parameters_without_battery = {name: value for name, value in DEFAULTS.items() if name != "battery"}
        # Act
        chair_with_default = FlyingChair(**parameters_without_battery)
        # Assert
        self.assertEqual(chair_with_default.battery, 100.0)
        for value in (0, 100, -1, 101):
            with self.subTest(battery=value):
                # Arrange
                parameters = DEFAULTS | {"battery": value}
                # Act
                if value in (0, 100):
                    chair = FlyingChair(**parameters)
                else:
                    with self.assertRaises(ValueError) as caught:
                        FlyingChair(**parameters)
                # Assert
                if value in (0, 100):
                    self.assertEqual(chair.battery, value)
                else:
                    self.assert_error(caught.exception, ValueError, "battery must be between 0 and 100")

    def test_TC_M_005_public_attributes_types(self):
        """TC-M-005: все публичные атрибуты и их типы."""
        # Arrange
        chair = make_chair()
        expected = DEFAULTS | {"position_km": 0.0, "is_flying": False}
        # Act
        values = snapshot(chair)
        # Assert
        self.assertEqual(values, expected)
        for name, value in values.items():
            with self.subTest(attribute=name):
                self.assertIs(type(value), str if name == "name" else bool if name == "is_flying" else float)

    def test_TC_M_006_public_attributes_read_only(self):
        """TC-M-006: прямое присваивание атрибутам отклоняется."""
        for name in ATTRIBUTES:
            with self.subTest(attribute=name):
                # Arrange
                chair = make_chair()
                before = snapshot(chair)
                value = "Другой" if name == "name" else True if name == "is_flying" else 999.0
                # Act
                with self.assertRaises(AttributeError):
                    setattr(chair, name, value)
                # Assert
                self.assertEqual(snapshot(chair), before)

    def test_TC_M_007_move_air(self):
        """TC-M-007: время полёта, расход заряда и состояние."""
        # Arrange
        chair = make_chair()
        # Act
        time = chair.move(30, "air")
        # Assert
        self.assert_time(time, 0.2)
        self.assert_state(chair, 30, 40, True)

    def test_TC_M_008_move_water(self):
        """TC-M-008: скорость в воде вдвое ниже воздушной."""
        # Arrange
        chair = make_chair()
        # Act
        time = chair.move(6, "water")
        # Assert
        self.assert_time(time, 0.08)
        self.assert_state(chair, 6, 94, False)

    def test_TC_M_009_move_ground_raises(self):
        """TC-M-009: движение и расчёт на земле вызывают доменное исключение."""
        for method in ("move", "calculate_energy"):
            with self.subTest(method=method):
                # Arrange
                chair = make_chair()
                before = snapshot(chair)
                # Act
                with self.assertRaises(FlyingChairCannotMoveOnGround) as caught:
                    getattr(chair, method)(1, "ground")
                # Assert
                self.assert_error(caught.exception, FlyingChairCannotMoveOnGround,
                                  "flying chair cannot move on ground")
                self.assertEqual(snapshot(chair), before)

    def test_TC_M_010_move_insufficient_battery_raises(self):
        """TC-M-010: положительный заряд недостаточен для перемещения."""
        for distance, terrain, cost in ((30, "air", 60), (11, "water", 11)):
            with self.subTest(terrain=terrain):
                # Arrange
                chair = make_chair(battery=10.0)
                before = snapshot(chair)
                # Act
                with self.assertRaises(BatteryEmpty) as caught:
                    chair.move(distance, terrain)
                # Assert
                self.assert_battery_error(caught.exception, cost, 10)
                self.assertEqual(snapshot(chair), before)

    def test_TC_M_011_move_exact_battery_succeeds(self):
        """TC-M-011: маршрут может израсходовать весь заряд батареи."""
        for distance, terrain, speed in ((10, "air", 150), (20, "water", 75)):
            with self.subTest(terrain=terrain):
                # Arrange
                chair = make_chair(battery=20.0)
                # Act
                time = chair.move(distance, terrain)
                # Assert
                self.assert_time(time, distance / speed)
                self.assert_state(chair, distance, 0, terrain == "air")
        # Arrange
        chair = make_chair(battery=0.3)
        # Act
        times = [chair.move(0.1, "water") for _ in range(3)]
        # Assert
        for time in times:
            self.assert_time(time, 0.1 / 75)
        self.assert_state(chair, 0.3, 0.0, False)

    def test_TC_M_012_move_error_preserves_state(self):
        """TC-M-012: неудачные перемещения сохраняют состояние кресла в полёте."""
        variants = ((50, "air", BatteryEmpty), (1, "ground", FlyingChairCannotMoveOnGround),
                    (0, "air", ValueError), (1, "lava", ValueError))
        for distance, terrain, error in variants:
            with self.subTest(distance=distance, terrain=terrain):
                # Arrange
                chair = make_chair()
                chair.move(5, "air")
                before = snapshot(chair)
                # Act
                with self.assertRaises(error) as caught:
                    chair.move(distance, terrain)
                # Assert
                self.assertIs(type(caught.exception), error)
                self.assertEqual(snapshot(chair), before)
                self.assert_state(chair, 5, 90, True)

    def test_TC_M_013_distance_nonpositive_raises(self):
        """TC-M-013: недопустимые расстояния при движении и расчёте расхода."""
        for method in ("move", "calculate_energy"):
            for distance in (0, -1):
                with self.subTest(method=method, distance=distance):
                    # Arrange
                    chair = make_chair()
                    before = snapshot(chair)
                    # Act
                    with self.assertRaises(ValueError) as caught:
                        getattr(chair, method)(distance, "air")
                    # Assert
                    self.assert_error(caught.exception, ValueError, "distance_km must be positive")
                    self.assertEqual(snapshot(chair), before)

    def test_TC_M_014_unknown_terrain_raises(self):
        """TC-M-014: неизвестная среда."""
        for method in ("move", "calculate_energy"):
            with self.subTest(method=method):
                # Arrange
                chair = make_chair()
                before = snapshot(chair)
                # Act
                with self.assertRaises(ValueError) as caught:
                    getattr(chair, method)(1, "lava")
                # Assert
                self.assert_error(caught.exception, ValueError, "unknown terrain: lava")
                self.assertEqual(snapshot(chair), before)

    def test_TC_M_015_overcome_wall_requires_flight(self):
        """TC-M-015: преодоление стены с земли, из воздуха и из воды."""
        for terrain, expected in ((None, False), ("air", True), ("water", False)):
            with self.subTest(terrain=terrain):
                # Arrange
                chair = make_chair()
                if terrain:
                    chair.move(1, terrain)
                # Act
                result = chair.can_overcome("wall")
                # Assert
                self.assertIs(result, expected)

    def test_TC_M_016_overcome_river_in_water(self):
        """TC-M-016: нахождения в воде достаточно при заряде 0 или 20."""
        for battery in (1.0, 21.0):
            with self.subTest(battery=battery):
                # Arrange
                chair = make_chair(battery=battery)
                chair.move(1, "water")
                # Act
                result = chair.can_overcome("river")
                # Assert
                self.assertIs(result, True)
                self.assertEqual(chair.battery, battery - 1)

    def test_TC_M_017_overcome_river_battery_threshold(self):
        """TC-M-017: вне воды заряд должен превышать 20."""
        for battery, expected in ((0.0, False), (20.0, False), (21.0, True)):
            with self.subTest(battery=battery):
                # Arrange
                chair = make_chair(battery=battery)
                # Act
                result = chair.can_overcome("river")
                # Assert
                self.assertIs(result, expected)

    def test_TC_M_018_overcome_tree_power_threshold(self):
        """TC-M-018: строгий порог мощности двигателя для преодоления дерева."""
        for mass, power, expected in ((1.0, 1.5, False), (1.0, 2.0, False),
                                      (1.2, 2.2, False), (1.0, 2.1, True)):
            with self.subTest(mass=mass, power=power):
                # Arrange
                chair = make_chair(mass_kg=mass, vert_engine_power=power)
                # Act
                result = chair.can_overcome("tree")
                # Assert
                self.assertIs(result, expected)

    def test_TC_M_019_overcome_mountain_thresholds(self):
        """TC-M-019: оба пороговых условия для горы должны выполняться."""
        for power, battery, expected in ((2.0, 100.0, False), (2.3, 100.0, False),
                                         (2.4, 50.0, False), (2.4, 51.0, True)):
            with self.subTest(power=power, battery=battery):
                # Arrange
                chair = make_chair(mass_kg=1.0, vert_engine_power=power, battery=battery)
                # Act
                result = chair.can_overcome("mountain")
                # Assert
                self.assertIs(result, expected)

    def test_TC_M_020_can_overcome_returns_bool(self):
        """TC-M-020: проверка известных препятствий возвращает bool, включая False."""
        for obstacle, expected in (("wall", False), ("river", True), ("tree", True), ("mountain", True)):
            with self.subTest(obstacle=obstacle):
                # Arrange
                chair = make_chair()
                before = snapshot(chair)
                # Act
                result = chair.can_overcome(obstacle)
                # Assert
                self.assertIs(type(result), bool)
                self.assertIs(result, expected)
                self.assertEqual(snapshot(chair), before)

    def test_TC_M_021_unknown_obstacle_raises(self):
        """TC-M-021: неизвестное препятствие вызывает ошибку валидации."""
        # Arrange
        chair = make_chair()
        before = snapshot(chair)
        # Act
        with self.assertRaises(ValueError) as caught:
            chair.can_overcome("rock")
        # Assert
        self.assert_error(caught.exception, ValueError, "unknown obstacle: rock")
        self.assertEqual(snapshot(chair), before)

    def test_TC_M_022_calculate_energy_matches_move_cost(self):
        """TC-M-022: формулы расхода энергии и возвращаемый тип float."""
        for terrain, expected in (("air", 6.0), ("water", 3.0)):
            with self.subTest(terrain=terrain):
                # Arrange
                chair = make_chair()
                # Act
                result = chair.calculate_energy(3, terrain)
                # Assert
                self.assertIs(type(result), float)
                self.assertAlmostEqual(result, expected, delta=1e-9)
        # Arrange
        chair = make_chair()
        before = snapshot(chair)
        # Act
        with self.assertRaises(FlyingChairCannotMoveOnGround) as caught:
            chair.calculate_energy(3, "ground")
        # Assert
        self.assert_error(caught.exception, FlyingChairCannotMoveOnGround,
                          "flying chair cannot move on ground")
        self.assertEqual(snapshot(chair), before)

    def test_TC_M_023_calculate_energy_preserves_state(self):
        """TC-M-023: расчёт не меняет состояние кресла в полёте."""
        # Arrange
        chair = make_chair()
        chair.move(5, "air")
        before = snapshot(chair)
        # Act
        result = chair.calculate_energy(30, "air")
        # Assert
        self.assertEqual(result, 60.0)
        self.assertEqual(snapshot(chair), before)

    def test_TC_M_024_calculate_energy_independent_of_battery(self):
        """TC-M-024: расчёт работает при недостаточном заряде батареи."""
        for battery in (0.0, 1.0):
            for terrain, expected in (("air", 60.0), ("water", 30.0)):
                with self.subTest(battery=battery, terrain=terrain):
                    # Arrange
                    chair = make_chair(battery=battery)
                    before = snapshot(chair)
                    # Act
                    result = chair.calculate_energy(30, terrain)
                    # Assert
                    self.assertIs(type(result), float)
                    self.assertEqual(result, expected)
                    self.assertEqual(snapshot(chair), before)

    def test_TC_M_025_recharge_adds_battery(self):
        """TC-M-025: обычная зарядка возвращает None."""
        # Arrange
        chair = make_chair(battery=20.0)
        # Act
        result = chair.recharge(50)
        # Assert
        self.assertIsNone(result)
        self.assertEqual(chair.battery, 70)

    def test_TC_M_026_recharge_caps_at_100(self):
        """TC-M-026: избыточная зарядка ограничивается максимальным значением."""
        for amount in (50, 1000):
            with self.subTest(amount=amount):
                # Arrange
                chair = make_chair(battery=50.0)
                # Act
                result = chair.recharge(amount)
                # Assert
                self.assertIsNone(result)
                self.assertEqual(chair.battery, 100)

    def test_TC_M_027_recharge_nonpositive_raises(self):
        """TC-M-027: величина зарядки должна быть положительной."""
        for amount in (0, -1):
            with self.subTest(amount=amount):
                # Arrange
                chair = make_chair(battery=20.0)
                before = snapshot(chair)
                # Act
                with self.assertRaises(ValueError) as caught:
                    chair.recharge(amount)
                # Assert
                self.assert_error(caught.exception, ValueError, "amount must be positive")
                self.assertEqual(snapshot(chair), before)

    def test_TC_M_028_recharge_preserves_position_and_flight(self):
        """TC-M-028: зарядка меняет только заряд батареи."""
        # Arrange
        chair = make_chair()
        chair.move(5, "air")
        before = snapshot(chair)
        # Act
        chair.recharge(5)
        # Assert
        self.assertEqual(snapshot(chair), before | {"battery": 95.0})

    def test_TC_M_029_status_keys_types_and_values(self):
        """TC-M-029: состояние содержит ровно восемь ключей из ТЗ."""
        # Arrange
        chair = make_chair()
        expected = dict(name="Царь", mass_kg=80.0, battery=100.0, position_km=0.0,
                        is_flying=False, vert_engine_power=82.0,
                        horizont_engine_power=50.0, max_speed_kmh=150.0)
        # Act
        status = chair.get_status()
        # Assert
        self.assertIs(type(status), dict)
        self.assertEqual(status, expected)
        for name, value in status.items():
            self.assertIs(type(value), type(expected[name]))

    def test_TC_M_030_status_is_snapshot(self):
        """TC-M-030: изменение возвращённого словаря не меняет состояние кресла."""
        # Arrange
        chair = make_chair()
        before = snapshot(chair)
        status = chair.get_status()
        # Act
        status["battery"] = 0
        status["name"] = "Другой"
        # Assert
        self.assertEqual(snapshot(chair), before)
        self.assertEqual(chair.get_status()["battery"], 100)
        self.assertEqual(chair.get_status()["name"], "Царь")

    def test_TC_M_031_invalid_string_parameter_types_raise(self):
        """TC-M-031: недопустимые типы имени, среды и препятствия."""
        for value in (1, None):
            for method, parameter in (("init", "name"), ("move", "terrain"),
                                      ("calculate_energy", "terrain"), ("can_overcome", "obstacle")):
                with self.subTest(method=method, value=value):
                    # Arrange
                    chair = make_chair()
                    before = snapshot(chair)
                    # Act
                    with self.assertRaises(TypeError) as caught:
                        if method == "init":
                            make_chair(name=value)
                        elif method == "can_overcome":
                            chair.can_overcome(value)
                        else:
                            getattr(chair, method)(1, value)
                    # Assert
                    self.assert_error(caught.exception, TypeError, f"{parameter} must be a string")
                    self.assertEqual(snapshot(chair), before)

    def test_TC_M_032_invalid_numeric_parameter_types_raise(self):
        """TC-M-032: нечисловые значения и bool отклоняются."""
        targets = [("init", parameter) for parameter in NUMERIC_PARAMETERS]
        targets += [("move", "distance_km"), ("calculate_energy", "distance_km"), ("recharge", "amount")]
        for value in ("1", None, True, False):
            for method, parameter in targets:
                with self.subTest(method=method, parameter=parameter, value=value):
                    # Arrange
                    chair = make_chair()
                    before = snapshot(chair)
                    # Act
                    with self.assertRaises(TypeError) as caught:
                        if method == "init":
                            make_chair(**{parameter: value})
                        elif method == "recharge":
                            chair.recharge(value)
                        else:
                            getattr(chair, method)(value, "air")
                    # Assert
                    self.assert_error(caught.exception, TypeError, f"{parameter} must be a number")
                    self.assertEqual(snapshot(chair), before)

    def test_TC_M_033_exception_hierarchy(self):
        """TC-M-033: иерархия доменных исключений из раздела 6.1 SPEC."""
        # Arrange
        pairs = ((CrazyVehicleError, RuntimeError), (FlyingChairError, CrazyVehicleError),
                 (BatteryEmpty, FlyingChairError), (FlyingChairCannotMoveOnGround, FlyingChairError))
        # Act
        inheritance = [issubclass(child, parent) for child, parent in pairs]
        domain_errors = [error("example") for error in (BatteryEmpty, FlyingChairCannotMoveOnGround)]
        # Assert
        self.assertTrue(all(inheritance))
        for error in domain_errors:
            self.assertIsInstance(error, FlyingChairError)
            self.assertIsInstance(error, RuntimeError)

    def test_TC_M_034_exception_messages(self):
        """TC-M-034: сообщения для каждой строки таблицы раздела 6.2 SPEC."""
        variants = [("init", {"name": ""}, (), ValueError, "name must not be empty")]
        variants += [("init", {name: 0}, (), ValueError, f"{name} must be positive")
                     for name in NUMERIC_PARAMETERS[:-1]]
        variants += [
            ("init", {"battery": 101}, (), ValueError, "battery must be between 0 and 100"),
            ("init", {"name": None}, (), TypeError, "name must be a string"),
            ("init", {"mass_kg": True}, (), TypeError, "mass_kg must be a number"),
            ("move", {}, (0, "air"), ValueError, "distance_km must be positive"),
            ("calculate_energy", {}, (1, "lava"), ValueError, "unknown terrain: lava"),
            ("can_overcome", {}, ("rock",), ValueError, "unknown obstacle: rock"),
            ("recharge", {}, (-1,), ValueError, "amount must be positive"),
            ("move", {}, (1, "ground"), FlyingChairCannotMoveOnGround, "flying chair cannot move on ground"),
        ]
        for method, overrides, args, error, message in variants:
            with self.subTest(method=method, parameters=overrides, args=args):
                # Arrange
                chair = make_chair()
                before = snapshot(chair)
                # Act
                with self.assertRaises(error) as caught:
                    if method == "init":
                        make_chair(**overrides)
                    else:
                        getattr(chair, method)(*args)
                # Assert
                self.assert_error(caught.exception, error, message)
                self.assertEqual(snapshot(chair), before)
        # Arrange
        chair = make_chair(battery=10.0)
        before = snapshot(chair)
        # Act
        with self.assertRaises(BatteryEmpty) as caught:
            chair.move(30, "air")
        # Assert
        self.assert_battery_error(caught.exception, 60, 10)
        self.assertEqual(snapshot(chair), before)

    def test_TC_M_035_validation_order_and_state(self):
        """TC-M-035: валидация входов предшествует проверкам среды и заряда."""
        for distance, terrain, error in (("1", "ground", TypeError), (0, "ground", ValueError),
                                         (1, "lava", ValueError), (1, "ground", FlyingChairCannotMoveOnGround),
                                         (0, 1, ValueError)):
            with self.subTest(distance=distance, terrain=terrain):
                # Arrange
                chair = make_chair(battery=0.0)
                before = snapshot(chair)
                # Act
                with self.assertRaises(error) as caught:
                    chair.move(distance, terrain)
                # Assert
                self.assertIs(type(caught.exception), error)
                self.assertEqual(snapshot(chair), before)
        # Arrange
        parameters = DEFAULTS | {"name": "", "mass_kg": -1}
        # Act
        with self.assertRaises(ValueError) as caught:
            FlyingChair(**parameters)
        # Assert
        self.assert_error(caught.exception, ValueError, "name must not be empty")

    def test_TC_M_036_move_empty_battery_raises(self):
        """TC-M-036: разряженная батарея запрещает движение в воздухе и воде."""
        for terrain, cost in (("air", 2), ("water", 1)):
            with self.subTest(terrain=terrain):
                # Arrange
                chair = make_chair(battery=0.0)
                before = snapshot(chair)
                # Act
                with self.assertRaises(BatteryEmpty) as caught:
                    chair.move(1, terrain)
                # Assert
                self.assert_battery_error(caught.exception, cost, 0)
                self.assertEqual(snapshot(chair), before)

    def test_TC_M_037_move_fractional_distance(self):
        """TC-M-037: дробные расстояния учитываются без округления."""
        for terrain, speed, battery in (("air", 150, 99), ("water", 75, 99.5)):
            with self.subTest(terrain=terrain):
                # Arrange
                chair = make_chair()
                # Act
                time = chair.move(0.5, terrain)
                # Assert
                self.assert_time(time, 0.5 / speed)
                self.assert_state(chair, 0.5, battery, terrain == "air")

    def test_TC_M_038_recharge_full_battery(self):
        """TC-M-038: зарядка полной батареи успешна и не превышает лимит."""
        # Arrange
        chair = make_chair()
        # Act
        result = chair.recharge(1)
        # Assert
        self.assertIsNone(result)
        self.assert_state(chair, 0, 100, False)

    def test_TC_M_039_numeric_int_and_float_accepted(self):
        """TC-M-039: оба допустимых числовых типа работают в конструкторе и методах."""
        for numeric_type in (int, float):
            for method in ("move", "calculate_energy", "recharge"):
                with self.subTest(numeric_type=numeric_type, method=method):
                    # Arrange
                    parameters = {name: numeric_type(value) for name, value in DEFAULTS.items() if name != "name"}
                    # Act
                    chair = make_chair(**parameters)
                    if method == "move":
                        result = chair.move(numeric_type(1), "air")
                    elif method == "calculate_energy":
                        result = chair.calculate_energy(numeric_type(1), "water")
                    else:
                        result = chair.recharge(numeric_type(1))
                    # Assert
                    for name, expected in parameters.items():
                        if name != "battery":
                            self.assertEqual(getattr(chair, name), expected)
                    if method == "move":
                        self.assert_time(result, 1 / 150)
                        self.assert_state(chair, 1, 98, True)
                    elif method == "calculate_energy":
                        self.assertIs(type(result), float)
                        self.assertEqual(result, 1.0)
                        self.assert_state(chair, 0, 100, False)
                    else:
                        self.assertIsNone(result)
                        self.assert_state(chair, 0, 100, False)

    def test_TC_M_040_move_switches_flight_state(self):
        """TC-M-040: смена среды обновляет is_flying."""
        for first, second in (("air", "water"), ("water", "air")):
            with self.subTest(first=first, second=second):
                # Arrange
                chair = make_chair()
                chair.move(1, first)
                # Act
                chair.move(1, second)
                # Assert
                self.assert_state(chair, 2, 97, second == "air")
