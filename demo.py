"""Небольшая демонстрация возможностей FlyingChair."""

from pprint import pprint

from flying_chair import FlyingChair, FlyingChairCannotMoveOnGround


def main():
    chair = FlyingChair(
        name="Царь",
        mass_kg=80,
        vert_engine_power=82,
        horizont_engine_power=50,
        max_speed_kmh=150,
    )

    print("1. Кресло создано:")
    pprint(chair.get_status(), sort_dicts=False)

    flight_time = chair.move(10, "air")
    print(f"\n2. Полёт на 10 км занял {flight_time:.3f} ч.")
    print(f"   Гору можно преодолеть: {chair.can_overcome('mountain')}")
    pprint(chair.get_status(), sort_dicts=False)

    water_time = chair.move(5, "water")
    print(f"\n3. Подводный участок 5 км занял {water_time:.3f} ч.")
    print(f"   Реку можно преодолеть: {chair.can_overcome('river')}")
    pprint(chair.get_status(), sort_dicts=False)

    chair.recharge(25)
    required = chair.calculate_energy(10, "air")
    print(f"\n4. После зарядки для полёта на 10 км потребуется {required:.1f} единиц заряда.")
    chair.move(10, "air")
    pprint(chair.get_status(), sort_dicts=False)

    print("\n5. Попытка движения по земле:")
    try:
        chair.move(1, "ground")
    except FlyingChairCannotMoveOnGround as error:
        print(f"   Получено доменное исключение: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
