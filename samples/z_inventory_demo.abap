*&---------------------------------------------------------------------*
*& Synthetic demonstration program - no production logic or company data
*&---------------------------------------------------------------------*
REPORT z_inventory_demo.

PARAMETERS p_matnr TYPE matnr.

AT SELECTION-SCREEN.
  IF p_matnr IS INITIAL.
    MESSAGE 'Enter a material number' TYPE 'E'.
  ENDIF.

START-OF-SELECTION.
  SELECT SINGLE matnr, mtart
    FROM mara
    WHERE matnr = @p_matnr
    INTO @DATA(ls_material).

  IF sy-subrc <> 0.
    MESSAGE 'Material not found' TYPE 'I'.
    RETURN.
  ENDIF.

  CALL FUNCTION 'BAPI_GOODSMVT_CREATE'.

  IF sy-subrc = 0.
    CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'.
  ENDIF.
