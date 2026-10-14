"""10 сценариев Given / When / Then с управлением через тестового пилота."""

from tests.pilot import Pilot
from tests.support import (
    BatteryEmpty, ChairTestCase, FlyingChairCannotMoveOnGround, make_chair,
    snapshot,
)


class FlyingChairScenarioTests(ChairTestCase):
    def test_TC_S_001_mountain_flight(self):
        """TC-S-001: Облет горы."""
        # Given: полностью заряженное кресло и пилот.
        chair = make_chair()
        pilot = Pilot(chair)
        self.assert_state(chair, 0, 100, False)
        # When: пилот взлетает и направляется к горе.
        time = pilot.take_off(10)
        # Then: кресло пролетело 10 км и потратило 20 единиц батареи.
        self.assert_time(time, 10 / 150)
        self.assert_state(chair, 10, 80, True)
        # When: пилот проверяет препятствие.
        possible = pilot.check_obstacle("mountain")
        # Then: оба условия выполнены.
        self.assertIs(possible, True)
        # When: пилот пролетает гору.
        time = pilot.fly(15)
        # Then: батарея достигает порога заряда для преодоления горы.
        self.assert_time(time, 0.1)
        self.assert_state(chair, 25, 50, True)
        # When: пилот проверяет следующую гору.
        possible = pilot.check_obstacle("mountain")
        # Then: ровно 50 единиц батареи недостаточно для преодоления следующей горы.
        self.assertIs(possible, False)
        # When: пилот заряжает кресло.
        pilot.recharge(30)
        # Then: батарея зарядилась до 80 единиц.
        self.assert_state(chair, 25, 80, True)
        # When: пилот снова проверяет гору.
        possible = pilot.check_obstacle("mountain")
        # Then: теперь гору можно преодолеть.
        self.assertIs(possible, True)
        # When: пилот пролетает вторую гору.
        time = pilot.fly(10)
        # Then: финальная позиция: проверка времени и заряда.
        self.assert_time(time, 10 / 150)
        self.assert_state(chair, 35, 60, True)

    def test_TC_S_002_underwater_and_wall(self):
        """TC-S-002: Подводный маршрут и перелёт через стену."""
        # Given
        chair = make_chair()
        pilot = Pilot(chair)
        # When: подлет к затопленному проходу.
        time = pilot.fly(5)
        # Then
        self.assert_time(time, 5 / 150)
        self.assert_state(chair, 5, 90, True)
        # When: пилот ныряет под воду.
        time = pilot.dive(6)
        # Then: скорость передвижения в 2 раза ниже, чем по воздуху.
        self.assert_time(time, 0.08)
        self.assert_state(chair, 11, 84, False)
        # When: проверка стены под водой.
        possible = pilot.check_obstacle("wall")
        # Then
        self.assertIs(possible, False)
        # When: возвращение в воздух.
        time = pilot.take_off(1)
        # Then
        self.assert_time(time, 1 / 150)
        self.assert_state(chair, 12, 82, True)
        # When: проверка стены в полёте.
        possible = pilot.check_obstacle("wall")
        # Then
        self.assertIs(possible, True)
        # When: пролет через стену.
        time = pilot.fly(3)
        # Then
        self.assert_time(time, 0.02)
        self.assert_state(chair, 15, 76, True)

    def test_TC_S_003_battery_recovery(self):
        """TC-S-003: Разряд батареи и продолжение полёта после зарядки."""
        # Given
        chair = make_chair(battery=20.0)
        pilot = Pilot(chair)
        # When: использование остатка заряда для полёта на 10 км.
        time = pilot.fly(10)
        # Then
        self.assert_time(time, 10 / 150)
        self.assert_state(chair, 10, 0, True)
        before = snapshot(chair)
        # When: попытка пролететь ещё.
        with self.assertRaises(BatteryEmpty) as caught:
            pilot.fly(1)
        # Then: доменное исключение возникает без изменения состояния.
        self.assert_battery_error(caught.exception, 2, 0)
        self.assertEqual(snapshot(chair), before)
        # When: зарядка сверх максимальной емкости.
        pilot.recharge(150)
        # Then
        self.assert_state(chair, 10, 100, True)
        before = snapshot(chair)
        # When: проверка возможности преодолеть следующий этап.
        required = pilot.estimate_energy(30, "air")
        # Then
        self.assertEqual(required, 60)
        self.assertEqual(snapshot(chair), before)
        # When: полет по следующему маршруту.
        time = pilot.fly(30)
        # Then
        self.assert_time(time, 0.2)
        self.assert_state(chair, 40, 40, True)
        # When: запрос финального состояния.
        status = pilot.status()
        # Then
        self.assertEqual(status, dict(name="Царь", battery=40.0, position_km=40.0,
                                     is_flying=True, vert_engine_power=82.0, horizont_engine_power=50.0))

    def test_TC_S_004_accumulated_route(self):
        """TC-S-004: накопление расстояния и смена среды на последовательных участках."""
        # Given
        chair = make_chair()
        pilot = Pilot(chair)
        steps = ((pilot.fly, 2, 2, 96, True, 150),
                 (pilot.fly, 3, 5, 90, True, 150),
                 (pilot.dive, 4, 9, 86, False, 75),
                 (pilot.fly, 1, 10, 84, True, 150))
        for action, distance, position, battery, flying, speed in steps:
            with self.subTest(position=position):
                # When: пилот проходит следующий участок маршрута.
                time = action(distance)
                # Then: расстояние и заряд учитывают все пройденные участки.
                self.assert_time(time, distance / speed)
                self.assert_state(chair, position, battery, flying)
        # When
        status = pilot.status()
        # Then
        self.assertEqual(status["position_km"], 10)
        self.assertEqual(status["battery"], 84)
        self.assertIs(status["is_flying"], True)

    def test_TC_S_005_river_and_medium(self):
        """TC-S-005: возможность преодолеть реку зависит от среды и заряда."""
        # Given
        chair = make_chair(battery=21.0)
        pilot = Pilot(chair)
        # When
        possible = pilot.check_obstacle("river")
        # Then
        self.assertIs(possible, True)
        # When
        pilot.dive(1)
        # Then
        self.assert_state(chair, 1, 20, False)
        # When
        possible = pilot.check_obstacle("river")
        # Then: нахождения в воде достаточно при заряде 20.
        self.assertIs(possible, True)
        # When
        pilot.fly(1)
        # Then
        self.assert_state(chair, 2, 18, True)
        # When
        possible = pilot.check_obstacle("river")
        # Then: низкий заряд вне воды не позволяет преодолеть реку.
        self.assertIs(possible, False)
        # When
        pilot.recharge(3)
        # Then
        self.assert_state(chair, 2, 21, True)
        # When
        possible = pilot.check_obstacle("river")
        # Then
        self.assertIs(possible, True)

    def test_TC_S_006_insufficient_charge_and_retry(self):
        """TC-S-006: расчёт расхода, отказ полёта, подзарядка и повторная попытка."""
        # Given
        chair = make_chair(battery=5.0)
        pilot = Pilot(chair)
        before = snapshot(chair)
        # When
        required = pilot.estimate_energy(3, "air")
        # Then
        self.assertEqual(required, 6)
        self.assertEqual(snapshot(chair), before)
        # When
        with self.assertRaises(BatteryEmpty) as caught:
            pilot.fly(3)
        # Then
        self.assert_battery_error(caught.exception, 6, 5)
        self.assertEqual(snapshot(chair), before)
        # When
        pilot.recharge(1)
        # Then
        self.assert_state(chair, 0, 6, False)
        # When
        time = pilot.fly(3)
        # Then
        self.assert_time(time, 3 / 150)
        self.assert_state(chair, 3, 0, True)
        # When
        status = pilot.status()
        # Then
        self.assertEqual(status["battery"], 0)
        self.assertEqual(status["position_km"], 3)
        self.assertIs(status["is_flying"], True)

    def test_TC_S_007_ground_error_and_continuation(self):
        """TC-S-007: отказ движения по земле сохраняет полёт и позволяет продолжить маршрут."""
        # Given
        chair = make_chair()
        pilot = Pilot(chair)
        # When
        pilot.fly(2)
        # Then
        self.assert_state(chair, 2, 96, True)
        before = snapshot(chair)
        # When
        with self.assertRaises(FlyingChairCannotMoveOnGround) as caught:
            pilot.travel_on_ground(1)
        # Then
        self.assert_error(caught.exception, FlyingChairCannotMoveOnGround,
                          "flying chair cannot move on ground")
        self.assertEqual(snapshot(chair), before)
        # When
        possible = pilot.check_obstacle("wall")
        # Then
        self.assertIs(possible, True)
        # When
        pilot.dive(2)
        # Then
        self.assert_state(chair, 4, 94, False)
        # When
        status = pilot.status()
        # Then
        self.assertEqual(status["position_km"], 4)
        self.assertEqual(status["battery"], 94)
        self.assertIs(status["is_flying"], False)

    def test_TC_S_008_engine_power_limits(self):
        """TC-S-008: зарядка не компенсирует недостаточную мощность вертикального двигателя."""
        # Given
        chair = make_chair(mass_kg=1.0, vert_engine_power=2.1, battery=51.0)
        pilot = Pilot(chair)
        # When
        tree = pilot.check_obstacle("tree")
        mountain = pilot.check_obstacle("mountain")
        # Then
        self.assertIs(tree, True)
        self.assertIs(mountain, False)
        # When
        pilot.fly(1)
        # Then
        self.assert_state(chair, 1, 49, True)
        # When
        pilot.recharge(51)
        # Then
        self.assert_state(chair, 1, 100, True)
        # When
        tree = pilot.check_obstacle("tree")
        mountain = pilot.check_obstacle("mountain")
        # Then: гору по-прежнему нельзя преодолеть даже при полном заряде.
        self.assertIs(tree, True)
        self.assertIs(mountain, False)

    def test_TC_S_009_planning_and_status_snapshot(self):
        """TC-S-009: планирование не меняет состояние, старый снимок сохраняет значения."""
        # Given
        chair = make_chair(battery=40.0)
        pilot = Pilot(chair)
        before = snapshot(chair)
        # When
        old_status = pilot.status()
        air_cost = pilot.estimate_energy(10, "air")
        water_cost = pilot.estimate_energy(5, "water")
        # Then
        self.assertEqual(air_cost, 20)
        self.assertEqual(water_cost, 5)
        self.assertEqual(snapshot(chair), before)
        # When
        pilot.fly(10)
        # Then
        self.assert_state(chair, 10, 20, True)
        # When
        pilot.dive(5)
        # Then
        self.assert_state(chair, 15, 15, False)
        # When
        new_status = pilot.status()
        # Then
        self.assertEqual(old_status, dict(name="Царь", battery=40.0, position_km=0.0,
                                         is_flying=False, vert_engine_power=82.0, horizont_engine_power=50.0))
        self.assertEqual(new_status, old_status | {"battery": 15.0, "position_km": 15.0})
        self.assertIsNot(new_status, old_status)

    def test_TC_S_010_validation_errors_and_continuation(self):
        """TC-S-010: после неверных команд можно продолжить маршрут."""
        # Given
        chair = make_chair()
        pilot = Pilot(chair)
        # When
        pilot.fly(1)
        # Then
        self.assert_state(chair, 1, 98, True)
        before = snapshot(chair)
        commands = ((pilot.dive, 0, "distance_km must be positive"),
                    (pilot.check_obstacle, "rock", "unknown obstacle: rock"),
                    (pilot.recharge, -1, "amount must be positive"))
        for action, argument, message in commands:
            with self.subTest(command=action.__name__):
                # When: пилот подаёт неверную команду.
                with self.assertRaises(ValueError) as caught:
                    action(argument)
                # Then: проверка параметров вызывает ошибку, не меняя состояние полёта.
                self.assert_error(caught.exception, ValueError, message)
                self.assertEqual(snapshot(chair), before)
        # When: пилот продолжает маршрут корректной командой движения под водой.
        pilot.dive(2)
        # Then
        self.assert_state(chair, 3, 96, False)
        # When
        status = pilot.status()
        # Then
        self.assertEqual(status["position_km"], 3)
        self.assertEqual(status["battery"], 96)
        self.assertIs(status["is_flying"], False)
