import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import json
from json.decoder import JSONDecodeError
import time
from loguru import logger

from taxonomy import Label, Example
from utils import hover_button, store_every_responses

# load_dotenv()
openai_api_key = 'your own key'
client = OpenAI(api_key=openai_api_key)

@logger.catch
def step3_instruction():
 
    # Instruction
    st.markdown('<h2> STEP 3: Generate Examples with AI! </h2>', unsafe_allow_html=True)
    st.info("""INFO: The elements 'Example' will be the objects of the conceptualized dimensions ('Labels') of your taxonomy.""")
    step3_instruction_text = """ 
    <h2> 👉🏻 Instruction </h2>
    <ol>
        <li> Under <b> ✅ Generate Examples </b>, click each of the label buttons and confirm your inputs from STEP 2, and click <b> 🤖 Confirm and Generate Examples </b>. </li>
        <li> Under <b> 🧐 Validate AI-generated Examples </b>, you will see tabs of generated examples. 
        <ul> 
            <li> For each tab, you will see an individual example of the three AI-generated outputs: (1) the original sentence; (2) the revised sentence; and (3) the context of this revision. </li>
            <li> Please click each tab to validate the AI-generated example and its corresponding context description. </li>
        </ul>
        <li> If you find there is a missing example of revision for the selected label that is highly essential in your occupation domain, please click <b> Add Your Own Examples </b>. 
        After closing the window, you will see the example added to the tabs. </li>
    </ol>
    """
    st.markdown(step3_instruction_text, unsafe_allow_html=True)
    st.warning("Warning: DO NOT REFRESH the page unless you want to restart everything from beginning.")
    st.divider()

@logger.catch
def step3_confirm_labels(labels: list):

    def _label_click(label: Label):
        st.session_state.selected_label_id = label.id
        st.session_state.selected_label_name = label.text 
        st.session_state.selected_label_rationale = label.rationale
    
    if "confirm_label_clicked" not in st.session_state:
        st.session_state.confirm_label_clicked = False

    st.markdown("<h3> ✅ Generate Examples </h3>", unsafe_allow_html=True)
    st.write("Here is a list of the chosen labels of your taxonomy. Please click each label button and generate its regarding examples.")
    
    hover_button()
    num_columns=2
    with st.container(border=True):            
        # Create columns inside the styled container
        columns = st.columns(num_columns)
        for index, label in enumerate(labels):
            with columns[index % num_columns]:
                st.button(label=label.text, on_click=_label_click, args=[label])

    # entire container 
    with st.container(border=True):
        # st.write('dd', st.session_state.step3_initial_index)
        if st.session_state.step3_initial_index is None:
            st.markdown(f"""<h5> Here is the name and rationale of <b style="color:blue"> {labels[0].text} </b>. </h5>""", unsafe_allow_html=True)
            st.markdown(f'<b> The Label Name </b>: {labels[0].text}', unsafe_allow_html=True)
            st.markdown(f'<b> The Rationale </b>: {labels[0].rationale}', unsafe_allow_html=True)
            st.session_state.step3_initial_index = True
        else:
            st.markdown(f"""<h5> Here is the name and rationale of <b style="color:blue"> {st.session_state.selected_label_name} </b>. </h5>""", unsafe_allow_html=True)
            st.markdown(f'<b> The Label Name </b>: {st.session_state.selected_label_name}', unsafe_allow_html=True)
            st.markdown(f'<b> The Rationale </b>: {st.session_state.selected_label_rationale}', unsafe_allow_html=True)
        
    
    click_confirm_label = st.button("🤖 Confirm and Generate Examples", type="primary")
    if click_confirm_label:
        st.session_state.confirm_label_clicked = True
        with st.status("Generating Examples with GPT-4...", expanded=True) as example_gen_status:
            st.write("Connecting to GPT-4...")
            st.write("Asking GPT-4 to generate...")
            st.write("Generating Now. Please Wait Until GPT-4 completes...")
            examples = generate_examples(st.session_state.domain, st.session_state.purpose, 
                                        st.session_state.user_id, st.session_state.selected_label_id, 
                                        st.session_state.selected_label_name, st.session_state.selected_label_rationale)
            time.sleep(2)
            example_gen_status.update(label="Example Generation Complete!", state='complete', expanded=False)

    if st.session_state.confirm_label_clicked:
        st.divider()
        if f"{st.session_state.domain}_{st.session_state.purpose}_{st.session_state.user_id}_{st.session_state.selected_label_id}_examples" in st.session_state:
            step3_show_and_validate(st.session_state.domain, st.session_state.purpose, st.session_state.user_id, 
                                st.session_state.selected_label_id)
        else:
            st.error("You did not generate examples for this label. Click Confirm and Generate Examples First.")

