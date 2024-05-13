import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import json
from json.decoder import JSONDecodeError
from loguru import logger

import time

from taxonomy import Label, Example
from utils import hover_button, store_every_responses

# load_dotenv()
openai_api_key = 'your own key'
client = OpenAI(api_key=openai_api_key)

@logger.catch
def definition_instruction():
 
    # Instruction
    st.markdown('<h2> STEP 4: Generate Definitions with AI! </h2>', unsafe_allow_html=True)
    st.info("""INFO: The elements 'Definition' will be the definition of the selected label based on your choice of examples in your taxonomy.""")
    step4_instruction_text = """ 
    <h2> 👉🏻 Instruction </h2>
    <ol>
        <li> Under <b> ✅ Generate Definitions </b>, click each of the label buttons and confirm your inputs from STEP 3, and click <b>🤖 Confirm and Generate Definitions</b>. </li>
        <li> Under <b> 🧐 Choose Your Preferred Definition </b>, you will see the three AI-generated candidates of the definition for the selected label. 
        <ul> 
            <li> If you would like to accept AI suggestions, click 'Choose GPT-4 Suggestions' and choose one among the given three candidates. </li>
            <li> If you don't like any of these three candidates and would like to provide your own definition, please click 'Provide My Own Definition' and write down the definition. </li>
        </ul>
    </ol>
    """
    st.markdown(step4_instruction_text, unsafe_allow_html=True)
    st.warning("Warning: DO NOT REFRESH the page unless you want to restart everything from beginning.")
    st.divider()

