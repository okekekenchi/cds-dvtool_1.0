import pandas as pd
import streamlit as st
from utils import alert
from util.project_utils import operator_map, operators
from components.list_source import set_list_source_string, get_list_from_selected_source

def detect_exact_dtype(series: pd.Series) -> str:
    """
    Detect the exact data type of a pandas Series, especially for object columns.
    
    Args:
        series: pandas Series to analyze
        
    Returns:
        str: One of 'string', 'integer', 'float', 'datetime', 'boolean', 'mixed', or 'unknown'
    """
    if not pd.api.types.is_object_dtype(series):
        return str(series.dtype)
    
    # Check for datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'datetime'
    
    # Try converting to different types to detect actual content
    try:
        # Check if it's numeric
        numeric = pd.to_numeric(series, errors='raise')
        if all(numeric == numeric.astype(int)):
            return 'integer'
        return 'float'
    except:
        pass
    
    # Check for boolean
    if pd.api.types.is_bool_dtype(series):
        return 'boolean'
    
    # Check if it's string (after trying other types)
    if pd.api.types.is_string_dtype(series):
        return 'string'
    
    # Check for mixed types
    unique_types = set(type(x) for x in series.dropna().head(100))
    if len(unique_types) > 1:
        return 'mixed'
    
    return 'unknown'

def perform_joins(sheets: dict,  joins: list[dict]) -> pd.DataFrame:
    """
    Performs a sequence of Pandas DataFrame joins based on join specifications.

    Args:
        sheets: Dictionary of {sheet_name: DataFrame} containing all available sheets
        joins: List of join specifications where each join contains:
            - left_table: Name of the left table
            - right_table: Name of the right table
            - join_type: Type of join ('inner', 'left', 'right', 'outer', 'a_inner', etc.)
            - on_cols: List of dicts with 'left_column' and 'right_column' pairs

    Returns:
        pd.DataFrame: Result of the joins, or empty DataFrame if:
            - No joins specified
            - Invalid join definition
            - Missing required sheet
            - Join column errors

    Raises:
        ValueError: If input validation fails
    """
    
    def convert_column_types(left_df, right_df, left_col, right_col):
        """Convert join columns to compatible types"""
        left_type = detect_exact_dtype(left_df[left_col])
        right_type = detect_exact_dtype(right_df[right_col])
        
        compatible_types = {
            'integer': {'integer', 'float'},
            'float': {'integer', 'float'},
            'string': {'string'},
            'datetime': {'datetime'}
        }
        
        try:
            if left_type in compatible_types and right_type in compatible_types[left_type]:
                return left_df, right_df
            else:
                left_df[left_col] = left_df[left_col].astype(str)
                right_df[right_col] = right_df[right_col].astype(str)
        except Exception as e:
            st.error(f"Could not convert {left_col} and {right_col} to compatible types: {str(e)}")
            return None, None
            
        return left_df, right_df
    
    result = pd.DataFrame
    
    for i, join in enumerate(joins):
        # Validate join specification
        required_keys = {'left_table', 'right_table', 'join_type', 'on_cols'}
        if not all(k in join for k in required_keys):
            st.error(f"Missing required fields in join specification")
            return pd.DataFrame()
        
        on_cols = join['on_cols']
        join_type = join['join_type']
        left_table = join['left_table']
        right_table = join['right_table']
        is_anti_join = join_type[:2] == "a_"

        if not len(on_cols):
            st.error(f"Missing required conditions in join specification")
            return pd.DataFrame
        
        left_df = result if not result.empty and left_table == getattr(result, 'name', None) else sheets.get(left_table)
        right_df = sheets.get(right_table)
        
        if left_df is None or right_df is None:
            st.error(f"Missing table: {left_table if left_df is None else right_table}")
            return pd.DataFrame()
        
        left_on = []
        right_on = []
        
        for col in on_cols:
            if col["left_column"] in left_df.columns:
                left_on.append(col["left_column"])
            else:
                st.error(f"Column **{col['left_column']}** not found in resulting joined entity")
                return pd.DataFrame()
                
            if col["right_column"] in right_df.columns:
                right_on.append(col["right_column"])
            else:
                st.error(f"Column **{col['right_column']}** not found in resulting joined entity")
                return pd.DataFrame()
            
            # Convert types if needed
            left_df, right_df = convert_column_types(left_df, right_df, col["left_column"], col["right_column"])
            if left_df is None or right_df is None:
                    return pd.DataFrame()
                
        if len(right_on) >= 2:
            cleaned_right_df = right_df[[right_on[0], right_on[1]]].drop_duplicates()
        else:
            # Handle the case where there's only 1 column
            cleaned_right_df = right_df[[right_on[0]]].drop_duplicates()
        
        if left_on and right_on:
            try:
                result = pd.merge(left_df, cleaned_right_df,
                                left_on=left_on, right_on=right_on,
                                how=(join_type).replace("a_", ""),
                                indicator=is_anti_join
                                )
                
                if is_anti_join:
                    result = result.query('_merge == "left_only"').drop('_merge', axis=1)
                
            except KeyError as e:
                st.error(f"Join column **{str(e)}** not found in resulting joined entity")
                return pd.DataFrame
            except Exception as e:
                st.error(f"Join failed between {left_table} and {right_table}: {str(e)}")
                return pd.DataFrame
        else:
            return pd.DataFrame
    return result