@logger.catch            
@st.cache_data(show_spinner=False, persist="disk")
def generate_examples(domain, purpose, user_id, label_id, label_name, label_rationale):
    def _ask_gpt4_examples(domain, purpose, label_name, label_rationale):

        system_prompt = f"""You're a helpful assistant helping a user generate the examples of edit intentions in their writing task of {purpose}. 
                        The user is a business professional in the following domain: {domain}.
                        """
        with open('prompt_collection/generation/example_generation.txt', 'r') as f:
            example_prompt = f.read()
        f.close()

        input_prompt = f"""<label> {label_name}\n\n<rationale> {label_rationale}      
                        """
        
        ### TO DO: Update Prompt for Example Generations ----->>>>>
        example_prompt = example_prompt.format(label_name, purpose, domain, purpose, purpose, domain, input_prompt)
        example_generation_prompt = client.chat.completions.create(model="gpt-4", 
                                                        messages = [{"role":"system", "content":system_prompt}, 
                                                                    {"role":"user", "content":example_prompt}], 
                                                        temperature = 0.8 
                                                        )
        example_response = example_generation_prompt.choices[0].message.content
        return example_response
        ### ------>>>>>>>
    
    cache_key = f"{domain}_{purpose}_{user_id}_{label_id}_examples"

    if cache_key in st.session_state:
        return st.session_state[cache_key]
    else:
        # Just in case the example generation makes JSON decoding error
        gpt4_taxo_examples = _ask_gpt4_examples(domain, purpose, label_name, label_rationale)
        try:    
            gpt4_taxo_examples = json.loads(gpt4_taxo_examples)
            print('success')
        except JSONDecodeError as e:
            gpt4_taxo_examples = _ask_gpt4_examples(domain, purpose, label_name, label_rationale)
            gpt4_taxo_examples = json.loads(gpt4_taxo_examples)
            print('here this blank error will come')
        except:
            st.error('Something weird happens. Please try generating examples again.')


        example_buttons = []
        for i, example in enumerate(gpt4_taxo_examples):
            example_buttons.append(Example(id=i, original=example['Original'], revised=example['Revised'], context=example['Context'], 
                                        label_id=label_id, decision=None, is_gpt=True))

        # Cache the generated labels in the session state
        st.session_state[cache_key] = example_buttons
        return example_buttons    

