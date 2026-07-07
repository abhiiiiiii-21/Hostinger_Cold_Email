TEMPLATE_MAP = {
    frozenset({"seo"}): "seo.txt",
    frozenset({"bad_ui"}): "bad_ui.txt",
    frozenset({"avg_ui"}): "avg_ui.txt",
    frozenset({"not_opening"}): "not_opening.txt",
    frozenset({"seo", "bad_ui"}): "bad_ui_seo.txt",
    frozenset({"seo", "avg_ui"}): "avg_ui_seo.txt",
    frozenset({"in_making"}): "website_in_making.txt",
}


def classify(review: str):
    review = review.lower().strip()

    issues = set()

    # SEO
    if "seo" in review:
        issues.add("seo")

    # Bad UI
    if "bad ui" in review:
        issues.add("bad_ui")

    # Average UI
    if "average ui" in review or "avg ui" in review:
        issues.add("avg_ui")

    # Website not opening
    if (
        "not opening" in review
        or "not working" in review
        or "website down" in review
        or "site down" in review
    ):
        issues.add("not_opening")

    # Website in making (coming soon)
    if (
        "coming soon" in review
        or "website in making" in review
        or "coming soon" in review
        or "making" in review
        or "under construction" in review
    ):
        issues.add("in_making")

    # Good UI (skip)
    if "good ui" in review:
        issues.add("good_ui")

    return issues


def choose_template(issues):
    """
    Returns the matching template filename.
    Returns None if no email should be sent.
    """

    # Skip good websites
    if "good_ui" in issues:
        return None

    return TEMPLATE_MAP.get(frozenset(issues))