def get_joined_sheets(sheets: dict) -> pd.DataFrame:
    joins = st.session_state.config['joins']
    first_sheet= next(iter(sheets.values()))
    return perform_joins(sheets, joins) if joins else first_sheet

  
def build_condition(df: pd.DataFrame, condition: dict) -> str:
    """
    Builds a pandas query condition string from a condition dictionary.

    Args:
        df: The pandas DataFrame against which the query will be executed.
            Used to infer column data types.
        condition: A dictionary defining the filter condition. Expected keys:
            - 'column': str, The name of the column to filter.
            - 'operator': str, The type of comparison (e.g., 'equals', 'contains', 'between').
            - 'value_1': str or numeric, The primary value for the comparison.
            - 'value_2': str or numeric, optional, A secondary value for operators like 'between' or positional 'contains'.

    Returns:
        A string representing the pandas query condition, or an empty string if
        the condition cannot be built (e.g., invalid operator, missing value for non-null check).
    """
    column = condition['column']
    operator = condition['operator']
    value = condition['value_1']
    value_2 = condition.get('value_2', None)
    
    try:
        column_char = int(condition['column_char']) if 'column_char' in condition else None
    except (ValueError, TypeError):
        column_char = None
    
    # --- Pre-process values based on column data type ---
    if pd.api.types.is_numeric_dtype(df[column]) and operator not in ['in_list', 'not_in_list']:
        try:
            value = float(value) if value not in ['', None] else None
            if value_2 not in ['', None]:
                value_2 = float(value_2)
        except ValueError:
            # Handle cases where numeric conversion fails
            st.warning(f"Invalid numeric value '{value}' for column '{column}'. Skipping condition.")
            return ""
                
    elif pd.api.types.is_datetime64_any_dtype(df[column]):
        if value not in ['', None]:
            value = repr(str(value))
        if value_2 not in ['', None]:
            value_2 = repr(str(value_2))
    else:
        value = repr(str(value)) if value not in ['', None] else None
        value_2 = repr(str(value_2)) if value_2 not in ['', None] else None
    
    if operator in ['equals', 'not_equals', 'greater_than', 'less_than', 'greater_than_equal', 'less_than_equal']:
        return f"`{column}` {operator_map[operator]} {value}" if value is not None else ""
    
    elif operator in ['column_equals','column_not_equals']:
        return f"`{column}` {operator_map[operator]} `{condition['value_1']}`" if value is not None else ""
    
    elif operator == 'between':
        if value == None or value_2 == None: return ""
        return f"`{column}` >= {value} & `{column}` <= {value_2}"
    
    elif operator in ['starts_with', 'ends_with']:
        return f"`{column}`.str.{operator_map[operator]}({value}, na=False)" if value is not None else ""
    
    elif operator in ['is_null', 'not_null']:
        return f"`{column}`.{operator_map[operator]}()"
    
    elif operator in ['contains', 'not_contains']:
        _not = "~" if operator == "not_contains" else ""
        if value_2 is not None: # Check if substring exists at specific position
            try:
                pos_str = str(value_2).strip("'\"")
                pos = int(pos_str)
                search_len = len(str(condition['value_1']))
                if pos < 1:
                    st.warning(f"Position cannot be negative for 'contains' operator on column '{column}'.")
                    return ""
                
                pos = pos - 1
                
                if operator == 'contains':
                    return (
                        f"`{column}`.notna() & "  # Must not be NA
                        f"`{column}`.str.len() > {pos} & " # Must be long enough
                        f"`{column}`.str.slice({pos}, {pos + search_len}).eq({value})" # Slice equals search value
                    )
                else:
                    return (
                        f"~(`{column}`.isna() | "
                        f"`{column}`.str.len() <= {pos} and "
                        f"`{column}`.str.slice({pos}, {pos + search_len}).eq({value}))"
                    )
                
            except ValueError:
                st.warning(f"Invalid position '{value_2}' for 'contains' operator on column '{column}'.")
                return ""
        else:
            return f"{_not}`{column}`.str.contains({value}, case=False, na=False)" if value is not None else ""
    
    elif operator in ['in_list', 'not_in_list']:
        if value in ['', None]:
            return ""
        
        values = get_list_from_selected_source(condition['value_1'])
        
        if values is None:
            values = [x.strip() for x in str(condition['value_1']).split(',')]
            
        try:
            if pd.api.types.is_numeric_dtype(df[column]):
                values = [float(x) for x in values]
            else:
                # Handle string columns with optional character position check
                if 'value_2' in condition and str(condition['value_2']).strip() and condition['value_2'] is not None:
                    try:
                        char_pos = int(condition['value_2'])
                        if char_pos < 1:
                            st.warning(f"Character position must be ≥ 1 (got {char_pos})")
                            char_pos = None
                        else:
                            values = [
                                str(x)[char_pos - 1] 
                                if len(str(x)) >= char_pos else None 
                                for x in values
                            ]
                            values = [x for x in values if x is not None] # Remove None values
                    except (ValueError, TypeError):
                        st.warning(f"Invalid character position '{condition['value_2']}' for column '{value}'")
                        pass # Fall back to normal string comparison
                
                values = [str(x) for x in values]
            
            _not = '~' if operator == 'not_in_list' else ''
            
            if column_char:
                return f"{_not}`{column}`.str[{column_char-1}].isin({values})"
            else:
                return f"{_not}`{column}`.isin({values})"
        except ValueError:
            st.warning(f"Invalid value in list for column '{column}'.")
            return ""
    else:
        return ""