@logger.catch
def step3_show_and_validate(domain, purpose, user_id, label_id):

    def _insert_your_own(examples:list):
        with st.popover("Add Your Own Examples", use_container_width=False):
            st.markdown("<h4> Create a new example </h4>", unsafe_allow_html=True)

            new_label_original = st.text_area("What is the original text of a new example you would like to add?", 
                                               placeholder="e.g., We have seen an increase in profit this quarter. (in Finance domain, for example)")
            new_label_revised = st.text_area("What is the revised text of the above original sentence?", 
                                             placeholder="e.g., We have seen an increase in profit this quarter, backed by our robust risk management policies that have helped us navigate market uncertainties.")
            new_label_context = st.text_area("Why do you want to revise like this?", 
                                             placeholder="In the revised text, the professional is attributing the increase in profits to their risk management policies, indicating their important role in mitigating risks.",
                                            height=200)
            
            if st.button("Add"):
                if (new_label_original != "") and (new_label_revised != "") and (new_label_context != ""):
                    end_examples_idx = len(examples)
                    examples.append(Example(id=end_examples_idx, original=new_label_original, revised=new_label_revised, context=new_label_context, 
                                        label_id=label_id, decision=None, is_gpt=False))
                    st.success("We successfully added this example to be validated. Please close this window and go back to the validation section.")
                else:
                    st.error("You did not provide responses to all three questions. Please fill out all of them and retry. Otherwise, close the window.")    
    
    def _example_click(example: Example):
        st.session_state.selected_example_id = example.id
        st.session_state.selected_example_original = example.original
        st.session_state.selected_example_revised = example.revised
        st.session_state.selected_example_context = example.context
        st.session_state.selected_example_label = example.label_id
        st.session_state.selected_example_decision = example.decision 
        st.session_state.selected_example_gpt = example.is_gpt
        st.session_state.selected_example_rejection = example.rejection

    def _update_example_revised(revised: str):
        st.session_state.selected_example_revised = revised

    def _update_example_context(example: str):
        st.session_state.selected_example_context = example
    
    def _update_example_decision(decision:str):
        st.session_state.selected_example_decision = decision

    def _update_example_rejection(rejection:str):
        st.session_state.selected_example_rejection = rejection

    def _validate_pane_page(examples: list): # st.session_state[cache_key_example]
        example_id = st.session_state.selected_example_id
        example_original = st.session_state.selected_example_original
        example_revised =  st.session_state.selected_example_revised
        example_context = st.session_state.selected_example_context
        example_gpt = st.session_state.selected_example_gpt
        example_label = st.session_state.selected_example_label
        example_rejection = st.session_state.selected_example_rejection

        decision_example_options = ["Keep", "Modify and Keep", "Remove"] if not example_gpt else ["Accept GPT-4 Suggestions", "Accept but Manual Modification", "Reject"]
        decision_help = """If you entirely agree with the three outputs, please click Accept GPT-4 Suggestions. 
                        If you agree with them but would like to modify a part of them, please click Accept but Manual Modifications. 
                        Otherwise, please click Reject.""" if example_gpt else """If you would like to keep this label as you think this is an essential concept of revision in your domain writing, 
                                please click Keep. If you would like to modify a part of them and keep, please click Modify and Keep. 
                        Otherwise, please click Remove if you no longer think this is an essential property of your domain writing."""
        
        flag_example_update = True
        example_sentence = f"<h5> Selected GPT-4 Example: <b style=\"color:blue\">{st.session_state.selected_example_original}</b></h5>" if example_gpt else f"<h5> Your Own Example: <b style=\"color:magenta\">{st.session_state.selected_example_original}</b></h5>"
        st.markdown(example_sentence, unsafe_allow_html=True)
        st.markdown("""Please read the example and its context below thoroughly. """)


        curr_idx = decision_example_options.index(st.session_state.selected_example_decision) if st.session_state.selected_example_decision is not None else 0
        feedback_example_mode = st.radio(label="What is your decision for this example?", index=curr_idx,
                                on_change=_update_example_decision, args=(st.session_state.selected_example_decision,),
                            options=decision_example_options, key=f"{example_label}_example_decision_{example_id}", 
                            help=decision_help)
        
        if feedback_example_mode != st.session_state.selected_example_decision:
            st.session_state.selected_example_decision = feedback_example_mode
        
        if feedback_example_mode == decision_example_options[1]:
            flag_example_update = False
            st.info("Please update the two inputs with your feedback and/or suggestions.")
        else:
            flag_example_update = True

        # Update Revised Example with Expert Feedback
        current_example_original = st.text_area(label="Original Sentence", value=example_original, disabled=True, key=f"{example_label}_example_original_{example_id}")
        current_example_revised = st.text_area(label="Revised Sentence", value=example_revised, disabled=flag_example_update,
                    on_change=_update_example_revised, args=(st.session_state.selected_example_revised,), key=f"{example_label}_example_revised_{example_id}")
        
        if current_example_revised != st.session_state.selected_example_revised:
            st.session_state.selected_example_revised = current_example_revised

        # Update Revision context with expert feedback
        current_example_context = st.text_area(label="Context of This Revision", value=example_context, disabled=flag_example_update,
                    on_change=_update_example_context, args=(st.session_state.selected_example_context,), key=f"{example_label}_example_context_{example_id}")
        
        if current_example_context != st.session_state.selected_example_context:
            st.session_state.selected_example_context = current_example_context


        # Collect Why Reject GPT-4 suggestion?
        if example_gpt and feedback_example_mode == decision_example_options[2]:
            current_example_rejection = st.text_area(label="Why do you reject this AI-generated example? Please write 2-3 sentences that are very clear and specific to your domain.", 
                                                     value=example_rejection, 
                                                     on_change=_update_example_rejection, args=(st.session_state.selected_example_rejection,), 
                                                     height=150, help="e.g., this example is too general to be specific example for the marketing domain-style revision.", 
                                                     key=f"{example_label}_example_rejection_{example_id}")
            if current_example_rejection != st.session_state.selected_example_rejection:
                st.session_state.selected_example_rejection = current_example_rejection
        
        st.markdown("<p> Click Submit & Update only if you are done with your decision. </p>", unsafe_allow_html=True)
        update_button = st.button(label="Submit & Update", type="primary", key=f"{example_label}_example_submit_{example_id}")

        if update_button: # Update everything in that specific Label element and show a successful msg
            st.cache_data.clear()
            examples[example_id].revised = st.session_state.selected_example_revised
            examples[example_id].context = st.session_state.selected_example_context
            examples[example_id].label_id = st.session_state.selected_label_id
            examples[example_id].decision = st.session_state.selected_example_decision
            examples[example_id].is_validated = True
            if st.session_state.selected_example_decision != decision_example_options[2]:
                examples[example_id].is_selected = True 
                examples[example_id].rejection = None # revert to None if selected
            else:
                examples[example_id].is_selected = False
                if st.session_state.selected_example_decision == 'Reject': # if rejecting AI-generated example
                    examples[example_id].rejection = st.session_state.selected_example_rejection
            st.success("We successfully updated the clicked example with your decision & feedback. Please continue the process with the next label.")
            st.rerun()

        # st.write(st.session_state[cache_example_key][st.session_state.selected_example_id])
    
    def _tab_page(examples: list):
        if st.session_state.selected_example_id is None:
            st.session_state.selected_example_id = examples[0].id
            st.session_state.selected_example_original = examples[0].original
            st.session_state.selected_example_revised = examples[0].revised
            st.session_state.selected_example_context = examples[0].context
            st.session_state.selected_example_label = examples[0].label_id
            st.session_state.selected_example_decision = examples[0].decision
            st.session_state.selected_example_gpt = examples[0].is_gpt
            st.session_state.selected_example_rejection = examples[0].rejection

        if "status_updated_examples" not in st.session_state:
            st.session_state.status_updated_examples = []

        st.markdown(f"<h3> 🧐 Validate AI-generated Examples for <b style=\"color:blue\">{st.session_state.selected_label_name}</h3>", unsafe_allow_html=True)
        st.markdown("""<span style="padding-right: 700px"> </span> ✅ (Accepted); ❌  (Rejected); ❓ (Unvalidated) <br>""", unsafe_allow_html=True)

        _insert_your_own(examples)

        example_idx_lst = []
        for example in examples:
            if example.is_validated:
                emoji = "✅" if example.is_selected else "❌"
            else:
                emoji = "❓"
            example_idx_composed = f"{emoji} Example {example.id+1}"
            example_idx_lst.append(example_idx_composed)

        example_tabs = st.tabs(example_idx_lst)

        for i, t in enumerate(example_tabs):
            with t:
                _example_click(examples[i])
                if examples[i] not in st.session_state.status_updated_examples:
                    st.session_state.status_updated_examples.append(examples[i])
                _validate_pane_page(examples)
                # st.session_state[cache_example_key][st.session_state.selected_example_id]
    
    cache_example_key = f"{domain}_{purpose}_{user_id}_{label_id}_examples"
    _tab_page(st.session_state[cache_example_key])


