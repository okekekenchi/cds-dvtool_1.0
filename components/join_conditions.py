import streamlit as st
from services.workbook_service import get_sheet_columns
from services.join_service import join_types

@st.dialog("Join Conditions", width='large')
def join_conditions(sheets:dict, idx:int, join:dict):
    """multi-column join"""
    col1, col2, col3, _ = st.columns([0.15, 0.3, 0.3, 0.25])

    with col1:
        st.write('')
        st.write('')
        st.write(f"Left table: **{join['left_table']}**")
        
    with col2:
        join_type = st.selectbox(label='',
                        placeholder="Join Type",
                        options=join_types.keys(),
                        index=list(join_types.keys()).index(join['join_type']),
                        help="Select which join type to implement",
                        format_func=lambda x: join_types[x],
                        key="join_type_condition"
                    )
    with col3:
        st.write('')
        st.write('')
        st.write(f"Right table: **{join['right_table']}**")
        
    col1, col2, col3 = st.columns([0.3, 0.3, 0.16])
    
    if 'on_cols' not in st.session_state.config['joins'][idx]:
        st.session_state.config['joins'][idx]['on_cols'] = []
    
    on_col = {}
    
    with col1:
        on_col['left_column'] = st.selectbox(
                                    "Left Column *",
                                    options=get_sheet_columns(sheets, join['left_table']),
                                    index=None,
                                    help="Select which sheets you want to include in validation"
                                )
    with col2:
        on_col['right_column'] = st.selectbox(
                                    "Right Column *",
                                    options=get_sheet_columns(sheets, join['right_table']),
                                    index=None,
                                    help="Select the column you want to join."
                                )
    error_msg = None
    with col3:
        st.write('')
        st.write('')
        if st.button("Add", key="add_join_columns", icon=":material/add:") and on_col:
            if on_col['right_column'] and on_col['left_column']:
                if on_col not in st.session_state.config['joins'][idx]['on_cols']:
                    st.session_state.config['joins'][idx]['on_cols'].append(on_col)
                else:
                    error_msg = "Columns have already been joined"
            else:
                error_msg = 'Fill all required fields.'
    
    if error_msg: st.badge(error_msg, color='orange')
    
    if not st.session_state.config['joins'][idx]['on_cols']:
        st.write("Your join condition list is empty!")
    else:
        for i, on_col in enumerate(st.session_state.config['joins'][idx]['on_cols']):
            st.divider()
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                col4, col5, col6 = st.columns([0.4,0.2,0.3])
                with col4:
                    st.write(f"**{join['left_table']} . {on_col['left_column']}**")
                with col5:
                    st.write("**=**")
                with col6:
                    st.write(f"**{join['right_table']} . {on_col['right_column']}**")
            with col2:
                if st.button(f"Delete", key=f"delete_join_condition_{i}", icon=":material/delete:"):
                    del st.session_state.config['joins'][idx]['on_cols'][i]
                    st.rerun(scope='fragment')
                    
    _, col1, col2 = st.columns([0.6,0.2,0.2])
    with col1:
        if st.session_state.config['joins'][idx]['on_cols']:
            if st.button("Save", key="save_join_condition", icon=":material/save:"):
                st.session_state.config['joins'][idx]['join_type'] = join_type
                st.rerun()
    with col2:
        if st.button("Cancel", icon=":material/close:"):
            st.rerun()
