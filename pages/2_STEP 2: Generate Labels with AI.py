import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import json
from json.decoder import JSONDecodeError
import time
import os
from loguru import logger

from taxonomy import Label
from utils import hover_button, store_every_responses

# load_dotenv('../../.env')
openai_api_key = 'your own key'
client = OpenAI(api_key=openai_api_key)

@logger.catch
def step2_instruction():
 
    # Instruction
    st.markdown('<h2> STEP 2: Generate Labels with AI! </h2>', unsafe_allow_html=True)
    st.info("""INFO: The elements 'Labels' will be the conceptualized dimensions of a taxonomy of revision intentions in your occupation domain.""")
    step2_instruction_text = """ 
    <h2> 👉🏻 Instruction </h2>
    <ol>
        <li> Under <b> ✅ Confirm Your Information </b>, please confirm your inputs from STEP 1, and click <b> 🤖 Confirm and Generate Labels </b>. </li>
        <li> Under <b> 🧐 Validate AI-generated Labels </b>, you will see the left pane of generated labels and the right pane of validation page. 
        Please click each button of the labels and follow the instruction on the right pane to validate them. </li>
        <li> If you find the generated labels miss some important dimensions of revision in your occupation domain, please click <b> Add Your Own Labels </b>. 
        After closing the window, you will see the label button added to the left pane.   </li>
    </ol>
    """
    st.markdown(step2_instruction_text, unsafe_allow_html=True)
    st.warning("Warning: DO NOT REFRESH the page unless you want to restart everything from beginning.")
    st.divider()

@logger.catch
def step2_confirm_input():
    
    if "confirm_clicked" not in st.session_state:
        st.session_state.confirm_clicked = False

    st.markdown("<h2> ✅ Confirm Your Information </h2>", unsafe_allow_html=True)

    with st.container(border=True):
        st.write(f"1. Your Working Domain: {st.session_state.domain}")
        st.write(f"2. The type of writing task: {st.session_state.purpose}")
        st.write(f"3. The intended use case scenario of your taxonomy: {st.session_state.scenario}")

    click_confirm_input = st.button("🤖 Confirm and Generate Labels", type="primary")
    if click_confirm_input:
        st.session_state.confirm_clicked = True
        with st.status("Generating Labels with GPT-4...", expanded=True) as label_gen_status:
            st.write("Connecting to GPT-4...")
            st.write("Asking GPT-4 to generate...")
            st.write("Generating Now. Please Wait Until GPT-4 completes...")
            labels = generate_labels(st.session_state.domain, st.session_state.purpose, st.session_state.user_id)
            time.sleep(2)
            label_gen_status.update(label="Label Generation Complete!", state='complete', expanded=False)

    if st.session_state.confirm_clicked:
        st.divider()
        step2_show_and_validate(st.session_state.domain, st.session_state.purpose, st.session_state.user_id)
                
@logger.catch
@st.cache_data(show_spinner=False, persist="disk")
def generate_labels(domain, purpose, user_id):
    def _ask_gpt4_labels(domain, purpose):

        system_prompt = f"""You're a helpful assistant helping a user generate the labels of edit intentions in their writing task of {purpose}. 
                        The user is a business professional in the following domain: {domain}. 
                        """
        with open('prompt_collection/generation/label_generation.txt', 'r') as f:
            label_prompt = f.read()
        f.close()
        
        label_prompt = label_prompt.format(purpose, domain, purpose, domain)
        label_generation_prompt = client.chat.completions.create(model="gpt-4", 
                                                        messages = [{"role":"system", "content":system_prompt}, 
                                                                    {"role":"user", "content":label_prompt}], 
                                                        temperature = 0.8 # temperature?
                                                        )
        label_response = label_generation_prompt.choices[0].message.content
        return label_response
    
    cache_key = f"{domain}_{purpose}_{user_id}_labels"

    if cache_key in st.session_state:
        return st.session_state[cache_key]
    else:
        gpt4_taxo_labels = _ask_gpt4_labels(domain, purpose)
        # Handling JSONDecoderError issues
        try:
            gpt4_taxo_labels = json.loads(gpt4_taxo_labels)
        except JSONDecodeError as e:
            gpt4_taxo_labels = _ask_gpt4_labels(domain, purpose)
            gpt4_taxo_labels = json.loads(gpt4_taxo_labels)
        except:
            st.error("Something weird has happened. Please try generating labels again.")

        label_buttons = []
        for i, label in enumerate(gpt4_taxo_labels):
            label_buttons.append(Label(id=i, text=label['Label'], rationale=label['Rationale'], decision=None, is_gpt=True))

        # Cache the generated labels in the session state
        st.session_state[cache_key] = label_buttons
        return label_buttons    

