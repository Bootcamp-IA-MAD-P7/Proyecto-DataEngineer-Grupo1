"""Smoke checks for the initial project harness."""


def test_package_can_be_imported() -> None:
    """The package baseline remains importable while modules are introduced."""
    import hr_pro_platform

    assert hr_pro_platform.__doc__
