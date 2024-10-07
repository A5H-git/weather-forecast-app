document.addEventListener('DOMContentLoaded', function () {
    getLocation();
});

function getLocation() {
    navigator.geolocation.getCurrentPosition(postToServer);
}

function processCurrentData(data) {
    document.querySelector("#current-icon").src = data.icon_url;
    document.querySelector("#current-forecast").innerHTML = data.description;
    document.querySelector("#current-temperature").innerHTML = `${data.temperature}°C`;
    document.querySelector("#current-rain-mm").innerHTML = `${data.precipitation}mm`;
}

function processHourlyData(data) {
    let i = 0;

    for (let time in data) {  
        const hour = data[time];

        document.querySelector(`#hourly-icon-${i}`).src = hour.icon_url;
        document.querySelector(`#hourly-forecast-${i}`).innerHTML = hour.description;
        document.querySelector(`#hourly-temperature-${i}`).innerHTML = `${hour.temperature.toFixed(1)}°C`;
        document.querySelector(`#hourly-rain-mm-${i}`).innerHTML = `${hour.precipitation}mm`;

        // set time
        time = new Date(time);
        const HH = time.getHours().toString().padStart(2, '0');
        const MM = time.getMinutes().toString().padStart(2, '0');
        document.querySelector(`#hourly-time-${i}`).innerHTML = `${HH}:${MM}`;

        i++; 

        if (i > data.max_time) {
            break;
        }
    }
}

function postToServer(position) {
    const lat = position.coords.latitude;
    const long = position.coords.longitude;

    document.querySelector("#location").innerHTML = `${lat.toFixed(0)}°, ${long.toFixed(0)}°`;

    axios.post("/", {
        latitude: lat,
        longitude: long,
    }).then(response => {
        const data = response.data;
        console.log(data)
        processCurrentData(data.forecast.current);
        console.log("Here");
        processHourlyData(data.forecast.hourly);
        console.log("Done");
    }).catch(error => {
        console.error("Error getting data.")
    });
}