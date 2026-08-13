REPORT z_audit_update_demo.

PARAMETERS p_key TYPE char10.

START-OF-SELECTION.
  SELECT SINGLE key_field
    FROM zaudit_demo
    INTO @DATA(lv_key)
    WHERE key_field = @p_key.

  UPDATE zaudit_demo
    SET changed_on = @sy-datum
    WHERE key_field = @p_key.
