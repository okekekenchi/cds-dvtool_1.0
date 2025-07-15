import streamlit as st
from util.project_utils import join_types, get_sheet_columns

@st.dialog("Join Conditions", width='large')
def join_conditions(idx, join):
    """multi-column join"""
    col1, col2, col3, _ = st.columns([0.15, 0.3, 0.3, 0.25])
    
    with col1:
        st.write('', '', '')
        st.write('', '', '')
        f"Left table: **{join['left_table']}**"
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
        st.write('', '', '')
        st.write('', '', '')
        f"Right table: **{join['right_table']}**"
        
    st.session_state.validation['joins'][idx]['join_type'] = join_type
                
    col1, col2, col3 = st.columns([0.3, 0.3, 0.16])
    
    if 'on_cols' not in st.session_state.validation['joins'][idx]:
        st.session_state.validation['joins'][idx]['on_cols'] = []
       
    on_col = {}
    
    with col1:
        on_col['left_column'] = st.selectbox(
                                    "Left Column",
                                    options=get_sheet_columns(join['left_table']),
                                    index=None,
                                    help="Select which sheets you want to include in validation"
                                )
    with col2:
        on_col['right_column'] = st.selectbox(
                                    "Right Column",
                                    options=get_sheet_columns(join['right_table']),
                                    index=None,
                                    help="Select the column you want to join."
                                )
    with col3:
        st.write('')
        st.write('')
        if st.button("Add", key="add_join_columns", icon=":material/add:") and on_col:
            if on_col['right_column'] and on_col['left_column']:
                if on_col not in st.session_state.validation['joins'][idx]['on_cols']:
                    st.session_state.validation['joins'][idx]['on_cols'].append(on_col)
                else:
                    st.warning("Columns have already been joined")
            else:
                st.warning('Fill all required fields.')
    
    if not st.session_state.validation['joins'][idx]['on_cols']:
        st.write("Your join condition list is empty!")
    else:
        for i, on_col in enumerate(st.session_state.validation['joins'][idx]['on_cols']):
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
                    del st.session_state.validation['joins'][idx]['on_cols'][i]
                    
    _, col1, col2 = st.columns([0.6,0.2,0.2])
    with col1:
        if st.session_state.validation['joins'][idx]['on_cols']:
            if st.button("Save", key="save_join_condition", icon=":material/save:"):
                st.rerun()
    with col2:
        if st.button("Cancel", icon=":material/close:"):
            st.rerun()
