import streamlit as st

join_types = {
    "left":"Left Join",
    "a_left":"Left Anti-Join",
    "right":"Right Join",
    "a_right":"Right Anti-Join",
    "inner":"Inner Join",
    "a_inner":"Inner Anti-Join",
    "outer":"Outer Join"
}

operators = {
    'equals':'Equals',
    'not_equals':'Not Equals',
    'column_equals':'Column Equals',
    'column_not_equals':'Column Not Equal to',
    'greater_than':'Greater than',
    'less_than': 'Less than',
    'greater_than_equal': 'Greater than equal',
    'less_than_equal': 'Less than equal',
    'between': 'Between',
    'contains': 'Contains',
    'not_contains': 'Does not contains',
    'starts_with': 'Starts with',
    'ends_with': 'Ends with',
    'is_null': 'Is null',
    'not_null': 'Not null',
    'in_list': 'In list',
    'not_in_list': 'Not in list'
}

operator_map = {
    'equals':'==',
    'column_equals':'==',
    'column_not_equals':'!=',
    'not_equals':'!=',
    'greater_than':'>',
    'less_than':'<',
    'greater_than_equal':'>=',
    'less_than_equal':'<=',
    'between': 'Between',
    'starts_with': 'startswith',
    'ends_with': 'endswith',
    'is_null': 'isna',
    'not_null': 'notna',
}

def get_selected_sheets() -> dict:
    all_sheets = st.session_state.project['sheets']
    selected_sheet_names = st.session_state.validation['sheets']
    return { name: all_sheets.get(name) for name in selected_sheet_names }

def get_sheet_columns(sheet_name: str):
    if sheet_name in st.session_state.project['sheets']:
        return list(st.session_state.project['sheets'][sheet_name].columns)
    else:
        return []

def get_common_columns(sheet_name1: str, sheet_name2: str) -> list[str]:
    """
    Get matching column names between two sheets stored in session state.

    Args:
        sheet_name1: The name of the first sheet.
        sheet_name2: The name of the second sheet.

    Returns:
        A list of column names common to both sheets. Returns an empty list
        if no common columns are found or if either sheet name is not found
        in the session state.
    """
    sheets = st.session_state.project['sheets']
    
    if sheet_name1 in sheets and sheet_name2 in sheets:
        cols1 = set(sheets[sheet_name1].columns)
        cols2 = set(sheets[sheet_name2].columns)
        return list(cols1 & cols2)
    else:
        return []

def print_matching_columns(join:dict):
    """
    Retrieves common columns between two tables specified in the 'join' dictionary
    and displays them in the Streamlit app.

    If no common columns are found, a warning message is displayed.

    Args:
        join: A dictionary expected to contain 'left_table' and 'right_table' keys,
              whose values are the names of the tables to compare.
    """
    if 'left_table' not in join or 'right_table' not in join:
        st.error("Error: 'join' dictionary must contain 'left_table' and 'right_table' keys.")
        return
    
    matching_columns = get_common_columns(join['left_table'], join['right_table'])
    if not matching_columns:
        st.warning('There are no matching columns found in both tables')
    else:
        formatted_columns  = ", ".join(item.strip() for item in matching_columns)
        st.write(f"**Matching columns includes:** {formatted_columns }")
        