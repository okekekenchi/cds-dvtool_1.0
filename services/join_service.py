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
    
    result = pd.DataFrame()
    suffix_separator = "_"
    
    for i, join in enumerate(joins):
        # Validate join specification
        required_keys = {'left_table', 'right_table', 'join_type', 'on_cols'}
        if not all(k in join for k in required_keys):
            st.warning(f"Missing required join specification(s) in **row {i+1}**")
            return pd.DataFrame()
        
        on_cols = join['on_cols']
        join_type = join['join_type']
        left_table = join['left_table']
        right_table = join['right_table']
        is_anti_join = join_type[:2] == "a_"
        
        if not len(on_cols):
            st.warning(f"Missing required join specification(s) in **row {i+1}**")
            return pd.DataFrame()
        
        left_df = result if not result.empty else sheets.get(left_table)
        right_df = sheets.get(right_table)
        
        if left_df is None or right_df is None:
            st.error(f"Missing sheet/table: {left_table if left_df is None else right_table}")
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
        
        right_suffix = f"{suffix_separator}{join['right_table']}"

        # Check for conflicts with existing columns
        right_columns = set(right_df.columns) - set(col['right_column'] for col in join['on_cols'])

        # Resolve conflicts by appending right_suffix
        rename_cols = {
            col: f"{col}{right_suffix}" 
            for col in right_columns 
            if col in set(left_df.columns)
        }
        
        if rename_cols:
            st.write(f"\n**Column Conflicts Renamed:** `{rename_cols}`")
        
        # Apply renaming to right_df (ONLY to non-join columns)
        right_df_renamed = right_df.rename(columns=rename_cols)
        
        if left_on and right_on:
            try:
                result = pd.merge(left_df, right_df_renamed,
                                left_on=left_on, right_on=right_on,
                                how=(join_type).replace("a_", ""),
                                indicator=is_anti_join,
                                suffixes=("", f"{suffix_separator}{right_table}")
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


def get_joined_sheets(sheets: dict, join_conditions: list) -> pd.DataFrame:
    """
    Returnsd the first selected sheet (dataframe) if no join condition is specified
    Joins all the selected sheets when join condition 

    Args:
        sheets (dict): selected sheets
        join_conditions (list): _description_

    Returns:
        pd.DataFrame: _description_
    """
    if sheets:
        first_sheet= next(iter(sheets.values()))
        return perform_joins(sheets, join_conditions) if join_conditions else first_sheet
    else:
        return pd.DataFrame

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
        
        