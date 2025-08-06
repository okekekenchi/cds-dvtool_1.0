import pandas as pd
import streamlit as st

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
    
    if operator == 'merge':
        if value not in df.columns:
            st.warning(f"Column '{value}' not found for merge operation.")
            return df
        if not value_2 or not isinstance(value_2, str):
            st.warning("Please provide a valid column name for the merged result.")
            return df
        
        df[value_2] = df[column].astype(str) + df[value].astype(str)
    
    elif operator == 'split':
        if value is None or value == '':
            st.warning("Delimiter cannot be empty for split operation.")
            return df
        
        delimiter = str(value)
        # Handle value_2 as comma-separated column names
        split_cols = None
        if value_2 and isinstance(value_2, str):
            split_cols = [col.strip() for col in value_2.split(',') if col.strip()]
        elif isinstance(value_2, list):
            split_cols = value_2
        
        # Perform the split
        split_df = df[column].str.split(delimiter, expand=True)
        
        if split_cols:
            if len(split_cols) == split_df.shape[1]:
                split_df.columns = split_cols
            else:
                st.warning(
                    f"Number of split columns ({split_df.shape[1]}) doesn't match "
                    f"provided names ({len(split_cols)}). Using default column names."
                )
                # Add split columns with default names if counts don't match
                split_df.columns = [f"{column}_{i+1}" for i in range(split_df.shape[1])]
            df = pd.concat([df, split_df], axis=1)
        else:
            # If no column names provided, store as list in original column
            df[column] = df[column].str.split(delimiter)
            
    return df

def run_column_operations(joined_df: pd.DataFrame, col_operations: dict) -> pd.DataFrame:
    """
    """
    if not col_operations or joined_df.empty:
        return joined_df
    
    df = joined_df.copy()
    try:        
        for operation in col_operations:
            df = apply_column_operation(df, operation)
            
        return df
    except Exception as e:
        st.error(f"Column operation failed: {str(e)}")
        return df
    