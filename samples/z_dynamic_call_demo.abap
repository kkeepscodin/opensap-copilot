REPORT z_dynamic_call_demo.

DATA lv_function_name TYPE rs38l_fnam VALUE 'Z_DEMO_RUNTIME_FUNCTION'.

START-OF-SELECTION.
  SELECT SINGLE bukrs
    FROM t001
    INTO @DATA(lv_bukrs).

  CALL FUNCTION lv_function_name.
