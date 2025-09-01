import streamlit as st

STATUS_OPTIONS = {
	1:"**Expand All**",
	0:"**Collapse All**"
}

def init_session_var():
	if 'validation_results' not in st.session_state:
		st.session_state.validation_results = {}
	if 'collapse_report' not in st.session_state:
		st.session_state.collapse_report = 0

def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, return default if denominator is zero"""
    return numerator / denominator if denominator != 0 else default
  
def findRule(rule_id):
  if st.session_state.all_rules:
    for rule in st.session_state.all_rules:
      if rule["id"] == rule_id:
        return rule
  else:
    return {}

@st.fragment
def project_report():
	"""Display the validation results in a user-friendly format"""
	init_session_var()
	st.markdown("""
		<style>
			.stExpander .stColumn { height: auto; background: white; }
		</style>
	"""
	, unsafe_allow_html=True)
	
	result_dfs = st.session_state.validation_results

	if result_dfs:
		st.segmented_control(
			"", options=STATUS_OPTIONS.keys(),
			format_func=lambda option: STATUS_OPTIONS[option],
			label_visibility="collapsed",
			default=1,
			key="collapse_report",
			width="content"
		)
  
		for idx, result in enumerate(result_dfs):
	
			total, failed = result['total_records'], len(result['failed_df'])
			passed = total - failed
			collapse = st.session_state.collapse_report
			expanded = collapse if collapse in [0,1] else 0
			rule = findRule(result["rule_id"])
   
			with st.expander(f"Rule {idx+1}: {rule['name']}", expanded=expanded, icon=":material/expand:"):
				col1, col2, col3 = st.columns(3)
				
				with col1:
					st.metric("Total Records", total,  border=True, height=135)
				with col2:
					st.metric("Passed", passed, border=True,
							delta=f"{safe_divide(passed, total)*100:.1f}%")
				with col3:
					st.metric("Failed", failed, border=True,
							delta=f"{-safe_divide(failed, total)*100:.1f}%")
				
				# Show failed records if any
				if failed:
					st.write("**Failed Records:**")
					st.dataframe(result['failed_df'])
					
					st.success(f"""
						**Final Result:** {failed} of {total} 
						record(s) failed the applied validation rule(s).
					""")
				else:
					st.info("There are no failed records.")
	else:
		st.info("Run validation check(s) to view report")