def apply_query_conditions(conditions):
    """Apply query conditions to dataframe"""
    df = st.session_state.joined_df

    if not conditions: return df
    
    try:
        query_parts = []
        for cond in conditions:
            # Build the condition string (e.g., "age > 30")
            condition_str = build_condition(df, cond)
            if condition_str:  # Skip empty conditions
                query_parts.append(condition_str)
                
                # Add the logic operator (And/Or) if it exists and there are more conditions
                if 'logic' in cond and query_parts:
                    logic_op = ' & ' if cond['logic'].lower() == 'and' else ' | '
                    query_parts.append(logic_op)
        
        
        # Join all parts and remove trailing operators
        query_str = ''.join(query_parts).rstrip(' &|')

        if not query_str:  # No valid conditions
            return df
        
        return df.query(query_str)
    except Exception as e:
        st.write(e)
        st.error(f"Query failed: {str(e)}")
        return df

def execute_query(sheets: dict):
    st.session_state.queried_df = st.session_state.joined_df
    
    if st.session_state.config['conditions'] and not st.session_state.joined_df.empty:
        st.session_state.queried_df = apply_query_conditions(st.session_state.config['conditions'])


def on_list_type_changed():
    if st.session_state.get("list_type") == "others":
        set_list_source_string()
    
def remove_condition(index):
    """Remove a condition from the list"""
    st.session_state.config['conditions'].pop(index)

def clear_conditions():
    """Reset all conditions"""
    st.session_state.config['conditions'] = []
    
@st.dialog('List')
def preview_list_from_selected_source(list_source):
    st.dataframe(get_list_from_selected_source(list_source))
        
