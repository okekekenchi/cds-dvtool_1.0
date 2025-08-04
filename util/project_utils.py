
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
    'starts_with': 'Starts with',
    'ends_with': 'Ends with',
    'is_null': 'Is null',
    'not_null': 'Not null',
    'contains': 'Contains',
    'not_contains': 'Does not contains',
    'in_list': 'In list',
    'not_in_list': 'Not in list',
    'merge': 'Merge',
    'split': 'Split',
    'wildcard_match': 'Like',
    'wildcard_not_match': 'Not Like'
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
    'wildcard_match': 'str.match',
    'wildcard_not_match': 'str.match'
}

# def clear_sheets():
#     """Reset all sheets"""
#     st.session_state.update({
#         "config": {
#             "sheets": [],
#             "joins": [],
#             "conditions": []
#         }
#     })

