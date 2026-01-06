from datetime import date

from fastapi.exceptions import HTTPException

from src.models import Item


def depreciate_price(item: Item, date_for_calculation: date) -> float:
    """
    Calculates the depreciated price of an item.

    Parameters
    ----------
    item : Item
        The item to depreciate.
    date_for_calculation : date
        The date for which to calculate the value.

    Returns
    -------
    float
        The depreciated price.

    Raises
    ------
    HTTPException
        If the calculation date is before the purchase date.
    """
    if date_for_calculation < item.purchase_date:
        raise HTTPException(
            status_code=400,
            detail="Date of depreciation cannot be before date of purchase",
        )
    days_passed = (date_for_calculation - item.purchase_date).days
    depreciation_factor = (1 - item.yearly_depreciation) ** (days_passed / 365)
    depreciated_price: float = item.initial_value * depreciation_factor

    if item.minimum_value is not None and depreciated_price < item.minimum_value:
        depreciated_price = item.minimum_value

    if (
        item.minimum_value_pct is not None
        and depreciated_price / item.initial_value < item.minimum_value_pct
    ):
        depreciated_price = item.initial_value * item.minimum_value_pct

    return depreciated_price
