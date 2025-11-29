import random
from typing import List

from ..schemas import AnalyticsData, ImageData


def get_analytics(image_ids: List[ImageData]) -> List[AnalyticsData]:
    """
    Generates mock Google Ads–style analytics data for a list of image IDs.
    This simulates impressions, clicks, interactions, conversions, etc.
    and returns structured analytics objects for each image.

    Parameters:
        image_ids (List[ImageData]): The ImageData objects for the generated images

    Returns:
        List[AnalyticsData]: A list of analytics data models per image.
    """

    analytics_results = []

    for img_data in image_ids:
        img_id = img_data.id
        # realistic ranges
        impressions = random.randint(15000, 30000)
        clicks = random.randint(int(impressions * 0.015), int(impressions * 0.06))
        interactions = int(clicks * random.uniform(1.1, 1.6))
        conversions = random.randint(int(clicks * 0.05), int(clicks * 0.25))
        cost = round(random.uniform(150.0, 400.0), 2)

        # derived metrics
        ctr = clicks / impressions
        interaction_rate = interactions / impressions
        conversion_rate = conversions / impressions
        avg_cpc = cost / clicks
        cpm = cost / impressions * 1000

        value_per_conversion = round(random.uniform(25.0, 60.0), 2)
        conversion_value = round(conversions * value_per_conversion, 2)

        analytics_results.append(
            AnalyticsData(
                id=img_id,
                impressions=impressions,
                clicks=clicks,
                ctr=ctr,
                interactions=interactions,
                interaction_rate=interaction_rate,
                conversions=conversions,
                conversion_rate=conversion_rate,
                cost=cost,
                avg_cpc=avg_cpc,
                cpm=cpm,
                conversion_value=conversion_value,
                value_per_conversion=value_per_conversion,
            )
        )

    return analytics_results


if __name__ == "__main__":
    # Debug / test mode
    test_images = [
        ImageData(id="image_1", file_name="img1.jpg"),
        ImageData(id="image_2", file_name="img2.jpg"),
        ImageData(id="image_3", file_name="img3.jpg"),
        ImageData(id="image_4", file_name="img4.jpg"),
        ImageData(id="image_5", file_name="img5.jpg"),
    ]
    mock = get_analytics(test_images)
    from pprint import pprint
    pprint(mock)