def build_query(sheets: dict):
    col1, col2, col3, col4 = st.columns([3, 3, 3, 3]) # Add new query condition
    new = {}
    new['value_2'] = None
    list_type = None
    value_1_is_required = True
    joined_df = st.session_state.joined_df = get_joined_sheets(sheets)
    options = ([] if joined_df.empty else joined_df.columns.to_list())
        
    with col1:
        new['column'] = st.selectbox("Column *", key="new_column", options=options)
        character_placeholder = st.empty()
        
    with col2:
        new['operator'] = st.selectbox("Operator *",
                                        options=operators.keys(),
                                        key="new_operator",
                                        format_func=lambda x: operators[x])
    with col3:
        if new['operator'] in ['is_null', 'not_null']:
            new['value_1'] = None
            value_1_is_required = False 
            
        elif new['operator'] in ['column_equals', 'column_not_equals']:
            new['value_1'] = st.selectbox("Column *", key="new_matching_column",
                                            options=([] if joined_df.empty else joined_df.columns))
            
        elif new['operator'] in ['in_list', 'not_in_list']:
            list_type = st.selectbox("List type *",
                                    options=['custom', 'others'],
                                    key="list_type",
                                    format_func=lambda x: x.replace('_',' ').capitalize(),
                                    on_change=on_list_type_changed
                                )
            
            
            if list_type == "custom":
                new['value_1'] = st.text_input("Comma-separated values *", key="nv_1")
                new['value_2'] = st.session_state.nv_list_character = None
            else:                
                if st.session_state.list_source_str:
                    new['value_1'] = st.text_input("List source *", key="nv_lsource",
                                                    value=st.session_state.list_source_str, disabled=True)
                    new['value_2'] = st.number_input("Character", key="nv_list_character", min_value=0,
                                                     step=1, max_value=100)
                else:
                    st.warning('No list source selected.')
            
            with character_placeholder.container():
                new['column_char'] = st.number_input("Character", key="nv_char", min_value=0,
                                                     step=1, max_value=100)
                
        elif new['operator'] == 'between':
            new['value_1'] = st.text_input("From value *", key="nv_2")
            new['value_2'] = st.text_input("To value *", key="nv_3")
            
        elif new['operator'] in ['contains', 'not_contains']:
            new['value_1'] = st.text_input("Value *", "", key="nv_4")
            new['value_2'] = st.text_input("Position", key="nv_5")
            
        else:
            new['value_1'] = st.text_input("Value *", key="nv_6")
            
    with col4:
        new['logic'] = st.selectbox("", options=['And', 'Or'], key="new_logic")
        
        if st.session_state.list_source_str and list_type == "others":
            st.markdown("<p style='margin-top:28px;'></p>", unsafe_allow_html=True)
            
            col_1, col_2, _ = st.columns([0.25,0.25, 0.5])
            with col_1:
                if st.button(f"", key=f"edit_list_source",icon=":material/edit:", help='Edit List Source'):
                    on_list_type_changed()
            with col_2:
                if st.button(f"", key=f"preview_list_source",icon=":material/visibility:", help="View list Source"):
                    preview_list_from_selected_source(st.session_state.list_source_str)
                    
    # Action buttons
    _, col1, col2 = st.columns([0.7,0.2,0.05])
    
    with col1:
        if st.button(f"Add", key="add_query_condition", icon=":material/add:"):            
            if (not new['column'] or not new['operator'] or not new['logic']):
                alert("Fill all required fields")
                return
            
            if not new['value_1'] and value_1_is_required:
                alert("Fill all required fields")
                return
            
            if new not in st.session_state.config['conditions']:
                st.session_state.config['conditions'].append(new)
                st.rerun()
            else:
                alert("You have already this condition")
                        
    with col2:
        st.button("", on_click=clear_conditions, icon=":material/refresh:",
                  help="Clear all conditions", key="clear_conditions")
    
    if st.session_state.config['conditions']:
        columns = ['Column', 'Character', 'Operator', 'Value', 'Logic', 'Action']
        
        for i, col in enumerate(st.columns([0.23, 0.2, 0.2, 0.2, 0.15, 0.07])):
            with col:
                st.write(f"**{columns[i]}**")
        
        for i, cond in enumerate(st.session_state.config['conditions']):
            col1, col2, col3, col4, col5, col6 = st.columns([0.23, 0.2, 0.2, 0.2, 0.15, 0.07])
            with col1:
                st.write(f"{cond['column']}")
            with col2:
                st.write(f"{cond['column_char'] if 'column_char' in cond else 'N/A'}")
            with col3:
                st.write(f"{cond['operator'].replace('_', ' ').title()}")
            with col4:
                if cond['operator'] in ['between']:
                    st.write(f"{cond['value_1']} **and** {cond['value_2']}")
                elif cond['operator'] in ['contains','not_contains'] and cond['value_2']:
                    st.write(f"{cond['value_1']} **in position** {cond['value_2']}")
                else:
                    st.write(f"{cond['value_1'] or 'N/A'}")
            with col5:
                st.write(f"{cond.get('logic', 'And')}")
            with col6:
                st.button("", icon=":material/delete:", help="Delete query condition",
                          key=f"remove_condition_{i}", on_click=remove_condition, args=(i,))
                
    execute_query(sheets)

