from analyzer import extract_tables


def test_table_extraction_ignores_screen_and_internal_table_operations():
    source = """
REPORT z_static_analysis_test.

DATA: it_rows TYPE TABLE OF z_demo_table,
      wa_row  TYPE z_demo_table.

SELECT *
  FROM z_demo_table
  INTO TABLE @it_rows.

LOOP AT SCREEN.
  screen-input = 0.
  MODIFY SCREEN.
ENDLOOP.

MODIFY it_rows FROM wa_row INDEX 1.
INSERT wa_row INTO TABLE it_rows.

MODIFY z_demo_table FROM wa_row.
INSERT z_demo_table FROM wa_row.
DELETE FROM z_demo_table.
"""

    operations = {
        (item.operation, item.name)
        for item in extract_tables(source)
    }

    assert ("modify", "SCREEN") not in operations
    assert ("modify", "IT_ROWS") not in operations
    assert ("insert", "WA_ROW") not in operations

    assert ("select", "Z_DEMO_TABLE") in operations
    assert ("modify", "Z_DEMO_TABLE") in operations
    assert ("insert", "Z_DEMO_TABLE") in operations
    assert ("delete", "Z_DEMO_TABLE") in operations