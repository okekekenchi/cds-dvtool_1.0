import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("services.join_service")

import re
import pandas as pd
import streamlit as st
from utils import get_model_class
from database.database import get_db
from enums.list_type import ListType
from util.project_utils import operator_map
from services.join_service import get_joined_sheets
from services.column_operation_service import run_column_operations
from models.validation_checklist import ValidationChecklist


def get_list_from_selected_source(all_sheets:dict, list_source: str,) -> list:
    parts = list_source.split('.', maxsplit=2)
    
    if len(parts) != 3:
        return None
    
    list_type, source, column = parts
    
    if list_type not in (list_type.value for list_type in ListType):
        return None
    
    if list_type == ListType.Master.value:
        with get_db() as db:
            data = get_model(source).all_df(db, columns=[column]).drop_duplicates().dropna().values.tolist()
            return [item[0] for item in data]
        
    elif list_type == ListType.Sheet.value:
        if source in all_sheets:
            all_list = all_sheets[source]
            if column in all_list:
                return all_list[column].drop_duplicates().dropna().values.tolist()
            else:
                st.warning(f'Column: {column} does not exist in sheet: {source}.')
        else:
            st.warning(f'There is no sheet: {source} in workbook.')
        
    elif list_type == ListType.Checklist.value:
        with get_db() as db:
            checklist = ValidationChecklist.find(db, source)
            return load_checklist(checklist.config, all_sheets)[column].drop_duplicates().dropna().values.tolist()
    
    return []

def get_model(table_name):
    table_class = table_name[:-1]
    return get_model_class(table_class)



def get_selected_sheets(all_sheets: dict, selected_sheet_names: list[str]) -> dict:
    return { name: all_sheets.get(name) for name in selected_sheet_names }

def load_checklist(config: dict, all_sheets:dict, get:str = "failed") -> pd.DataFrame | dict:
    """_summary_

    Args:
        config (dict):
            -sheets: All selected sheets
            -joins: Join conditions
            -conditions: query condition and column specifications
        sheets (dict): _description_

    Returns:
        pd.DataFrame: 
    """
    for sheet in config['sheets']:
        if sheet["name"] not in all_sheets.keys():
            st.warning(f"Sheet {sheet["name"]} not found")
            return pd.DataFrame()
     
    selected_sheets = run_column_operations(all_sheets, config.get('sheets', []))
    
    result = get_joined_sheets(selected_sheets, config.get('joins', []))

    result['failed_df'] = execute_query(all_sheets, result["joined_df"], config.get('conditions', []))
    
    # Create boolean mask for passed records (records NOT in failed_df)
    passed_mask = ~result["residual_df"].index.isin(result['failed_df'].index)
    result["passed_df"] = result["residual_df"][passed_mask]
    
    if get == "failed":
        return result['failed_df']
    elif get == "passed":
        return result['passed_df']
    elif get == "all":
        return result


