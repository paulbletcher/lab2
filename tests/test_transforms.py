"""Regression checks for row alignment and nested credit expansion."""

import unittest

import pandas as pd

from pipeline.transform import flatten_directors, flatten_lead_actors, flatten_movie_details


class TransformTests(unittest.TestCase):
    def test_collections_preserve_duplicate_index_and_missing_values(self):
        base = dict(title="Test", release_date="2001-02-03", budget="10", revenue="30", vote_average=7, vote_count=1)
        movies = pd.DataFrame([
            dict(base, tmdb_id="1", belongs_to_collection={"id": 42, "name": "Series"}),
            dict(base, tmdb_id="2", belongs_to_collection=None),
            dict(base, tmdb_id="3", belongs_to_collection={"id": 99, "name": "Other"}),
        ], index=[8, 2, 8])
        flat = flatten_movie_details(movies)
        pd.testing.assert_index_equal(flat.index, movies.index)
        self.assertEqual(flat.tmdb_id.tolist(), ["1", "2", "3"])
        self.assertEqual(flat.collection_id.iloc[[0, 2]].tolist(), [42, 99])
        self.assertTrue(flat.loc[2, ["collection_id", "collection_name"]].isna().all())
        self.assertEqual(str(flat.collection_id.dtype), "Int64")
        self.assertTrue(flat.revenue_to_budget.eq(3).all())
        for value in (None, {}, float("nan")):
            with self.subTest(missing=value):
                movies["belongs_to_collection"] = [value] * len(movies)
                result = flatten_movie_details(movies)
                self.assertTrue(result[["collection_id", "collection_name"]].isna().all().all())
                self.assertEqual(str(result.collection_id.dtype), "Int64")

    def test_credit_ties_duplicates_and_empty_lists(self):
        credits = {
            "z": {
                "cast": [
                    {"id": 1, "name": "First", "order": 0},
                    {"id": 2, "name": "Tied", "order": 0},
                    {"id": 3, "name": "String", "order": "-1"},
                    {"id": 4, "name": "Float", "order": -1.0},
                    {"id": 5, "name": "Missing order"},
                ],
                "crew": [
                    {"id": 10, "name": "Director", "job": "Director"},
                    {"id": 11, "name": "Co-director", "job": "Director"},
                    {"id": 10, "name": "Repeated", "job": "Director"},
                    {"id": 12, "name": "Writer", "job": "Writer"},
                ],
            },
            "empty": {"cast": [], "crew": []},
            "missing": {},
            "null": {"cast": None, "crew": None},
            "a": {"cast": [{"id": 20, "name": "Another lead", "order": 1}],
                  "crew": [{"id": 10, "name": "Director", "job": "Director"}]},
        }
        self.assertEqual(flatten_lead_actors(credits).values.tolist(), [["z", 1, "First"], ["a", 20, "Another lead"]])
        self.assertEqual(flatten_directors(credits).values.tolist(), [["z", 10, "Director"], ["z", 11, "Co-director"], ["a", 10, "Director"]])
        for source in ({}, {"missing": {}}, {"empty": {"cast": [], "crew": []}}, {"null": {"cast": None, "crew": None}}):
            self.assertEqual(flatten_lead_actors(source).columns.tolist(), ["tmdb_id", "lead_actor_id", "lead_actor_name"])
            self.assertEqual(flatten_directors(source).columns.tolist(), ["tmdb_id", "director_id", "director_name"])
            self.assertTrue(flatten_lead_actors(source).empty)
            self.assertTrue(flatten_directors(source).empty)


if __name__ == "__main__":
    unittest.main()
