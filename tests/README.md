# Тесты FlyingChair

Запуск из корня проекта:

```powershell
python -m unittest discover -s tests -t . -v
```

`test_module.py` содержит 40 модульных тестов в AAA; `test_scenario.py` —
10 сценарных тестов в GWT. `pilot.py` содержит обёртку-пилота, которая
делегирует действия реальному креслу. ID каждого TC включён в имя
метода (`TC-M-001` → `test_TC_M_001_…`) и его docstring.
Параметризованные варианты выполняются через `subTest`.

Тесты ожидают `flying_chair.py` в корне проекта с экспортами
`FlyingChair`, `CrazyVehicleError`, `FlyingChairError`, `BatteryEmpty`
и `FlyingChairCannotMoveOnGround`. Проверки ошибок движения ожидают
конкретные доменные исключения; базовый `RuntimeError` не подходит.
Наследование от `RuntimeError` проверяется отдельно согласно SPEC 6.1.

Реализация FlyingChair пока отсутствует. До её добавления запуск выдаёт
ошибку импорта, а не успешный или пропущенный результат тестирования.
Тесты используют только стандартную библиотеку Python (Python 3.9+).
