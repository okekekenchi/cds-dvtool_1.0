import streamlit as st
import pandas as pd

join_types = {
    "left":"Left Join",
    "a_left":"Left Anti-Join",
    "right":"Right Join",
    "a_right":"Right Anti-Join",
    "inner":"Inner Join",
    "a_inner":"Inner Anti-Join",
    "outer":"Outer Join"
}

import pandas as pd
from pandas.api.types import infer_dtype

def detect_exact_dtype(series: pd.Series) -> str:
    """Detect the exact data type of a pandas Series using pandas' robust inference."""
    # Use pandas' built-in, optimized inference engine first for object types.
    inferred_type = infer_dtype(series, skipna=True)

    # Map inferred types to your desired categories
    if inferred_type in ['integer', 'mixed-integer']:
        return 'integer'
    if inferred_type in ['floating', 'decimal', 'mixed-integer-float']:
        return 'float'
    if inferred_type in ['datetime', 'datetime64', 'date']:
        return 'datetime'
    if inferred_type == 'boolean':
        return 'boolean'
    if inferred_type in ['string', 'unicode']:
        return 'string'
    if inferred_type == 'empty':
        return 'empty'
    
    # Fallback for complex types or if pandas' main dtypes are already specific
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'datetime'
    if pd.api.types.is_integer_dtype(series):
        return 'integer'
    if pd.api.types.is_float_dtype(series):
        return 'float'
        
    return 'mixed' # If inference is still unclear (e.g., 'mixed')

def handle_error_return() -> dict:
    """Default return"""
    return {
        'joined_df': pd.DataFrame(),
        'residual_df': pd.DataFrame(),
        'total_records': 0,
        'join_steps': 0
    }
    
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
    
def prepare_join_columns(left_df, right_df, on_cols):
    """Prepare join columns with type conversion"""
    left_on, right_on = [], []
    
    for col in on_cols:
        left_col, right_col = col['left_column'], col['right_column']
        
        if left_col not in left_df.columns or right_col not in right_df.columns:
            st.error(f"Join column not found: {left_col} or {right_col}")
            return [], []
        
        # Convert types if needed
        left_df, right_df = convert_column_types(left_df, right_df, left_col, right_col)
        if left_df is None or right_df is None:
            return [], []
        
        left_on.append(left_col)
        right_on.append(right_col)
    
    return left_on, right_on

def handle_column_conflicts(left_df, right_df, right_on, right_table):
    """Handle column naming conflicts"""
    suffix = f"_{right_table}"
    right_columns_to_rename = {
        col: f"{col}{suffix}" 
        for col in right_df.columns 
        if col in left_df.columns and col not in right_on
    }
    
    right_df_renamed = right_df.rename(columns=right_columns_to_rename)
    right_on_renamed = [right_columns_to_rename.get(col, col) for col in right_on]
    
    return right_df_renamed, right_on_renamed

