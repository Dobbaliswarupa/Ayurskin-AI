import json
import os


def load_wellness_data():
    """
    Load wellness recommendations
    from wellness.json.
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
        "wellness.json"
    )

    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Wellness database not found:\n{data_path}"
        )

    with open(
        data_path,
        "r",
        encoding="utf-8"
    ) as file:

        wellness_data = json.load(file)

    return wellness_data


def recommend_wellness(skin_type):
    """
    Generate general wellness suggestions
    based on the user's skin profile.
    """

    wellness_data = load_wellness_data()

    recommendations = []

    for item_id, item in wellness_data.items():

        suitable_for = item.get(
            "suitable_for",
            []
        )

        if skin_type in suitable_for:

            recommendations.append({
                "id": item_id,
                "name": item.get(
                    "name",
                    "Unknown"
                ),
                "category": item.get(
                    "category",
                    "General Wellness"
                ),
                "suggestion": item.get(
                    "suggestion",
                    ""
                ),
                "note": item.get(
                    "note",
                    ""
                )
            })

    return recommendations