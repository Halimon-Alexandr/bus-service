from datetime import datetime, timedelta
import pytz
kiev_timezone = pytz.timezone("Europe/Kiev")
from schedule import workday, weekend, bus_arrival_times, special_holidays, holiday

class Tracking:
    def __init__(self):
        self.workday_schedule = sorted(workday)
        self.weekend_schedule = sorted(weekend)
        self.holidays_schedule = sorted(holiday)
        self.special_holidays = special_holidays
        self.bus_arrival_times = bus_arrival_times
        self.offset = 0

    def load_schedule(self):
        today = datetime.now(kiev_timezone).date()
        if today in self.special_holidays:
            return self.holidays_schedule
        weekday = today.weekday()
        is_workday = weekday < 5
        return self.workday_schedule if is_workday else self.weekend_schedule

    def generate_bus_schedule(self, bus_stop_query):
        index = 0
        skip_stops = {
            "Ощадбанк",
            "Монтажний технікум",
            "Машинобудівний завод",
            "Школа № 5",
            "Лікарня",
            "Верхня Немія",
            "Залізничний вокзал",
            "Маслозавод",
            "Автовокзал",
            "Школа № 2",
        }
        change_bus = True
        bus_schedule = self.load_schedule()
        while len(bus_schedule) != index:
            try:
                current_time = bus_schedule[index]
                for direction, offset in self.bus_arrival_times.get(bus_stop_query, {}).items():
                    departure_time = bus_schedule[index]
                    bus_number = (index % 2) + 1
                    departure_time_dt = datetime.now(kiev_timezone).replace(
                        hour=int(departure_time[:2]),
                        minute=int(departure_time[3:]),
                        second=0,
                    )
                    arrival_time = departure_time_dt + timedelta(minutes=offset)
                    if bus_stop_query in skip_stops and change_bus:
                        index += 1
                        change_bus = False
                    yield direction, bus_number, arrival_time
                index += 1
                change_bus = True
            except IndexError:
                break

    def format_time(self, time: datetime) -> str:
        return time.strftime('%H:%M')

    def get_bus_schedule(self, bus_stop_name="", current_time=None):
        if current_time is None:
            current_time = datetime.now(kiev_timezone)
        found_stops = [stop for stop in self.bus_arrival_times if bus_stop_name.lower() in stop.lower()]
        if len(found_stops) == 1:
            bus_stop_query = found_stops[0]
            schedule_info = {"bus_stop": found_stops[0]}
        elif len(found_stops) > 1:
            return {"stops": found_stops}
        else:
            raise ValueError("Зупинку не знайдено")
        
        schedule_current_busstop = list(self.generate_bus_schedule(bus_stop_query))
        schedule_current_busstop = sorted(schedule_current_busstop, key=lambda item: item[2])
        for index, (direction, bus_number, arrival_time) in enumerate(schedule_current_busstop):
            if current_time.time() <= arrival_time.time():
                next_bus_info = schedule_current_busstop[(index + self.offset) % len(schedule_current_busstop)]
                direction = next_bus_info[0]
                bus_number = next_bus_info[1]
                arrival_time = next_bus_info[2]
                time_left = arrival_time - datetime.now(kiev_timezone)
                hours_left = time_left.seconds // 3600
                minutes_left = (time_left.seconds % 3600) // 60
                schedule_info.update({
                    "direction": direction,
                    "bus_number": bus_number,
                    "arrival_time": arrival_time.strftime('%H:%M'),
                    "time_left": f"{hours_left} годин {minutes_left} хвилин" if hours_left else f"{minutes_left} хвилин",
                    "full_schedule": [(d, n, self.format_time(a)) for d, n, a in schedule_current_busstop]
                })
                break
        if schedule_info == {"bus_stop": bus_stop_query}:
            return self.get_bus_schedule(bus_stop_name=bus_stop_name, current_time=datetime.now(kiev_timezone).replace(hour=0, minute=0, second=0))
        return schedule_info
