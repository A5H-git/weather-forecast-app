import json
from datetime import date, datetime, time, timezone

import requests
import tzlocal
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from weather.wmo_codes import WMO_MAP

STATUS_OK = 200
MAX_ENTRIES = 5
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
ICON_BASE_URL = "https://openweathermap.org/img/wn"


@method_decorator(csrf_exempt, name="dispatch")
class Index(View):

    def get(self, request, *args, **kwargs) -> HttpResponse:

        context = {
            "today": date.today(),
            "current_time": datetime.now().strftime("%H:%M"),
            "forecast": "Loading...",
            "max_entries": range(MAX_ENTRIES),
        }

        return render(request, "weather/index.html", context)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Get latitude and longitude from the POST data
        body: dict = json.loads(request.body)
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        response = {
            "latitude": latitude,
            "longitude": longitude,
            "today": date.today(),
            "forecast": self.get_forecast(latitude, longitude),
        }

        return JsonResponse(response)

    def get_forecast(self, latitude, longitude) -> str:
        variables = [
            "weather_code",
            "temperature_2m",
            "precipitation",
        ]

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(variables),
            "hourly": ",".join(variables),
        }

        try:
            response = requests.get(OPEN_METEO_API, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return {"error": "Failed fetching."}
        else:
            forecast = response.json()
            hourly = forecast["hourly"]
            current = forecast["current"]

        return {
            "current": self._process_current(current),
            "hourly": self._process_hourly(hourly),
        }

    def _process_current(self, data: dict) -> dict:
        forecast = Forecast(**data)
        return forecast.as_dict()

    def _process_hourly(self, data: dict) -> dict:
        # Time is assumed to be present all the time
        # Hourly data will have up more than 5 days worth of data
        time_list = data["time"]
        curr_dt = datetime.now(timezone.utc)

        start_idx = 0

        for i, dt in enumerate(time_list):
            # ensure consistency
            dt = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)

            if dt.date() == curr_dt.date() and dt.hour == curr_dt.hour:
                start_idx = i + 1
                break

        # Find index of next time hour + 6
        forecasts: list[Forecast] = []
        for i in range(start_idx, start_idx + MAX_ENTRIES):
            forecast_data = {key: data[key][i] for key in data.keys()}
            forecast = Forecast(**forecast_data)
            forecasts.append(forecast)

        return {forecast.iso_time: forecast.as_dict() for forecast in forecasts}


class Forecast:

    def __init__(self, **kwargs) -> None:

        # Base implementation no TZ information...
        self._dt = datetime.fromisoformat(kwargs["time"]).replace(tzinfo=timezone.utc)
        self.iso_time = self._dt.isoformat()
        self.temperature = kwargs["temperature_2m"]
        self.precipitation = kwargs["precipitation"]
        self.weather_code = kwargs["weather_code"]

    def as_dict(self) -> None:

        weather_info = WMO_MAP[self.weather_code]

        out = {
            "time": self.iso_time,
            "temperature": self.temperature,
            "precipitation": self.precipitation,
            "description": weather_info.get("description", "undefined"),
            "icon_url": self.get_weather_icon(weather_info.get("icon")),
        }

        return out

    def get_weather_icon(self, icon_id: str) -> str:
        icon_id = f"{icon_id}{'d' if self.isDay() else 'n'}"
        icon_url = f"{ICON_BASE_URL}/{icon_id}@2x.png"
        return icon_url

    def isDay(self) -> bool:
        # Arbitrarily set day to be 0600-1800
        dt_local = self._dt.astimezone(tzlocal.get_localzone())
        day_start = time(6, 0)
        day_end = time(18, 0)
        return day_start <= dt_local.time() < day_end
