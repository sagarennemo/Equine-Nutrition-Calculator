import pytest
import pandas as pd

def test_load_context_returns_correct_types(ctx):
    assert isinstance(ctx.macro, pd.DataFrame)
    assert isinstance(ctx.micro, pd.DataFrame)
    assert isinstance(ctx.vitamins, pd.DataFrame)
    assert isinstance(ctx.concentrates, pd.DataFrame)
    assert isinstance(ctx.energy_protein, dict)


def test_macro_has_expected_columns(ctx):
    assert "mineral" in ctx.macro.columns
    assert "calcium" in ctx.macro["mineral"].values