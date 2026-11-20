import pandas as pd


def summarize_franchises(movies):
    return (
        movies.loc[movies["collection_id"].notna()]
        .groupby("collection_id", as_index=False)
        .agg(
            collection_name=("collection_name", "first"),
            films_in_sample=("tmdb_id", "nunique"),
            films_with_ratio=("revenue_to_budget", "count"),
            median_ratio=("revenue_to_budget", "median"),
            lowest_ratio=("revenue_to_budget", "min"),
        )
    )


def analyze_licensing(movies):
    windows = {
        "all_years": movies,
        "2000_onward": movies.loc[movies["release_date"].dt.year.ge(2000)],
    }
    comparison = []
    outputs = {}

    for window, films in windows.items():
        franchise_films = films.loc[films["collection_id"].notna()]
        standalones = films.loc[films["collection_id"].isna()]
        franchises = summarize_franchises(films)

        comparison.append({
            "time_window": window,
            "franchise_films": len(franchise_films),
            "franchise_films_with_ratio": franchise_films["revenue_to_budget"].count(),
            "standalone_films": len(standalones),
            "standalone_films_with_ratio": standalones["revenue_to_budget"].count(),
            "franchise_film_median": franchise_films["revenue_to_budget"].median(),
            "standalone_median": standalones["revenue_to_budget"].median(),
            "collections_with_ratio": franchises["median_ratio"].count(),
            "franchise_equal_weight_median": franchises["median_ratio"].median(),
        })

        outputs[f"franchises_{window}"] = (
            franchises.loc[franchises["films_with_ratio"].ge(3)]
            .sort_values(
                ["median_ratio", "films_with_ratio", "collection_id"],
                ascending=[False, False, True],
            )
            .head(3)
        )

        outputs[f"standalones_{window}"] = (
            standalones.dropna(subset=["revenue_to_budget"])
            .sort_values(
                ["revenue_to_budget", "revenue", "tmdb_id"],
                ascending=[False, False, True],
            )
            .head(5)
        )

    outputs["comparison"] = pd.DataFrame(comparison)
    return outputs


def summarize_talent(films, person_id, person_name):
    return (
        films.groupby(person_id, as_index=False)
        .agg(
            **{person_name: (person_name, "first")},
            films=("tmdb_id", "nunique"),
            films_with_ratio=("revenue_to_budget", "count"),
            median_ratio=("revenue_to_budget", "median"),
            lowest_ratio=("revenue_to_budget", "min"),
        )
        .sort_values(
            ["median_ratio", "films_with_ratio", person_id],
            ascending=[False, False, True],
        )
    )