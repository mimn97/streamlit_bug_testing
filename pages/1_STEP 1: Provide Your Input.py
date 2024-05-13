import streamlit as st
from utils import store_every_responses
from loguru import logger

@logger.catch
def domain_input():
    def _commit(domain, purpose, scenario, user_id):
        st.session_state.domain = domain
        st.session_state.purpose = purpose
        st.session_state.scenario = scenario
        st.session_state.user_id = user_id

    # Instruction
    st.markdown('<h2> STEP 1: Provide Your Domain Information! </h2>', unsafe_allow_html=True)
    # step1_instruction_text = """ 
    #     <h2> 👉🏻 Instruction </h2>
    #     Under the section 'ℹ️ <b> Questions For Generating Your Taxonomy,' </b>
    #     <ol>
    #         <li> In Q1, please select the domain of your occupation. </li>
    #         <li> In Q2, please select the type of writing task that you want to build a taxonomy of text revision about. </li>
    #         <li> In Q3, please write down a description about an intended use case of this taxonomy in <b style="color:red"> full and complete sentences </b>. 
    #         This information will be used as a criteria to evaluate the GPT-generated elements of your taxonomy of interest, based on your domain information.</li>
    #         <li> In Q4: please copy and paste your ID code (attached in the invitation email) in the textbox. This will be used only for identifier purpose. 
    #         <li> After filling out all blanks, click '<b> Save Your Domain Information </b>'. </li>
    #     </ol>
    #     """
    step1_instruction_text = """ 
    <h2> 👉🏻 Instruction </h2>
    Please fill out the questions under the section 'ℹ️ <b> Questions For Generating Your Taxonomy.'</b>
    <h4>Notes</h4> 
    <ol>
        <li> In Q3, please write down a description about an intended use case of this taxonomy in <b style="color:red"> full and complete sentences </b>. 
        This information will be used as a criteria to evaluate the GPT-generated elements of your taxonomy of interest, based on your domain information.</li>
        <li> After filling out all blanks, click '<b> Save Your Domain Information </b>'. </li>
    </ol>
    """
    st.markdown(step1_instruction_text, unsafe_allow_html=True)
    st.warning("WARNING: Don't refresh the page unless you want to restart everything from beginning.")


    # Expert Input

    st.markdown("<hr><h3> ℹ️ Questions For Generating Your Taxonomy </h3>", unsafe_allow_html=True)

    domains = ['Finance', 'Human Resources', 'Information Technology', 'Legal', 'Marketing']
    selected_domain_idx = domains.index(st.session_state.domain) if st.session_state.domain is not None else 0
    domain = st.selectbox(label='Q1: Please select the domain of your occupation',
                          options=domains, index=selected_domain_idx)

    selected_purpose_idx = st.session_state.lst_purposes.index(st.session_state.purpose) if st.session_state.purpose is not None else 0
    purpose = st.selectbox(label='Q2: Please select the type of writing task that you want to build a taxonomy of text revision about.',
                           options=st.session_state.lst_purposes, index=selected_purpose_idx)
    if purpose == 'Others':
        other_purpose = st.text_input(label="What other type of writing tasks would like to work on instead?", 
                                      placeholder="e.g., Presentation", 
                                      value=st.session_state.other_purpose)
        
        if other_purpose != st.session_state.other_purpose:
            st.session_state.other_purpose = other_purpose
            st.session_state.lst_purposes.insert(len(st.session_state.lst_purposes)-1, other_purpose)
            st.session_state.purpose = st.session_state.other_purpose

    selected_scenario = st.session_state.scenario if st.session_state.scenario is not None else ''
    scenario = st.text_area(label="""Q3: Please write down a description about an intended use case of this taxonomy in full and complete sentences.""",
                             value=selected_scenario,
                             placeholder='e.g., For the legal domain, for example, this taxonomy will perform as a guideline for revising their email writing tasks.')
    
    given_user_id = st.session_state.user_id if st.session_state.user_id is not None else ''
    user_id = st.text_input(label="Q4: Please copy and paste your ID code (attached in the invitation email) in the textbox.", 
                            value = given_user_id, 
                            placeholder="e.g., 55455")

    save_domain_input = st.button(label='Save Your Domain Information', on_click=_commit, args=(domain, purpose, scenario, user_id), type="primary")
    
    # Check there's any missing input
    if save_domain_input:
        if not all([bool(st.session_state[prop]) for prop in step1_essential_properties[:-2]]):
            st.error("You did not provide every input to those four questions. Please fill out every four question and re-click this button.")
        else: # even if all inputs were provided
            if len(st.session_state.user_id) == 5: # additional check if the digit provided is 5.
                st.success("We successfully saved your provided information. Please move to the next page \"STEP 2: Generate Labels with AI\".")
                st.session_state.is_step1_complete = True
                store_every_responses(st.session_state)
            else:
                st.error("You've provided non-5 digit code. Please check your email again and enter the correct one.")
    
if __name__ == "__main__":

    st.set_page_config(
        page_title='STEP 1: Provide Information for Your Taxonomy!',
        # layout='wide',
        initial_sidebar_state='expanded',
    )

    # initialize state values
    step1_essential_properties = ['domain', 'lst_purposes', 'purpose', 'scenario', 'user_id', 'other_purpose', 'is_step1_complete']
    for prop in step1_essential_properties:
        if prop not in st.session_state:
            st.session_state[prop] = None
    
    if ('confirm_home_instruction' in st.session_state) and (st.session_state.confirm_home_instruction):
        if st.session_state.lst_purposes is None:
            st.session_state.lst_purposes = ["Email", "Meeting Minutes", "Project Proposal", "Others"]
        
        domain_input()
        st.cache_data.clear() 
        # st.write(st.session_state)
    else:
        st.error("You have not marked the checkbox that you have read all instruction carefully. Please go back to the Home page and mark the checkbox.")