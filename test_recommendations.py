
import unittest

from recommendations import (
    recommend_products,
    generate_skincare_routine,
)


class TestRecommendations(unittest.TestCase):

    def setUp(self):
        self.products = [
            {
                "product_id": 1,
                "product_name": "Basic Cleanser",
                "category": "Cleanser",
                "skin_type": "Normal, Dry",
                "skin_concerns": "Dryness",
                "ingredients": "Water, Glycerin",
                "price": 200,
            },
            {
                "product_id": 2,
                "product_name": "Vitamin C Serum",
                "category": "Serum",
                "skin_type": "All",
                "skin_concerns": "Dark Spots, Dullness",
                "ingredients": "Water, Ascorbic Acid",
                "price": 500,
                "usage_instructions": "Use in the evening",
            },
            {
                "product_id": 3,
                "product_name": "Daily Moisturizer",
                "category": "Moisturizer",
                "skin_type": "Normal, Dry",
                "skin_concerns": "Dryness",
                "ingredients": "Water, Glycerin",
                "price": 350,
            },
            {
                "product_id": 4,
                "product_name": "Sun Protection",
                "category": "Sunscreen",
                "skin_type": "All",
                "skin_concerns": "Uneven Skin Tone",
                "ingredients": "Water, Zinc Oxide",
                "price": 400,
            },
        ]

    def test_budget_filtering(self):
        results = recommend_products(
            self.products,
            "Normal",
            "Dryness",
            300,
        )

        names = [
            item["product"]["product_name"]
            for item in results
        ]

        self.assertIn("Basic Cleanser", names)
        self.assertNotIn("Daily Moisturizer", names)
        self.assertNotIn("Vitamin C Serum", names)

    def test_ingredient_avoidance(self):
        results = recommend_products(
            self.products,
            "Normal",
            "Dark Spots",
            1000,
            "Vitamin C",
        )

        names = [
            item["product"]["product_name"]
            for item in results
        ]

        self.assertNotIn("Vitamin C Serum", names)

    def test_unknown_ingredients_are_excluded_when_avoiding(self):
        products = [
            {
                "product_name": "Unknown Ingredients Product",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "",
                "price": 200,
            }
        ]

        results = recommend_products(
            products,
            "Normal",
            "Dryness",
            500,
            "Fragrance",
        )

        self.assertEqual(results, [])

    def test_no_matching_products(self):
        products = [
            {
                "product_name": "Basic Cleanser",
                "category": "Cleanser",
                "skin_type": "Normal, Dry",
                "skin_concerns": "Dryness",
                "ingredients": "Water, Glycerin",
                "price": 200,
            },
            {
                "product_name": "Daily Moisturizer",
                "category": "Moisturizer",
                "skin_type": "Normal, Dry",
                "skin_concerns": "Dryness",
                "ingredients": "Water, Glycerin",
                "price": 350,
            },
        ]

        results = recommend_products(
            products,
            "Oily",
            "Acne",
            1000,
        )

        self.assertEqual(results, [])

    def test_ranking_prefers_more_concern_matches(self):
        products = [
            {
                "product_name": "Cheaper One Concern",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "Water",
                "price": 200,
            },
            {
                "product_name": "More Relevant",
                "skin_type": "Normal",
                "skin_concerns": "Dryness, Dullness",
                "ingredients": "Water",
                "price": 500,
            },
        ]

        results = recommend_products(
            products,
            "Normal",
            "Dryness, Dullness",
            1000,
        )

        self.assertEqual(
            results[0]["product"]["product_name"],
            "More Relevant",
        )

    def test_invalid_prices_are_excluded(self):
        products = [
            {
                "product_name": "NaN Product",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "Water",
                "price": float("nan"),
            },
            {
                "product_name": "Infinity Product",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "Water",
                "price": float("inf"),
            },
            {
                "product_name": "Zero Price Product",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "Water",
                "price": 0,
            },
        ]

        results = recommend_products(
            products,
            "Normal",
            "Dryness",
        )

        self.assertEqual(results, [])

    def test_routine_generation(self):
        routine = generate_skincare_routine([
            {"product": self.products[0]},
            {"product": self.products[1]},
            {"product": self.products[2]},
            {"product": self.products[3]},
        ])

        self.assertIn("AM", routine)
        self.assertIn("PM", routine)

        self.assertTrue(
            any("Cleanse" in step for step in routine["AM"])
        )

        self.assertTrue(
            any("sunscreen" in step.lower() for step in routine["AM"])
        )

        self.assertTrue(
            any("serum" in step.lower() for step in routine["PM"])
        )

    def test_all_skin_types_match(self):
        products = [
            {
                "product_name": "Universal Product",
                "skin_type": "All",
                "skin_concerns": "Dryness",
                "ingredients": "Water",
                "price": 250,
            }
        ]

        results = recommend_products(
            products,
            "Sensitive",
            "Dryness",
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["skin_type_match"])

    def test_invalid_budget_returns_no_results(self):
        results = recommend_products(
            self.products,
            "Normal",
            "Dryness",
            0,
        )

        self.assertEqual(results, [])

    def test_non_numeric_budget_returns_no_results(self):
        results = recommend_products(
            self.products,
            "Normal",
            "Dryness",
            "abc",
        )

        self.assertEqual(results, [])

    def test_skin_type_variations_match(self):
        products = [
            {
                "product_name": "Oily Skin Product",
                "skin_type": "Oily Skin",
                "skin_concerns": "Acne",
                "ingredients": "Water",
                "price": 250,
            }
        ]

        results = recommend_products(
            products,
            "Oily",
            "Acne",
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["skin_type_match"])

    def test_ingredient_alias_matching(self):
        products = [
            {
                "product_name": "Niacinamide Product",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "Water, Nicotinamide",
                "price": 250,
            }
        ]

        results = recommend_products(
            products,
            "Normal",
            "Dryness",
            500,
            "Niacinamide",
        )

        self.assertEqual(results, [])

    def test_vitamin_c_alias_matching(self):
        products = [
            {
                "product_name": "Vitamin C Product",
                "skin_type": "Normal",
                "skin_concerns": "Dark Spots",
                "ingredients": "Water, Ascorbic Acid",
                "price": 250,
            }
        ]

        results = recommend_products(
            products,
            "Normal",
            "Dark Spots",
            500,
            "Vitamin C",
        )

        self.assertEqual(results, [])

    def test_fragrance_alias_matching(self):
        products = [
            {
                "product_name": "Fragranced Product",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "Water, Parfum",
                "price": 250,
            }
        ]

        results = recommend_products(
            products,
            "Normal",
            "Dryness",
            500,
            "Fragrance",
        )

        self.assertEqual(results, [])

    def test_multiple_avoided_ingredients(self):
        products = [
            {
                "product_name": "Product With Avoided Ingredients",
                "skin_type": "Normal",
                "skin_concerns": "Dryness",
                "ingredients": "Water, Parfum, Nicotinamide",
                "price": 250,
            }
        ]

        results = recommend_products(
            products,
            "Normal",
            "Dryness",
            500,
            "Fragrance, Niacinamide",
        )

        self.assertEqual(results, [])

    def test_morning_serum_placement(self):
        serum = {
            "product_name": "Morning Serum",
            "category": "Serum",
            "usage_instructions": "Apply in the morning",
        }

        routine = generate_skincare_routine([serum])

        self.assertTrue(
            any("Morning Serum" in step for step in routine["AM"])
        )

        self.assertFalse(
            any("Apply serum" in step for step in routine["PM"])
        )

    def test_serum_without_timing_instructions(self):
        serum = {
            "product_name": "Unspecified Serum",
            "category": "Serum",
        }

        routine = generate_skincare_routine([serum])

        self.assertTrue(
            any(
                "Check the product label" in step
                for step in routine["AM"]
            )
        )

        self.assertFalse(
            any("Apply serum" in step for step in routine["AM"])
        )

        self.assertFalse(
            any("Apply serum" in step for step in routine["PM"])
        )

    def test_missing_product_category_is_ignored(self):
        products = [
            {
                "product_name": "Product Without Category",
                "usage_instructions": "Use in the morning",
            }
        ]

        routine = generate_skincare_routine(products)

        self.assertIn("AM", routine)
        self.assertIn("PM", routine)

        self.assertTrue(
            any("No matching products" in step for step in routine["AM"])
        )

    def test_empty_routine_generation(self):
        routine = generate_skincare_routine([])

        self.assertTrue(routine["AM"])
        self.assertTrue(routine["PM"])

        self.assertTrue(
            any("No matching products" in step for step in routine["AM"])
        )


if __name__ == "__main__":
    unittest.main()
def test_serum_with_restricted_morning_use(self):
    serum = {
        "product_name": "Night Serum",
        "category": "Serum",
        "usage_instructions": "Do not use in the morning",
    }

    routine = generate_skincare_routine([serum])

    self.assertFalse(
        any("Apply serum" in step for step in routine["AM"])
    )

    self.assertFalse(
        any("Apply serum" in step for step in routine["PM"])
    )