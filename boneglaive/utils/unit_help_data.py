"""Unit help data accessor — shared by text and graphical UI layers."""

def get_unit_help_data():
    """Load unit help data without requiring a UI component instance."""
    from boneglaive.ui.ui_components import UnitHelpComponent

    class _Stub:
        pass

    component = UnitHelpComponent(_Stub(), _Stub())
    return component.unit_help_data
