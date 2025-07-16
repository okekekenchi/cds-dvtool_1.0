import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

# Reload util and components before importing anything from them
reload_package("util")
reload_package("utils")
reload_package("enums")
reload_package("components")

import pandas as pd
import streamlit as st
from utils import alert
from util.project_utils import operator_map, operators
from components.list_source import set_list_source_string, get_list_from_selected_source
from util.project_utils import get_selected_sheets


def perform_joins(joins) -> pd.DataFrame:
    """
    Performs a sequence of Pandas DataFrame joins based on a list of join specifications.

    Args:
        joins: A list of dictionaries, where each dictionary defines a join operation.
               Each join dict is expected to have:
               - 'left_table': str (name of the left table/DataFrame)
               - 'right_table': str (name of the right table/DataFrame)
               - 'join_type': str (e.g., 'inner', 'left', 'right', 'outer')
               - 'on_cols': list of dicts, each with 'left_column' and 'right_column'

    Returns:
        A pandas DataFrame representing the result of the chained joins, or None
        if no joins are specified, an invalid join definition is found,
        or a required sheet is missing.
    """
    result = pd.DataFrame
    selected_sheets = get_selected_sheets()
    
    for i, join in enumerate(joins):
        # st.session_state.update.validation['joins'] = []
        # st.session_state.validation['joins']
        if join["left_table"] and join["right_table"] and "on_cols" in join:
            left_df = result if not result.empty and join['left_table'] == result.name else selected_sheets[join["left_table"]]
            right_df = selected_sheets[join["right_table"]]
            how = join["join_type"]
            is_anti_join = join["join_type"][:2] == "a_"
            
            left_on = [ col["left_column"] for col in join["on_cols"] ]
            right_on = [ col["right_column"] for col in join["on_cols"] ]
            
            if len(right_on) >= 2:
                cleaned_right_df = right_df[[right_on[0], right_on[1]]].drop_duplicates()
            else:
                # Handle the case where there's only 1 column
                cleaned_right_df = right_df[[right_on[0]]].drop_duplicates()
    
    

            if left_on and right_on:
                try:
                    result = pd.merge(left_df,
                                    cleaned_right_df,
                                    left_on=left_on,
                                    right_on=right_on,
                                    how=(join["join_type"]).replace("a_", ""),
                                    indicator=is_anti_join
                                    )
                    
                    if is_anti_join:
                        result = result.query('_merge == "left_only"').drop('_merge', axis=1)
                        
                except Exception as e:
                    e
                    st.error(f"An error occurred during join {i+1} ('{join['left_table']}' {how} '{join['right_table']}'): {e}")
                    return pd.DataFrame
            else:
                return pd.DataFrame
        else:
            return pd.DataFrame
    return result


def get_joined_sheets() -> pd.DataFrame:
    joins = st.session_state.validation['joins']
    first_sheet= next(iter(get_selected_sheets().values()))
    return perform_joins(joins) if joins else first_sheet

  
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
    if pd.api.types.is_numeric_dtype(df[column]):
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

    if not conditions:
        return df
    
    try:
        query_parts = []
        for cond in conditions:
            # Build the condition string (e.g., "age > 30")
            condition_str = build_condition(df, cond)
            if condition_str:  # Skip empty conditions
                query_parts.append(condition_str)
                
                # Add the logic operator (And/Or) if it exists and there are more conditions
                if 'logic' in cond and len(query_parts) > 1:
                    logic_op = ' & ' if cond['logic'].lower() == 'and' else ' | '
                    query_parts.append(logic_op)
        
        # Join all parts and remove trailing operators
        query_str = ''.join(query_parts).rstrip(' &|')
        
        if not query_str:  # No valid conditions
            return df
            
        return df.query(query_str)
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return df

def execute_query():
    st.session_state.joined_df = get_joined_sheets()
    st.session_state.queried_df = st.session_state.joined_df
    
    if st.session_state.validation['conditions'] and not st.session_state.joined_df.empty:
        st.session_state.queried_df = apply_query_conditions(st.session_state.validation['conditions'])


def on_list_type_changed():
    if st.session_state.get("list_type") == "others":
        set_list_source_string()
    
def remove_condition(index):
    """Remove a condition from the list"""
    st.session_state.validation['conditions'].pop(index)

def clear_conditions():
    """Reset all conditions"""
    st.session_state.validation['conditions'] = []
    
@st.dialog('List')
def preview_list_from_selected_source(list_source):
    st.dataframe(get_list_from_selected_source(list_source))
        
def build_query():
    col1, col2, col3, col4 = st.columns([3, 3, 3, 3]) # Add new query condition
    new = {}
    new['value_2'] = None
    list_type = None
    value_1_is_required = True
    
    with col1:
        joined_df = get_joined_sheets()
        new['column'] = st.selectbox("Column *", key="new_column",
                                     options=([] if joined_df.empty else joined_df.columns))
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
                    new['value_2'] = st.text_input("Character", key="nv_list_character")
                else:
                    st.warning('No list source selected.')
            
            with character_placeholder.container():
                new['column_char'] = st.text_input("Character", key="nv_char")
                
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
            
            if new not in st.session_state.validation['conditions']:
                st.session_state.validation['conditions'].append(new)
                st.rerun()
            else:
                alert("You have already this condition")
                        
    with col2:
        st.button("", on_click=clear_conditions, icon=":material/refresh:",
                  help="Clear all conditions", key="clear_conditions")
    
    if st.session_state.validation['conditions']:
        columns = ['Column', 'Character', 'Operator', 'Value', 'Logic', 'Action']
        
        for i, col in enumerate(st.columns([0.23, 0.2, 0.2, 0.2, 0.15, 0.07])):
            with col:
                st.write(f"**{columns[i]}**")
        
        for i, cond in enumerate(st.session_state.validation['conditions']):
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
                
    execute_query()

