import json
import os


def load_ingredients():
    """
    Load traditional skincare ingredients
    from the JSON database.
    """

    current_file = os.path.dirname(
        os.path.abspath(__file__)
    )

    project_folder = os.path.dirname(
        current_file
    )

    data_path = os.path.join(
        project_folder,
        "data",
        "ingredients.json"
    )

    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Ingredients database not found:\n{data_path}"
        )

    with open(
        data_path,
        "r",
        encoding="utf-8"
    ) as file:

        ingredients = json.load(file)

    return ingredients


def recommend_traditional_skincare(skin_type):
    """
    Recommend traditional skincare ingredients
    based on estimated skin type.
    """

    ingredients = load_ingredients()

    recommendations = []

    for ingredient_id, ingredient in ingredients.items():

        suitable_for = ingredient.get(
            "suitable_for",
            []
        )

        if skin_type in suitable_for:

            recommendations.append({

                "id": ingredient_id,

                "name": ingredient.get(
                    "name",
                    "Unknown"
                ),

                "image": ingredient.get(
                    "image",
                    ""
                ),

                "category": ingredient.get(
                    "category",
                    "General skincare"
                ),

                "suitable_for": ingredient.get(
                    "suitable_for",
                    []
                ),

                "traditional_use": ingredient.get(
                    "traditional_use",
                    ""
                ),

                "benefits": ingredient.get(
                    "benefits",
                    []
                ),

                "caution": ingredient.get(
                    "caution",
                    ""
                )
            })

    return recommendations