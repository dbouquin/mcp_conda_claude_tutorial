from mcp.server.fastmcp import FastMCP
import weather
import os
import sys

mcp = FastMCP('Weather Tools')

@mcp.tools('get_weather_data')
def get_weather_data(city_name: str) -> dict:
    try:
        return weather.getWeatherData(city_name)
    except Exception as e:
        error_message = f"Error fetching weather data: {str(e)}"
        traceback.print_exc(file=sys.stdout)
        return {"error": error_message}
    
if __name__ == "__main__":
    try:
        print("Starting Weather Tools server...")
        mcp.run(transport="stdio")
    except Exception as e:
        error_message = f"Error starting MCP server: {str(e)}"
        traceback.print_exc(file=sys.stdout)
        print(error_message)
        sys.exit(1)