def build_condition(all_sheets: dict, df: pd.DataFrame, condition: dict) -> str|pd.Series:
    """
    Builds a pandas query condition string from a condition dictionary.
    
    Args:
        all_sheets: All sheets uploaded
        df: The pandas DataFrame against which the query will be executed.
            Used to infer column data types.
        condition: A dictionary defining the filter condition. Expected keys:
            - 'column': str, The name of the column to filter.
            - 'column_char': int, The position of a character in column value
            - 'operator': str, The type of comparison (e.g., 'equals', 'contains', 'between').
            - 'value_1': str or numeric, The primary value for the comparison.
            - 'value_2': str or numeric, optional, A secondary value for operators like 'between' or positional 'contains, in list, column_equls'.
            
    Returns:
        A string representing the pandas query condition, or an empty string if
        the condition cannot be built (e.g., invalid operator, missing value for non-null check).
    """
    column = condition['column']
    column_char = condition.get('column_char', 0)
    operator = condition['operator']
    value = condition['value_1']
    value_2 = condition.get('value_2', None)
    
    if column not in df.columns:
        st.warning(f"Column {column} does not exist.")
        return ""
    
    try:
        column_char = int(column_char)
    except (ValueError, TypeError):
        column_char = 0
    
    if operator in ['is_null', 'not_null']:
        return f"`{column}`.{operator_map[operator]}()"
    
    if operator in ['has_parent', 'has_no_parent']:
        children = set()
        items = df[column].astype(str).str.upper().dropna().unique()
        
        for item in items:
            for alt_item in items:
                if item == alt_item or len(alt_item) >= len(item):
                    continue
                
                if item[:-2] == alt_item:
                    children.add(item)
        
        not_operator = '~' if operator == 'has_no_parent' else ''
        return f"{not_operator}`{column}`.isin({list(children)})"
    
    elif operator in ['length_equals','length_not_equals']:
        if value is None: return ""
        
        target_column = value
        if target_column not in df.columns:
            st.warning(f"Column {target_column} does not exist.")
            return ""
        
        try:
            df[target_column] = pd.to_numeric(df[target_column], errors='raise')            
        except ValueError:
            st.warning(f"Target column '{target_column}' contains non-numeric values.")
            return ""
        
        if not pd.api.types.is_numeric_dtype(df[target_column]):
            st.warning(f"Target column '{target_column}' could not be converted to numeric.")
            return ""

        return f"`{column}`.str.len() {operator_map[operator]} `{target_column}`"
    
    elif operator in ['column_equals','column_not_equals']:
        if value is None: return ""
        
        # Get the target column to compare with
        target_column = condition['value_1']
        if target_column not in df.columns:
            st.warning(f"Column {target_column} does not exist.")
            return ""
        
        # Check if we're doing character position comparison
        column_char_pos = condition.get('column_char', 0)
        target_char_pos = condition.get('value_2', 0)
        
        try:
            column_char_pos = int(column_char_pos) if column_char_pos not in [None, ''] else 0
            target_char_pos = int(target_char_pos) if target_char_pos not in [None, ''] else 0
        except ValueError:
            st.warning("Character positions must be integers")
            return ""
        
        # Case 1: Both character positions specified
        if column_char_pos > 0 and target_char_pos > 0:
            not_operator = '~' if operator == 'column_not_equals' else ''
            return (
                f"{not_operator}(`{column}`.notna() & "
                f"`{target_column}`.notna() & "
                f"`{column}`.str.len() >= {column_char_pos} & "
                f"`{target_column}`.str.len() >= {target_char_pos} & "
                f"`{column}`.str[{column_char_pos-1}] == "
                f"`{target_column}`.str[{target_char_pos-1}])"
            )
        
        # Case 2: Only first column's character position specified
        elif column_char_pos > 0:
            not_operator = '~' if operator == 'column_not_equals' else ''
            return (
                f"{not_operator}(`{column}`.notna() & "
                f"`{target_column}`.notna() & "
                f"`{column}`.str.len() >= {column_char_pos} & "
                f"`{column}`.str[{column_char_pos-1}] == "
                f"`{target_column}`)"
            )
        
        # Case 3: Only second column's character position specified
        elif target_char_pos > 0:
            not_operator = '~' if operator == 'column_not_equals' else ''
            return (
                f"{not_operator}(`{column}`.notna() & "
                f"`{target_column}`.notna() & "
                f"`{target_column}`.str.len() >= {target_char_pos} & "
                f"`{column}` == "
                f"`{target_column}`.str[{target_char_pos-1}])"
            )
            
        
        col_str = df[column].astype(str)
        target_col_str = df[target_column].astype(str)

        # Use the converted columns for the comparison
        if operator == 'column_equals':
            return col_str.eq(target_col_str)
        else:  # 'column_not_equals'
            return col_str.ne(target_col_str)
    

        # Default: full column comparison
        not_operator = '~' if operator == 'column_not_equals' else ''
        return f"{not_operator}`{column}`.eq(`{target_column}`)"
    
    
    elif operator in ['wildcard_match', 'wildcard_not_match']:
        if value is None:
            st.warning("You haven't specified a wildcard for a query condition.")
            return ""
        
        # Convert user-friendly wildcards to regex
        pattern = (
            str(value)
            .replace('*', '.*')  # * becomes .* (any characters)
            .replace('?', '.')    # ? becomes . (single character)
        )
        
        # Handle position-specific checks
        if value_2:
            try:
                char_pos = int(value_2) - 1
                if char_pos < 0:
                    st.warning("Character position must be greater than Zero")
                    return ""
                else:
                    pattern = f'^.{{{char_pos}}}{pattern}' # Create position-specific pattern
            except ValueError:
                st.warning(f"Invalid character position: {value_2}")
                return ""
        
        # Build the regex condition
        not_operator = '~' if operator == 'wildcard_not_match' else ''
        return f"{not_operator}`{column}`.str.match('^{pattern}$', case=False, na=False)"
    
    elif operator in ['non_distinct_combinations', 'distinct_combinations']:
        if value is None: return ""
            
        if value not in df.columns:
            st.warning(f"Column {value} does not exist.")
            return ""
            
        non_distinct_values = (
            df.groupby(value)[column]
            .nunique()
            .loc[lambda x: x > 1]
            .dropna()
            .index
        ).tolist()
        
        # from the remaining distinct records, get the "column" where "value" not in "non_distinct_values"
        # then include result (list) in final query
                
        if len(non_distinct_values) == 0:
            return "False" if operator == 'non_distinct_combinations' else "True"
        
        not_operator = '~' if operator == 'non_distinct_combinations' else ''
                
        return f"{not_operator}`{value}`.isin({non_distinct_values})"
        
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
    
    elif operator == 'between':
        if value == None or value_2 == None: return ""
        return f"`{column}` >= {value} & `{column}` <= {value_2}"
    
    elif operator in ['starts_with', 'ends_with']:
        return f"`{column}`.str.{operator_map[operator]}({value}, na=False)" if value is not None else ""
    
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
                
                if pos > 0:
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
    
    elif operator in ['in_column_list', 'not_in_column_list']:
        target_column = condition['value_1']

        if target_column not in df.columns:
            st.warning(f"Target column '{target_column}' does not exist.")
            return pd.Series(False, index=df.index)

        # This creates a boolean Series where each row's `column` value
        # is checked against the list of values in the *same row* of `target_column`.
        condition_mask = df.apply(
            lambda row: str(row[column]).strip() in [
                v.strip() for v in str(row[target_column]).split(',')
            ] if pd.notna(row[target_column]) else False,
            axis=1
        )

        # Invert the mask if the operator is 'not_in_column_list'
        if operator == 'not_in_column_list':
            return ~condition_mask
        else:
            return condition_mask
        
    elif operator in ['in_list', 'not_in_list']:
        if value in ['', None]:
            return ""
        
        values = get_list_from_selected_source(all_sheets, condition['value_1'])
        
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
                        if char_pos < 0:
                            st.warning(f"Character position must be ≥ 1 (got {char_pos})")
                            char_pos = None
                        elif char_pos == 0:
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
                return (
                    f"{_not}(`{column}`.isna() | "
                    f"`{column}`.str.len() < {column_char} | "
                    f"`{column}`.str[{column_char-1}].isin({values}))"
                )
            else:
                return f"{_not}`{column}`.isin({values})"
                    
        except ValueError:
            st.warning(f"Invalid value in list for column '{column}'.")
            return ""
    else:
        return ""
    