if __name__ == "__main__":

    st.set_page_config(
        page_title='STEP 3: Generate Examples with AI!',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    step3_essential_properties = ['selected_example_id', 'selected_example_original', 'selected_example_revised', 'selected_example_context', 'selected_example_label',
                                  'selected_example_rejection', 'is_step3_complete', 'step3_initial_index']
    for prop in step3_essential_properties:
        if prop not in st.session_state:
            st.session_state[prop] = None
        
    if ('is_step2_complete' in st.session_state) and (st.session_state.is_step2_complete):
        st.cache_data.clear()
        # (1) only extract selected labels to generate their examples
        cache_labels_key = f"{st.session_state.domain}_{st.session_state.purpose}_{st.session_state.user_id}_labels"
        selected_cache_labels = [label for label in st.session_state[cache_labels_key] if label.is_selected==True]
        
        # (3) Run the functions
        step3_instruction()
        step3_confirm_labels(selected_cache_labels)

        st.markdown(f"""
                <hr>
                <br>
                <h5> Click the button 'Complete STEP 3' once you validate all suggested examples for every label. </h5>
                """, unsafe_allow_html=True)
    
        # (4) Complete STEP 3 of generating examples for selected labels
        if st.button('💾 Complete STEP 3', type="primary"):
            selected_labels_example_key = [key for key, _ in st.session_state.items() if (('examples' in key) and ('updated' not in key) and ('dict' not in key))]
            cache_labels_key = f"{st.session_state.domain}_{st.session_state.purpose}_{st.session_state.user_id}_labels"
            selected_cache_labels = [label for label in st.session_state[cache_labels_key] if label.is_selected==True]

            if len(selected_labels_example_key) == len(selected_cache_labels): # if generated examples for all selected labels
                if all([len([example for example in st.session_state[state_key] if example.is_validated==True]) == len(st.session_state[state_key]) for state_key in selected_labels_example_key]):
                    st.success("We succesfully received your feedback. Please go to the next page STEP 4.")
                    st.session_state.is_step3_complete = True
                    for state_key in selected_labels_example_key:
                        if f'dict_{state_key}' not in st.session_state:
                            st.session_state[f"dict_{state_key}"] = None 
                        st.session_state[f"dict_{state_key}"] = [elem.__dict__ for elem in st.session_state[state_key]]
                    store_every_responses(st.session_state)
                else: # there are some labels whose examples were not entirely validated
                    label_not_validated = []
                    for state_key in selected_labels_example_key:
                        if not all([example.is_validated for example in st.session_state[state_key]]):
                            label_not_validated.extend([label.text for label in selected_cache_labels if st.session_state[state_key][0].label_id == label.id])
                    st.error(f"Here are the labels whose examples are not fully validated: {label_not_validated}")
            else:
                st.error("You did not generate all examples. Please make sure to generate examples for every of the labels.")
            
    else:
        st.error("You did not complete STEP 2. Please go back to the previous page to generate labels first.")




