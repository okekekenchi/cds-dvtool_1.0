import pandas as pd
import streamlit as st

def merge_operation(df: pd.DataFrame, condition: dict, column:str, value, value_2):
    if value not in df.columns:
        st.warning(f"Column '{value}' not found for merge operation.")
        return df
    if not value_2 or not (isinstance(value_2, str) or isinstance(value_2, list)):
        st.warning("Please provide a valid column name for the merged result.")
        return df
    
    # Handle NaN values and add separator option
    separator = condition.get('separator', '')  # Optional enhancement
    df[value_2] = df[column].fillna('').astype(str) + separator + df[value].fillna('').astype(str)
    return df

def split_operation(df: pd.DataFrame, condition: dict, column:str, value, value_2):
    if not value:
        st.warning("Delimiter cannot be empty for split operation.")
        return df
    
    if column not in df.columns:
        st.warning(f"Column '{column}' not found.")
        return df
    
    # Convert to string if not already
    if not pd.api.types.is_string_dtype(df[column]):
        try:
            df[column] = df[column].astype(str)
        except:
            st.warning(f"Column '{column}' cannot be converted to string type.")
            return df
    
    # Parse delimiter and max_split
    delimiter = str(value)
    max_split = condition.get('max_split', -1)
    
    if ':' in value:
        try:
            parts = value.split(':', 1)
            delimiter = parts[0]
            if len(parts) > 1 and parts[1]:
                max_split = int(parts[1])
        except ValueError:
            st.warning("Invalid max_split value. Using default.")
    
    # Handle column names
    split_cols = []
    if isinstance(value_2, str):
        split_cols = [col.strip() for col in value_2.split(',') if col.strip()]
    elif isinstance(value_2, list):
        split_cols = value_2
    
    # Perform split
    split_df = df[column].str.split(delimiter, n=max_split, expand=True)
    
    if split_cols and len(split_cols) == split_df.shape[1]:
        for i, col_name in enumerate(split_cols):
            df[col_name] = split_df[i]
    else:
        for i in range(split_df.shape[1]):
            df[f"{column}_{i+1}"] = split_df[i]
    
    return df

def get_character_operation(df: pd.DataFrame, column:str, value, value_2):
    """gets a character at the specified position and creates a new column based on the character.
    """
    # The 'value' will hold the 1-based character position.
    # The 'value_2' will hold the name of the new column.
    if not value or not value_2:
        st.warning("Please specify both the character position and the new column name.")
        return df
    
    try:
        position = int(value)
        if position <= 0:
            st.warning("Character position must be a positive integer.")
            return df
    except ValueError:
        st.warning("Character position must be an integer.")
        return df

    new_column_name = str(value_2)

    # Use .str.slice to extract the character at the specified position.
    # We subtract 1 from the position because Python indexing is 0-based.
    # We use .fillna('') to handle any NaN values gracefully.
    df[new_column_name] = (
        df[column].astype(str)
        .str.slice(start=position-1, stop=position)
        .replace('', None)  # Empty string for out-of-bounds becomes None
    )
                
    return df

def apply_column_operation(df: pd.DataFrame, condition: dict) -> pd.DataFrame:
    """
    Apply column operations like merge and split to column.

    Args:
        df (pd.DataFrame): The DataFrame to operate on.
        condition (dict): A dictionary containing column operation details.
                          Expected keys: 'column', 'operator', 'value_1', 'value_2'.

    Returns:
        pd.DataFrame: The DataFrame after applying the operation.
    """
    column = condition['column']
    operator = condition['operator']
    value = condition['value_1']
    value_2 = condition.get('value_2', None)
    
    if column not in df.columns:
        st.warning(f"Column '{column}' not found.")
        return df
    
    try:
        if operator == 'merge':
            return merge_operation(df, condition, column, value, value_2)
        
        elif operator == 'split':
            return split_operation(df, condition, column, value, value_2)
        
        elif operator == 'get_character':
            return get_character_operation(df, column, value, value_2)
        
        else:
            st.warning(f"Unknown operator: {operator}")
            return df
    except Exception as e:
        st.error(f"Operation '{operator}' failed: {str(e)}")
        return df

def run_column_operations(all_sheets:dict, selected_sheets: list[dict]) -> dict:
    """
    Runs column operation(s) for each selected sheet
    """
    try:
        all_df = {}
        for sheet in selected_sheets:
            
            sheet_df = all_sheets.get(sheet.get('name'), pd.DataFrame())
            
            if not sheet.get('col_operations', []) or sheet_df.empty:
                all_df[sheet['name']] = sheet_df
                continue
            
            df = sheet_df.copy()
            try:        
                for operation in sheet.get('col_operations'):
                    df = apply_column_operation(df, operation)
            except Exception as e:
                st.error(f"Column operation failed: {str(e)}")
            finally:
                all_df[sheet['name']] = df
    except Exception as e:
        st.warning(f"Could not perform column operation {str(e)}")
    finally:
        return all_df