@logger.catch
def step4_confirm_all(labels: list, examples:list):

    def _label_click(label: Label):
        st.session_state.selected_label_id = label.id
        st.session_state.selected_label_name = label.text 
        st.session_state.selected_label_rationale = label.rationale
    
    if "confirm_label_clicked_step4" not in st.session_state:
        st.session_state.confirm_label_clicked_step4 = False

    st.markdown("<h3> ✅ Generate Definitions </h3>", unsafe_allow_html=True)
    st.write("Here is a list of the chosen labels of your taxonomy. Please click each label button to see the rationale and corresponding example contexts.")
    
    hover_button()
    num_columns=2
    with st.container(border=True):            
        # Create columns inside the styled container
        columns = st.columns(num_columns)
        for index, label in enumerate(labels):
            with columns[index % num_columns]:
                st.button(label=label.text, on_click=_label_click, args=[label])
    
    st.markdown(f"<br> <h5> Here is the information about the label <b style=\"color:red\">{st.session_state.selected_label_name}</b> of your taxonomy. </h5>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f'<b> The Label Name </b>: {st.session_state.selected_label_name}', unsafe_allow_html=True)
        st.markdown(f'<b> The Rationale </b>: {st.session_state.selected_label_rationale}', unsafe_allow_html=True)
        concatnated_example_context = ''
        gpt4_input_context = ''
        for example in examples:
            if example.label_id == st.session_state.selected_label_id:
                ex_context = f'<li> {example.context} </li>'
                concatnated_example_context += ex_context
                gpt4_ex_context = f'<context> {example.context} </context>\n'
                gpt4_input_context += gpt4_ex_context

        st.markdown(f'<b> The example context </b>: <ul> {concatnated_example_context}</ul>', unsafe_allow_html=True)
    
    if st.button("🤖 Confirm and Generate Definition", type="primary"):
        st.session_state.confirm_label_clicked_step4 = True
        with st.status("Generating Definition with GPT-4...", expanded=True) as def_gen_status:
            st.write("Connecting to GPT-4...")
            st.write("Asking GPT-4 to generate...")
            st.write("Generating Now. Please Wait Until GPT-4 completes...")
            defs = generate_definition(st.session_state.domain, st.session_state.purpose, 
                                        st.session_state.user_id, st.session_state.selected_label_id, 
                                        st.session_state.selected_label_name, gpt4_input_context)
            
            time.sleep(2)
            def_gen_status.update(label="Definition Generation Complete!", state='complete', expanded=False)

    if st.session_state.confirm_label_clicked_step4:
        st.divider()
        # retrieve all the generated definitions for this specific label id
        cache_def_key = f"{st.session_state.domain}_{st.session_state.purpose}_{st.session_state.user_id}_{st.session_state.selected_label_id}_definitions"
        if cache_def_key in st.session_state:
            # validation starts
            step4_show_and_validate(st.session_state.domain, st.session_state.purpose, st.session_state.user_id, 
                                st.session_state.selected_label_id, cache_def_key)
        else:
            st.error("You did not generate definitions for this label. Click Confirm and Generate Definitions First.")

@logger.catch            
@st.cache_data(show_spinner=False, persist="disk")
def generate_definition(domain, purpose, user_id, label_id, label_name, example_context):
    def _ask_gpt4_defs(domain, purpose, label_name, example_context):

        system_prompt = f"""You're a helpful assistant helping a user generate the definitions of edit intentions in their writing task of {purpose}. 
                        The user is a business professional in the following domain: {domain}. 
                        """
        with open('prompt_collection/generation/definition_generation.txt', 'r') as f:
            def_prompt_template = f.read()
        f.close()

        input_prompt = f"""<label>{label_name}</label>{example_context}"""
        
        def_prompt = def_prompt_template.format(purpose, domain, domain, purpose, domain, purpose, domain, domain, purpose, input_prompt)
        def_generation_prompt = client.chat.completions.create(model="gpt-4", 
                                                        messages = [{"role":"system", "content":system_prompt}, 
                                                                    {"role":"user", "content":def_prompt}], 
                                                        temperature = 0.8
                                                        )
        def_response = def_generation_prompt.choices[0].message.content
        return def_response
    
    cache_key = f"{domain}_{purpose}_{user_id}_{label_id}_definitions"

    if cache_key in st.session_state:
        return st.session_state[cache_key]
    else:
        gpt4_taxo_defs = _ask_gpt4_defs(domain, purpose, label_name, example_context)
        # Handling JSONDecodeError issues
        try:
            gpt4_taxo_defs = json.loads(gpt4_taxo_defs)
        except JSONDecodeError as e:
            gpt4_taxo_defs = _ask_gpt4_defs(domain, purpose, label_name, example_context) # rerun again
            gpt4_taxo_defs = json.loads(gpt4_taxo_defs)
        except:
            st.error("Something weird has happend. Please click generating definitions again.")

        defs_buttons = []
        for i, defi in enumerate(gpt4_taxo_defs):
            defi_dict = {'text': defi['summary'], 'label_id': label_id, 'is_gpt': True, 'is_selected':None}
            defs_buttons.append(defi_dict)

        # for user-generated definition
        defs_buttons.append({'text': None, 'label_id': label_id, 'is_gpt': False, 'is_selected':None})

        # Cache the generated labels in the session state
        st.session_state[cache_key] = defs_buttons
        return defs_buttons    

@logger.catch
def step4_show_and_validate(domain, purpose, user_id, label_id, generated_def_key):
    
    def _validate_pane_page(def_lst: list): # def_lst: st.session_state[cache_key_definition]
        
        # 1. Your feedback Mode
        if f"label_{label_id}_def_decision" not in st.session_state:
            st.session_state[f"label_{label_id}_def_decision"] = None

        if f'label_{label_id}_flag_def_update' not in st.session_state:
            st.session_state[f'label_{label_id}_flag_def_update'] = True
        
        label_sentence = f"<h5> Selected Label: <b style=\"color:blue\">{st.session_state.selected_label_name}</b></h5>"
        st.markdown(label_sentence, unsafe_allow_html=True)
        # # Q: What's your decision?
        decision_def_options = ["Choose GPT-4 Suggestions", "Provide My Own Definition"] 
        decision_curr_idx = decision_def_options.index(st.session_state[f"label_{label_id}_def_decision"]) if st.session_state[f"label_{label_id}_def_decision"] is not None else 0
        feedback_def_mode = st.radio(label="What is your decision for the definitions?", index=decision_curr_idx,
                            options=decision_def_options)

        if feedback_def_mode != st.session_state[f"label_{label_id}_def_decision"]:
            st.session_state[f"label_{label_id}_def_decision"] = feedback_def_mode

        # st.write("Decision: ", st.session_state[f"label_{label_id}_def_decision"])

        # # 2: Choose your definition
        if f"label_{label_id}_user_definition" not in st.session_state:
            st.session_state[f"label_{label_id}_user_definition"] = ""
        
        choose_gpt4_cache_key =  f"{domain}_{purpose}_{user_id}_{label_id}_definitions_selected_text"
        if choose_gpt4_cache_key not in st.session_state:
            st.session_state[choose_gpt4_cache_key] = None

        def_text_lst = [defi['text'] for defi in def_lst[:-1]]
        
        # # Q: What's your own definition?
        if feedback_def_mode == decision_def_options[1]: # provide your own
            st.session_state[f'{label_id}_flag_def_update'] = True
            st.info("Provide your definition of this label in a full, complete sentence.")
            
            # st.write(st.session_state[f"label_{label_id}_user_definition"])
            user_def = st.text_area(label="Provide Your Definition of this label in a 2-3 complete sentence.", 
                                    value=st.session_state[f"label_{label_id}_user_definition"],
                                    placeholder="""e.g., This refers to the replacement of informal or vague phrases with more formal and precise financial terms, 
                                    ensuring clear and professional communication. (Given that this label belongs to financial domain.)""")
            
            if user_def != st.session_state[f"label_{label_id}_user_definition"]:
                st.session_state[f"label_{label_id}_user_definition"] = user_def
            
            def_lst[-1]['text'] = st.session_state[f"label_{label_id}_user_definition"]
            # st.write(st.session_state[f"label_{label_id}_user_definition"])
        else:
            # # Q: What's your choice among the GPT-4 suggestions?
            st.session_state[f'{label_id}_flag_def_update'] = False
            st.info("Choose one defitinion among the three candidates below.")
            
            text_curr_idx = def_text_lst.index(st.session_state[choose_gpt4_cache_key]) if st.session_state[choose_gpt4_cache_key] is not None else 0
            def_lst_radio = st.radio(label="Choose among the three AI-generated candidates of definition", options=def_text_lst, label_visibility="collapsed",
                                    disabled=st.session_state[f'{label_id}_flag_def_update'], index=text_curr_idx)
            
            if def_lst_radio != st.session_state[choose_gpt4_cache_key]:
                st.session_state[choose_gpt4_cache_key] = def_lst_radio

            # st.write(st.session_state[choose_gpt4_cache_key])

        # 3. Update the decision
        # show_pane, submit_pane = st.columns([2.2, 0.5]) 
        # with show_pane:
        st.markdown("<br><br><b> Click Submit & Update only if you are done with your decision. </b>", unsafe_allow_html=True)
        # with submit_pane:
        if st.button(label="Submit & Update", type="primary", key=f"{label_id}_def_submit"):
            if st.session_state[f"label_{label_id}_def_decision"] == decision_def_options[0]: # if accept GPT-4
                # selected_gpt4_def_idx = def_text_lst.index(st.session_state[choose_gpt4_cache_key])
                # def_lst[selected_gpt4_def_idx]['is_selected'] = True
                if st.session_state[choose_gpt4_cache_key] is not None:
                    st.session_state[f"{domain}_{purpose}_{user_id}_labels"][label_id].definition = st.session_state[choose_gpt4_cache_key]
                    st.success("We succesfully updated your decision for the definition among the GPT-4 suggestions!")
                    st.cache_data.clear() 
                else:
                    st.error("You did not click any option among the GPT-4 suggestions. Please click one of the GPT-4 suggestions above and retry.")
            else: # if user-own
                st.session_state[f"{domain}_{purpose}_{user_id}_labels"][label_id].definition = st.session_state[f"label_{label_id}_user_definition"]
            
            # st.rerun()
            
    
    cache_def_key = f"{domain}_{purpose}_{user_id}_{label_id}_definitions"
    _validate_pane_page(st.session_state[cache_def_key])
    # st.write(st.session_state[cache_def_key])
    # st.write(st.session_state[f"{domain}_{purpose}_{user_id}_labels"][label_id])


if __name__ == "__main__":

    st.set_page_config(
        page_title='STEP 4: Generate Definitions with AI!',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    step4_essential_properties = ['is_step4_complete']
    for prop in step4_essential_properties:
        if prop not in st.session_state:
            st.session_state[prop] = None
        

    if ('is_step3_complete' in st.session_state) and (st.session_state.is_step3_complete):
        # (1) only extract selected labels to generate their examples
        cache_labels_key = f"{st.session_state.domain}_{st.session_state.purpose}_{st.session_state.user_id}_labels"
        selected_cache_labels = [label for label in st.session_state[cache_labels_key] if label.is_selected==True]
        selected_labels_example_key = [key for key, _ in st.session_state.items() if ('examples' in key) and ('updated' not in key) and ('dict' not in key)]
        selected_cache_examples = []
        for state_key in selected_labels_example_key:
            selected_cache_examples.extend([example for example in st.session_state[state_key] if example.is_selected==True])
        
        st.cache_data.clear() 
        definition_instruction()
        step4_confirm_all(selected_cache_labels, selected_cache_examples)

        st.markdown(f"""
                <br><br><hr>
                <h5> Please Click the button 'Complete STEP 4' once you choose all definitions for every label. </h5>
                """, unsafe_allow_html=True)
        
        if st.button('💾 Complete STEP 4', type="primary"):
            all_selected_definitions = [label.definition for label in selected_cache_labels]
            if all(label is not None for label in all_selected_definitions): # all checked and validated definitions
                st.success("You succesfully completed STEP 4 to generate definitions of all selected labels for your taxonomy. Please go to STEP 5.")
                st.session_state.is_step4_complete = True
                st.cache_data.clear()  
            else:
                st.error("You did not validate all definitions. Please make sure to generate the definition and click Submit & Update button for every label.")
    else:
        st.error("You did not complete STEP 3. Please go back to the previous page to generate examples first.")