def perform_joins(sheets: dict, joins: list[dict]) -> dict:
    """
    Performs multi-table joins and returns a single cumulative residual of all failed records.
    
    Args:
        sheets: Dictionary of {sheet_name: DataFrame}
        joins: List of join specifications
    
    Returns:
        dict: Contains joined data and cumulative residual of all failed records
    """
    current_data = None
    cumulative_residual = pd.DataFrame()
    original_left_table_name = joins[0]['left_table'] if joins else None
    
    if not original_left_table_name:
        return handle_error_return()
    
    original_left_data = sheets.get(original_left_table_name).copy()
    original_record_count = len(original_left_data)
    
    original_index_col = '__original_index__'
    original_left_data[original_index_col] = original_left_data.index
    
    for i, join in enumerate(joins):
        # Validate join specification
        required_keys = {'left_table', 'right_table', 'join_type', 'on_cols'}
        if not all(k in join for k in required_keys) or not join['on_cols']:
            st.warning(f"You have not specified join condition for row {i+1}")
            return handle_error_return()
        
        on_cols = join['on_cols']
        join_type = join['join_type']
        left_table = join['left_table']
        right_table = join['right_table']
        is_anti_join = join_type.startswith("a_")
        
        # Store the original left table for residual reconstruction
        left_df = original_left_data if i == 0 else current_data
        right_df = sheets.get(right_table)
        
        if left_df is None or right_df is None:
            missing_table = left_table if left_df is None else right_table
            st.error(f"Missing sheet/table: {missing_table}")
            return handle_error_return()
        
        # Prepare join columns
        left_on, right_on = prepare_join_columns(left_df, right_df, on_cols)
        if not left_on or not right_on:
            return handle_error_return()
        
        right_df_renamed, right_on_renamed = handle_column_conflicts(
            left_df, right_df, right_on, right_table
        )
        
        # Perform the join with indicator
        base_join_type = join_type.replace("a_", "")
        try:
            joined_with_indicator = pd.merge(
                left_df, 
                right_df_renamed,
                left_on=left_on, 
                right_on=right_on_renamed,
                how=base_join_type,
                indicator=True
            )
            
            if is_anti_join:
                main_result = joined_with_indicator[joined_with_indicator['_merge'] == 'left_only'].copy()
                step_residual = joined_with_indicator[joined_with_indicator['_merge'] == 'both'].copy()
            else:
                if base_join_type == 'inner':
                    main_result = joined_with_indicator[joined_with_indicator['_merge'] == 'both'].copy()
                    step_residual = joined_with_indicator[joined_with_indicator['_merge'] == 'left_only'].copy()
                else: # left, right, outer
                    main_result = joined_with_indicator.copy()
                    step_residual = joined_with_indicator[joined_with_indicator['_merge'] == 'left_only'].copy()

            # Remove indicator column
            current_data = main_result.drop('_merge', axis=1)
            step_residual = step_residual.drop('_merge', axis=1)
            
            failed_original_indices = step_residual[original_index_col]
            
            # Extract the original records that failed this join
            original_failed_records = original_left_data[original_left_data.index.isin(failed_original_indices)]
    
            # Add to cumulative residual (avoid duplicates)
            if cumulative_residual.empty:
                cumulative_residual = original_failed_records
            else:
                # Only add records that aren't already in the cumulative residual
                new_failed_indices = original_failed_records.index.difference(cumulative_residual.index)
                cumulative_residual = pd.concat([cumulative_residual, original_failed_records.loc[new_failed_indices]])
            
        except Exception as e:
            st.error(f"Join failed between {left_table} and {right_table}: {str(e)}")
            return handle_error_return()
    
    # Before returning, drop the helper column from the final results
    if current_data is not None and original_index_col in current_data.columns:
        current_data = current_data.drop(columns=[original_index_col])
    if not cumulative_residual.empty and original_index_col in cumulative_residual.columns:
        cumulative_residual = cumulative_residual.drop(columns=[original_index_col])

    return {
        'joined_df': current_data if current_data is not None else pd.DataFrame(),
        'residual_df': cumulative_residual,
        'total_records': original_record_count,
        'join_steps': len(joins)
    }
    
def get_joined_sheets(sheets: dict, join_conditions: list[dict]) -> dict:
    """
    Returns the first selected sheet (dataframe) if no join condition is specified
    Joins all the selected sheets when join condition 

    Args:
        sheets (dict): selected sheets
        join_conditions (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    if sheets:
        if join_conditions:
            return perform_joins(sheets, join_conditions)
        else:
            first_sheet = next(iter(sheets.values()))
            return {
                'joined_df': first_sheet,
                'residual_df': pd.DataFrame(columns=first_sheet.columns),
                'total_records': len(first_sheet),
                'join_steps': 0
            }
    else:
        return handle_error_return()

def get_common_columns(sheets: dict, sheet_name1: str, sheet_name2: str) -> list[str]:
    """
    Get matching column names between two sheets stored in session state.

    Args:
        sheets: all sheets in workbook
        sheet_name1: The name of the first sheet.
        sheet_name2: The name of the second sheet.

    Returns:
        A list of column names common to both sheets. Returns an empty list
        if no common columns are found or if either sheet name is not found
        in the session state.
    """    
    if sheet_name1 in sheets and sheet_name2 in sheets:
        cols1 = set(sheets[sheet_name1].columns)
        cols2 = set(sheets[sheet_name2].columns)
        return list(cols1 & cols2)
    else:
        return []    

def print_matching_columns(sheets:dict, join:dict):
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
    
    matching_columns = get_common_columns(sheets, join['left_table'], join['right_table'])
    if not matching_columns:
        if join['left_table'] and join['right_table']:
            st.badge("The tables don't share any common column names for merging/joining",
                    icon=":material/warning:", color="orange")
    else:
        formatted_columns  = ", ".join(item.strip() for item in matching_columns)
        st.badge(f"**Matching column names include:** {formatted_columns }",
                    icon=":material/check:", color="gray")
    