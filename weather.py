import requests

baseURL = "http://api.weatherapi.com/v1/current.json"
key = "75346521a8ce44fba4e2101312509106"

def getWeather(cityName):
    parameters = {
        'key': key,
        'q': cityName
    }
    response = requests.get(baseURL, params=parameters)
    return response.json()
    returnedData = {
        "CityName": cityName,
        "region": responseJson['location']['region'],
        "country": responseJson['location']['country'],
        "temperatureC": responseJson['current']['temp_c'],
        "UV": responseJson['current']['uv'],
        "precipitation": responseJson['current']['precip_mm']
    }
    return returnedData