@logger.catch
def step2_show_and_validate(domain, purpose, user_id):

    def _label_click(label: Label):
        st.session_state.selected_label_id = label.id
        st.session_state.selected_label_name = label.text 
        st.session_state.selected_label_rationale = label.rationale
        st.session_state.selected_label_decision = label.decision
        st.session_state.selected_label_gpt = label.is_gpt
        st.session_state.selected_label_rejection = label.rejection

    def _update_label_name(name: str):
        st.session_state.selected_label_name = name

    def _update_label_rationale(rationale: str):
        st.session_state.selected_label_rationale = rationale

    def _update_label_decision(decision:str):
        st.session_state.selected_label_decision = decision

    def _update_label_rejection(rejection:str):
        st.session_state.selected_label_rejection = rejection
    
    def _show_pane_page(labels: list): # st.session_state[cache_key]
        if st.session_state.selected_label_id is None:
            st.session_state.selected_label_id = labels[0].id
            st.session_state.selected_label_name = labels[0].text 
            st.session_state.selected_label_rationale = labels[0].rationale
            st.session_state.selected_label_decision = labels[0].decision
            st.session_state.selected_label_gpt = labels[0].is_gpt
            st.session_state.selected_label_rejection = labels[0].rejection

        if "status_updated_labels" not in st.session_state:
            st.session_state.status_updated_labels = []

        st.write("✅ (Accepted); ❌  (Rejected); ❓ (Unvalidated)")
        hover_button()

        num_columns = 2
        with st.container(border=True):
            columns = st.columns(num_columns)
            for index, label in enumerate(labels):
                button_key = f"label_button_{label.id}"
                if label.is_validated==True: # for only buttons that were already validated
                    if (label.is_selected==True) and (label.id in st.session_state.status_updated_labels):
                        button_label = f"✅ {label.text}" 
                    elif (label.is_selected == False) and (label.id in st.session_state.status_updated_labels):
                        button_label = f"❌ {label.text}"
                else: # for the buttons that were not validated yet
                    button_label = f"❓{label.text}" 
                with columns[index % num_columns]:
                    if st.button(button_label, key=button_key, use_container_width=True):
                        _label_click(label)
                        if label.id not in st.session_state.status_updated_labels:
                            st.session_state.status_updated_labels.append(label.id)

    def _insert_your_own(labels:list):

        with st.popover("Add Your Own Labels", use_container_width=False):
            st.markdown("<h4> Provide Your Own Label </h4>", unsafe_allow_html=True)

            new_label_name = st.text_input("What is the name of a new label you would like to add?", placeholder="e.g., Employee Benefits (in HR domain, for example)")
            new_label_rationale = st.text_area("Why do you think this label is important to be added when revising your domain writing tasks? Please write down in 1-2 sentences.", 
                                               placeholder="e.g., HR team may revise information about employee benefits and compensation to ensure accurate delivery of this important information. ",
                                               height=150)
            
            if st.button("Add"):
                if (new_label_name != "") and (new_label_rationale != ""):
                    st.success("We successfully added this label to be validated. Please close this window and go back to the validation section.")
                    end_label_idx = len(labels)
                    labels.append(Label(id=end_label_idx, text=new_label_name, rationale=new_label_rationale, decision=None, is_gpt=False))
                    st.rerun()
                else:
                    st.error("You did not answer the two questions. Please fill out the two if you would like to create a new label. Otherwise, close this window.")

    def _validate_pane_page(labels: list): # st.session_state[cache_key]
        label_id = st.session_state.selected_label_id
        label_name = st.session_state.selected_label_name 
        label_rationale = st.session_state.selected_label_rationale
        label_gpt = st.session_state.selected_label_gpt
        label_rejection = st.session_state.selected_label_rejection

        if label_gpt: # if gpt-4 generated
            st.markdown(f"""<h3>Selected GPT-4 Label: <b style="color:blue">{st.session_state.selected_label_name}</mark> </h3>""", unsafe_allow_html=True)
            st.markdown("""Please read the label name and the reason of genertaion below thoroughly. """)

            # Update Decision
            flag_manual_update = True
            decision_options = ["Accept GPT-4 Suggestions", "Accept but Manual Modification", "Reject"]
        
            
            curr_idx = decision_options.index(st.session_state.selected_label_decision) if st.session_state.selected_label_decision is not None else 0
            feedback_mode = st.radio(label="Q: What is your decision for this label?", index=curr_idx,
                                    on_change=_update_label_decision, args=(st.session_state.selected_label_decision,),
                                options=decision_options, 
                                help="""If you entirely agree with the two outputs, please click Accept GPT-4 Suggestions. 
                        If you agree with them but would like to modify a part of them, please click Accept but Manual Modifications. 
                        Otherwise, please click Reject.""")
            
            if feedback_mode != st.session_state.selected_label_decision:
                st.session_state.selected_label_decision = feedback_mode
            
            if feedback_mode == decision_options[1]: # modify
                flag_manual_update = False
                st.info("Please update the two inputs with your feedback and/or suggestions.")
            else:            
                flag_manual_update = True
        
            # Update Label Name with expert feedback
            current_label_name = st.text_input(label="The name of AI-generated Label", value=label_name, disabled=flag_manual_update,
                        on_change=_update_label_name, args=(st.session_state.selected_label_name,))
            
            if current_label_name != st.session_state.selected_label_name:
                st.session_state.selected_label_name = current_label_name

            # Update Label Rationale with expert feedback
            current_label_rationale = st.text_area(label="Why did AI generate this label as an important revision style in your domain writing?", 
                                                   value=label_rationale, disabled=flag_manual_update,
                        on_change=_update_label_rationale, args=(st.session_state.selected_label_rationale,), height=150)
            
            if current_label_rationale != st.session_state.selected_label_rationale:
                st.session_state.selected_label_rationale = current_label_rationale
            
            # Collect why reject?
            if feedback_mode == decision_options[2]: # reject
                current_label_rejection = st.text_area(label="Why do you reject this AI-generated label? Please write 2-3 sentences that are very clear and specific to your domain.", value=label_rejection,
                        on_change=_update_label_rejection, args=(st.session_state.selected_label_rejection,), height=150, 
                        placeholder="""e.g., the label name of clarity and tone formalness sounds too general to be said as financial-specific revision intention. 
                        
                        (Given that your occupation is finance domain.) """)
                
                if current_label_rejection != st.session_state.selected_label_rejection:
                    st.session_state.selected_label_rejection = current_label_rejection

            col1, col2 = st.columns([3.2,1])

            with col1:
                st.markdown("<p> Click Submit & Update only if you are done with your decision. </p>", unsafe_allow_html=True)
            #     cancel_button = st.button(label="Cancel & Back")

            with col2:
                update_button = st.button(label="Submit & Update", type="primary")

            if update_button: # Update everything in that specific Label element and show a successful msg
                st.cache_data.clear()
                labels[label_id].text = st.session_state.selected_label_name
                labels[label_id].rationale = st.session_state.selected_label_rationale
                labels[label_id].is_validated = True
                labels[label_id].decision = st.session_state.selected_label_decision
                if st.session_state.selected_label_decision != decision_options[2]: # reject
                    labels[label_id].is_selected = True
                    labels[label_id].rejection = None # if someone switches to selecting again
                else:
                    labels[label_id].is_selected = False
                    labels[label_id].rejection = st.session_state.selected_label_rejection
                st.success("We successfully updated the clicked label with your decision & feedback. Please continue the process with the next label. ")
                st.rerun()
        else: # if human-generated
            # Update Decision
            st.markdown(f"""<h3>Your Own Label: <b style="color:magenta">{st.session_state.selected_label_name}</b> </h3>""", unsafe_allow_html=True)
            flag_manual_update = None
            decision_options = ["Keep", "Modify and Keep", "Remove"]
            
            curr_idx = decision_options.index(st.session_state.selected_label_decision) if st.session_state.selected_label_decision is not None else 0
            feedback_mode = st.radio(label="This is the label you added. What is your decision for this label?", index=curr_idx,
                                    on_change=_update_label_decision, args=(st.session_state.selected_label_decision,),
                                options=decision_options, 
                                help="""If you would like to keep this label as you think this is an essential concept of revision in your domain writing, 
                                please click Keep. If you would like to modify a part of them and keep, please click Modify and Keep. 
                        Otherwise, please click Remove if you no longer think this is an essential property of your domain writing.""")
            
            if feedback_mode != st.session_state.selected_label_decision:
                st.session_state.selected_label_decision = feedback_mode
            
            if feedback_mode == decision_options[1]:
                flag_manual_update = False
                st.info("Please update the two inputs with your feedback and/or suggestions.")
            else:            
                flag_manual_update = True
        
            # Update Label Name with expert feedback
            current_label_name = st.text_input(label="Label Name", value=label_name, disabled=flag_manual_update,
                        on_change=_update_label_name, args=(st.session_state.selected_label_name,))
            
            if current_label_name != st.session_state.selected_label_name:
                st.session_state.selected_label_name = current_label_name

            # Update Label Rationale with expert feedback
            current_label_rationale = st.text_area(label="Rationale Behind This Label", value=label_rationale, disabled=flag_manual_update,
                        on_change=_update_label_rationale, args=(st.session_state.selected_label_rationale,))
            
            if current_label_rationale != st.session_state.selected_label_rationale:
                st.session_state.selected_label_rationale = current_label_rationale

            col1, col2 = st.columns([3.2,1])

            with col1:
                st.markdown("<p> Click Submit & Update only if you are done with your decision. </p>", unsafe_allow_html=True)

            with col2:
                update_button = st.button(label="Submit & Update", type="primary")

            if update_button: # Update everything in that specific Label element and show a successful msg
                st.cache_data.clear()
                labels[label_id].text = st.session_state.selected_label_name
                labels[label_id].rationale = st.session_state.selected_label_rationale
                labels[label_id].is_validated = True
                labels[label_id].decision = st.session_state.selected_label_decision
                if st.session_state.selected_label_decision != decision_options[2]:
                    labels[label_id].is_selected = True
                else:
                    labels[label_id].is_selected = False # Reject
                    labels[label_id].rejection = st.session_state.selected_label_rejection
                st.success("We successfully updated the clicked label with your decision & feedback. Please continue the process with the next label. ")
                st.rerun()            
        
    # ---> Here it starts
    st.markdown("<h2> 🧐 Validate AI-generated Labels </h2> <br>", unsafe_allow_html=True)
    
    cache_label_key = f"{domain}_{purpose}_{user_id}_labels"
    if cache_label_key in st.session_state:
        show_pane, _, validate_pane = st.columns([2.2, 0.5, 3]) 
        with show_pane:
            _show_pane_page(st.session_state[cache_label_key])
            st.markdown("<br>",  unsafe_allow_html=True)
            _insert_your_own(st.session_state[cache_label_key])

        with validate_pane:
            _validate_pane_page(st.session_state[cache_label_key])
            # st.write(st.session_state[cache_label_key][st.session_state.selected_label_id])

        st.markdown(f"""
                    <hr>
                    <br>
                    <h5> Click the button 'Complete STEP 2' once you validate all suggested labels. </h5>
                    """, unsafe_allow_html=True)
        
        if st.button('💾 Complete STEP 2', type="primary"):
            label_key = f"{st.session_state.domain}_{st.session_state.purpose}_{st.session_state.user_id}_labels"
            if len([label for label in st.session_state[label_key] if label.is_validated==True]) == len(st.session_state[label_key]):
                st.session_state.is_step2_complete = True
                st.success("We succesfully received your feedback. Please go to the next page STEP 3.")
                if f'dict_{label_key}' not in st.session_state:
                    st.session_state[f"dict_{label_key}"] = None
                st.session_state[f"dict_{label_key}"] = [elem.__dict__ for elem in st.session_state[label_key]]
                store_every_responses(st.session_state)
            else:
                st.error("You did not complete validation. Please go back to the above labels and make sure to validate every of them.")
                st.error(f"Here are the labels that you have not validated: {[label.text for label in st.session_state[label_key] if label.is_validated !=True]}")
    else:
        st.error("You have not confirmed the information above and generated the labels. Pleae complete the above section.")
    

    
if __name__ == "__main__":

    st.set_page_config(
        page_title='STEP 2: Generate Labels with AI!',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    step2_essential_properties = ['selected_label_id', 'selected_label_name', 'selected_label_rationale', 'selected_label_decision', 'selected_label_gpt', 
                                  'selected_label_rejection', 'is_step2_complete']
    for prop in step2_essential_properties:
        if prop not in st.session_state:
            st.session_state[prop] = None

    if ('is_step1_complete' in st.session_state) and (st.session_state.is_step1_complete):
        st.cache_data.clear()
        step2_instruction()
        step2_confirm_input()
        # st.write(st.session_state)
    else:
        st.error("You did not complete STEP 1. Please go back to STEP 1 page.")
