import os
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

def get_db_connection():
    """
    Builds the database connection string dynamically based on the environment.
    """
    env = os.getenv("ENVIRONMENT", "UNKNOWN")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    
    print(f"--- Running in {env} Environment ---")
    
    # SQLAlchemy connection string format: postgresql://user:password@host:port/dbname
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(connection_string)

def get_coordinates(city_name):
    """Fetches coordinates for a city."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]["latitude"], data["results"][0]["longitude"]
    except Exception as e:
        print(f"Geocoding error for {city_name}: {e}")
    return None, None

def extract_and_load(cities):
    """Extracts weather data and loads it into the configured database."""
    url = "https://api.open-meteo.com/v1/forecast"
    all_weather_data = []

    for city in cities:
        lat, lon = get_coordinates(city)
        if lat is None:
            continue
            
        params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        print(f"Fetching weather for {city}...")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("current_weather", {})
            data['city_name'] = city
            all_weather_data.append(data)
        except Exception as e:
            print(f"Error fetching {city}: {e}")

    if all_weather_data:
        df = pd.DataFrame(all_weather_data)
        df['ingested_at'] = datetime.now()
        
        # Load to Database
        try:
            engine = get_db_connection()
            # Write to raw_weather_data table
            df.to_sql('raw_weather_data', engine, if_exists='append', index=False)
            print("✅ Successfully loaded data into the database!")
        except Exception as e:
            print(f"❌ Database connection or load failed: {e}")
    else:
        print("No data extracted.")

if __name__ == "__main__":
    target_cities = ["Pune", "New York", "London", "Tokyo"]
    extract_and_load(target_cities)
```

### Test It Locally
Run the script in your terminal:
```bash
python extract_weather.py