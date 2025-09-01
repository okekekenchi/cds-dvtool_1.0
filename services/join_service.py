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

def handle_error_return() -> dict:
    return {
        'joined_df': pd.DataFrame(),
        'residual_df': pd.DataFrame(),
        'total_records_failed': 0,
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

def perform_joins(sheets: dict, joins: list[dict], return_residuals: bool = False) -> dict:
    """
    Performs multi-table joins and returns a single cumulative residual of all failed records.
    
    Args:
        sheets: Dictionary of {sheet_name: DataFrame}
        joins: List of join specifications
        return_residuals: If True, returns cumulative residual
    
    Returns:
        dict: Contains joined data and cumulative residual of all failed records
        or pd.DataFrame: Single joined result if return_residuals=False
    """
    
    current_data = None
    cumulative_residual = pd.DataFrame()
    original_left_table = None
    original_record_count = 0
    
    for i, join in enumerate(joins):
        # Validate join specification
        required_keys = {'left_table', 'right_table', 'join_type', 'on_cols'}
        if not all(k in join for k in required_keys) or not join['on_cols']:
            st.warning(f"Invalid join specification in row {i+1}")
            return handle_error_return()
        
        on_cols = join['on_cols']
        join_type = join['join_type']
        left_table = join['left_table']
        right_table = join['right_table']
        is_anti_join = join_type.startswith("a_")
        
        # Store the original left table for residual reconstruction
        if i == 0:
            original_left_table = left_table
            original_left_data = sheets.get(left_table, pd.DataFrame())
            original_record_count = len(original_left_data)
        
        # Get dataframes
        left_df = current_data if current_data is not None else sheets.get(left_table)
        right_df = sheets.get(right_table)
        
        if left_df is None or right_df is None:
            missing_table = left_table if left_df is None else right_table
            st.error(f"Missing sheet/table: {missing_table}")
            return handle_error_return()
        
        # Prepare join columns
        left_on, right_on = prepare_join_columns(left_df, right_df, on_cols)
        if not left_on or not right_on:
            return handle_error_return()
        
        # Handle column naming conflicts
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
            
            # Determine main result and residual for this join step
            if is_anti_join:
                main_result = joined_with_indicator[joined_with_indicator['_merge'] == 'left_only'].copy()
                step_residual = joined_with_indicator[joined_with_indicator['_merge'] != 'left_only'].copy()
            else:
                main_result = joined_with_indicator[joined_with_indicator['_merge'] != 'left_only'].copy()
                step_residual = joined_with_indicator[joined_with_indicator['_merge'] == 'left_only'].copy()

            # Remove indicator column
            main_result = main_result.drop('_merge', axis=1)
            step_residual = step_residual.drop('_merge', axis=1)
            
            # CRITICAL: Reconstruct original records for this step's residual
            # We need to get back to the original left table records that failed
            original_left_data = sheets[original_left_table] if original_left_table in sheets else left_df
            
            # Get the indices of failed records from the original left table
            if i == 0:
                # First join: residual indices are directly from original left table
                failed_indices = step_residual.index
            else:
                # Subsequent joins: we need to trace back through the join chain
                # This is complex - for now, we'll use a simpler approach
                failed_indices = step_residual.index
            
            # Extract the original records that failed this join
            original_failed_records = original_left_data[original_left_data.index.isin(failed_indices)]
            
            # Add to cumulative residual (avoid duplicates)
            if cumulative_residual.empty:
                cumulative_residual = original_failed_records
            else:
                # Only add records that aren't already in the cumulative residual
                new_failed_indices = original_failed_records.index.difference(cumulative_residual.index)
                new_failed_records = original_failed_records[original_failed_records.index.isin(new_failed_indices)]
                cumulative_residual = pd.concat([cumulative_residual, new_failed_records], ignore_index=True)
            
            # Update current data for next join
            current_data = main_result
            
        except Exception as e:
            st.error(f"Join failed between {left_table} and {right_table}: {str(e)}")
            return handle_error_return()
    
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
        first_sheet= next(iter(sheets.values()))
        return (
            perform_joins(sheets, join_conditions)
            if join_conditions else
            handle_error_return() | {
                'joined_df': first_sheet,
                'residual_df': first_sheet,
                "total_records": len(first_sheet),
                'total_records_failed': len(first_sheet),
            }
        )
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
    