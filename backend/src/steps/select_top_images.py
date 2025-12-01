import logging

try:
    from ..schemas import AnalyticsData, ImageData
except ImportError:  # pragma: no cover
    from schemas import AnalyticsData, ImageData  # type: ignore


logger = logging.getLogger(__name__)


def select_top_images(
    analytics_data: list[AnalyticsData] | list[ImageData],
    top_n: int = 2,
) -> list[AnalyticsData]:
    """
    Selects the top N images based on analytics data.
    
    Uses a composite scoring system that considers:
    - Interactions (count and rate)
    - Conversion value and rate
    - Overall engagement metrics
    
    Parameters:
        analytics_data: List of AnalyticsData objects, or ImageData objects with analytics
        top_n: Number of top images to return (default: 2)
    
    Returns:
        List of top N AnalyticsData objects, sorted by score (highest first)
    """
    # Extract AnalyticsData from input
    analytics_list: list[AnalyticsData] = []

    for item in analytics_data:
        if isinstance(item, ImageData):
            if item.analytics is None:
                raise ValueError(f"ImageData with id '{item.id}' has no analytics data")
            analytics_list.append(item.analytics)
        elif isinstance(item, AnalyticsData):
            analytics_list.append(item)
        else:
            raise TypeError(f"Unsupported type: {type(item)}")

    if len(analytics_list) < top_n:
        raise ValueError(
            f"Not enough images to select top {top_n}. "
            f"Only {len(analytics_list)} images provided."
        )

    # Calculate composite score for each image
    logger.info("Scoring %s images to select top %s", len(analytics_list), top_n)
    scored_images = []

    for analytics in analytics_list:
        # Normalize metrics to create a composite score
        # Weight different factors:
        # - Interactions: 40% (both count and rate)
        # - Conversion value: 30%
        # - Conversion rate: 20%
        # - CTR: 10%

        # Normalize interactions (higher is better)
        # Using interaction_rate as primary, with interactions count as secondary
        interaction_score = (
            analytics.interaction_rate * 0.6 +
            (analytics.interactions / 1000.0) * 0.4  # Normalize interactions count
        )

        # Normalize conversion value (higher is better)
        # Assuming typical range 0-1000, normalize to 0-1
        conversion_value_score = min(analytics.conversion_value / 1000.0, 1.0)

        # Conversion rate (already a rate, 0-1)
        conversion_rate_score = analytics.conversion_rate

        # CTR (already a rate, typically 0-0.1, normalize to 0-1)
        ctr_score = min(analytics.ctr * 10, 1.0)  # Scale CTR to 0-1 range

        # Composite score
        composite_score = (
            interaction_score * 0.4 +
            conversion_value_score * 0.3 +
            conversion_rate_score * 0.2 +
            ctr_score * 0.1
        )

        scored_images.append((composite_score, analytics))

    # Sort by score (highest first) and return top N
    scored_images.sort(key=lambda x: x[0], reverse=True)

    top_images = [analytics for _, analytics in scored_images[:top_n]]
    logger.info("Selected top image IDs: %s", [a.id for a in top_images])

    return top_images


if __name__ == "__main__":
    # Test mode
    from .get_analytics import get_analytics

    test_images = [
        ImageData(id="image_1", file_name="img1.jpg"),
        ImageData(id="image_2", file_name="img2.jpg"),
        ImageData(id="image_3", file_name="img3.jpg"),
        ImageData(id="image_4", file_name="img4.jpg"),
        ImageData(id="image_5", file_name="img5.jpg"),
    ]

    # Get analytics for all images
    analytics = get_analytics(test_images)

    # Select top 2
    top_2 = select_top_images(analytics, top_n=2)

    print("Top 2 images selected:")
    for i, img_analytics in enumerate(top_2, 1):
        print(f"\n{i}. Image ID: {img_analytics.id}")
        print(f"   Interactions: {img_analytics.interactions}")
        print(f"   Interaction Rate: {img_analytics.interaction_rate:.4f}")
        print(f"   Conversion Value: ${img_analytics.conversion_value:.2f}")
        print(f"   Conversion Rate: {img_analytics.conversion_rate:.4f}")
        print(f"   CTR: {img_analytics.ctr:.4f}")

