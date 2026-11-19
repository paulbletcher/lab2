import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

api_key = os.getenv("TMDB_API_KEY")
if not api_key:
    raise ValueError("TMDB_API_KEY is missing from .env")

ids_path = project_root / "data" / "validated" / "validated_ids.csv"
validated_ids = pd.read_csv(ids_path, dtype={"tmdb_id": str})
movie_id = validated_ids.loc[0, "tmdb_id"]

url = f"https://api.themoviedb.org/3/movie/{movie_id}"
params = {"api_key": api_key}

details_response = requests.get(url, params=params, timeout=20)
print("Movie details HTTP status:", details_response.status_code)
if details_response.status_code != 200:
    raise RuntimeError(f"Movie details request failed for ID {movie_id}")
details = details_response.json()

credits_response = requests.get(f"{url}/credits", params=params, timeout=20)
print("Credits HTTP status:", credits_response.status_code)
if credits_response.status_code != 200:
    raise RuntimeError(f"Credits request failed for ID {movie_id}")
credits = credits_response.json()

assert str(details["id"]) == str(credits["id"]) == movie_id

print("\nMovie:", details["title"])
print("Movie ID:", movie_id)
print("Details fields:", list(details))
print("Credits fields:", list(credits))
print("Genres:", details.get("genres"))
print("First cast entry:", credits["cast"][:1])
print("First crew entry:", credits["crew"][:1])