def get_op(op_str: str) -> str:
    """Helper to get standardized query operators."""
    if op_str.lower() == 'and':
        return ' & '
    elif op_str.lower() == 'or':
        return ' | '
    return ' '

def execute_query(all_sheets: dict, joined_df: pd.DataFrame, conditions: dict) -> pd.DataFrame:
    """
    Query execution handles:
    - Complex string matching
    - Nested logical conditions
    - Position-specific wildcards
    - Mixed AND/OR logic
    
    Args:
        sheets (pd.DataFrame): all sheets uploaded
        joined_df (pd.DataFrame): jioned dataframes
        conditions (dict): query conditions

    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if not conditions or joined_df.empty:
        return joined_df
    
    try:
        # Initialize a boolean mask
        final_mask = pd.Series(True, index=joined_df.index)
        current_mask = pd.Series(True, index=joined_df.index)
        current_logic = 'AND'  # Default to AND logic
        
        for cond in conditions:            
            # Handle logic changes
            if 'nested_logic' in cond:
                # Apply current group with its logic
                if current_logic == 'AND':
                    final_mask &= current_mask
                else:
                    final_mask |= current_mask
                
                # Reset for new group
                current_mask = pd.Series(True, index=joined_df.index)
                current_logic = cond['nested_logic']
                continue
            
            # Build and apply condition
            condition_result = build_condition(all_sheets, joined_df, cond)
            
            # Check the type of the result and handle accordingly
            if isinstance(condition_result, str):
                if not condition_result:
                    continue
                try:
                    cond_mask = joined_df.eval(condition_result, engine='python')
                except Exception as e:
                    st.error(f"Condition failed: {condition_result}\nError: {str(e)}")
                    continue
            elif isinstance(condition_result, pd.Series):
                cond_mask = condition_result
            else:
                continue # Handle unexpected return types
            
            # Apply with current logic
            if 'logic' in cond and cond['logic'].upper() == 'OR':
                current_mask |= cond_mask
            else:
                current_mask &= cond_mask
                                        
        # Apply the final group
        if current_logic == 'AND':
            final_mask &= current_mask
        else:
            final_mask |= current_mask
        
        return joined_df[final_mask]
    
    except Exception as e:
        st.write(e)
        st.error(f"Critical failure: {str(e)}")
        return joined_df