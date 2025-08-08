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
        if not value:
            st.warning("Delimiter cannot be empty for split operation.")
            return df

        delimiter = ''
        max_split = -1
        try:
            split_parts = str(value).split(':', 1)
            delimiter = split_parts[0]
            if len(split_parts) > 1:
                max_split = int(split_parts[1])
        except (ValueError, IndexError):
            st.warning("Invalid format for delimiter and max split value. Use 'delimiter:max_split'.")
            return df

        # Handle value_2 as comma-separated column names
        split_cols = None
        if isinstance(value_2, str):
            split_cols = [col.strip() for col in value_2.split(',') if col.strip()]
        elif isinstance(value_2, list):
            split_cols = value_2

        # Perform the split using the max_split variable
        split_df = df[column].str.split(delimiter, n=max_split, expand=True)

        if split_cols:
            if len(split_cols) == split_df.shape[1]:
                split_df.columns = split_cols
            else:
                st.warning(
                    f"Number of split columns ({split_df.shape[1]}) doesn't match "
                    f"provided names ({len(split_cols)}). Using default column names."
                )
                split_df.columns = [f"{column}_{i+1}" for i in range(split_df.shape[1])]
            df = pd.concat([df, split_df], axis=1)
        else:
            # If no column names provided, store as list in original column
            df[column] = df[column].str.split(delimiter, n=max_split)
    
    elif operator == 'get_character':
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
        df[new_column_name] = df[column].astype(str).str.slice(start=position-1, stop=position).fillna('')
                
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