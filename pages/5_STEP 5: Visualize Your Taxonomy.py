import streamlit as st
from streamlit_react_flow import react_flow
from openai import OpenAI
import json
from loguru import logger

from utils import escape_latex_special_chars, store_every_responses

# load_dotenv()
openai_api_key = 'your own key'
client = OpenAI(api_key=openai_api_key)

@logger.catch
def step4_instruction():
 
    # Instruction
    st.markdown('<h2> STEP 5: Visualize Your Taxonomy </h2>', unsafe_allow_html=True)
    step4_instruction_text = """ 
        <p> In this step, we visualize your domain taxonomy of revision intentions based on the selected labels, definitions, and examples according to STEP 2-4. </p>
        """
    st.markdown(step4_instruction_text, unsafe_allow_html=True)
    st.warning("Warning: DO NOT REFRESH the page unless you want to restart everything from beginning.")

    state_session_in_dict = json.dumps(store_every_responses(st.session_state, is_server=False), indent=4)
    st.markdown("<h5> Note: please download JSON file of your taxonomy results in case you would like to store in your own computer. </h5>", unsafe_allow_html=True)
    st.download_button(label="Download JSON file of Your Taxonomy", data=state_session_in_dict, file_name="your_downloaded_taxonomy.json", mime="application/json")
    st.divider()

@logger.catch
def construct_taxonomy(domain:str, purpose:str, selected_labels:list, selected_examples:list):

    def _create_node(id, data, label_id, background, x, y):
        node = {"id": str(id), "data": {"label": data, "label_id": label_id}, "type": "input", "position":{"x": x, "y":y}, 
                  "style":{"background": background, "width":350, "fontSize": 15}}
        return node
         
    def _connect_two_nodes(source_node_id, target_node_id):
        edge_info = {"id": f"e{source_node_id}-{target_node_id}", "source":str(source_node_id), "target":str(target_node_id)}
        return edge_info
    
    flowstyles = {"height": 1000, "width": 2000}

    input_info = f"Revision Intentions of {domain} {purpose} Writing"
    input_node = {"id": str(0), "data": {"label": input_info}, "type": "input", "position":{"x": 0, "y":500}, "style":{"fontSize": 20}}
    
    node_lst = [input_node]

    label_node_lst = []
    definition_node_lst = []
    example_node_lst = []
    edge_lst = []
    
    # create all label nodes
    for i, label in enumerate(selected_labels):
        label_node_id = len(example_node_lst)+len(definition_node_lst)+i+1
        def_node_id = label_node_id+1
        label_node = _create_node(id=label_node_id, data=label.text, label_id = label.id, background='#d5ebea', x=300, y=150*(label_node_id+i+1))
        def_node = _create_node(id=def_node_id, data=label.definition, label_id = label.id, background='#ebd3f5', x=700, y=150*(label_node_id+i+1))
        label_node_lst.append(label_node)
        definition_node_lst.append(def_node)
        node_lst.extend(label_node_lst)
        node_lst.extend(definition_node_lst)

        edge_lst.append(_connect_two_nodes(label_node_id, def_node_id))

        that_examples = [ex for ex in selected_examples if ex.label_id == label.id]
        for j, that_ex in enumerate(that_examples):
            original_escaped = escape_latex_special_chars(that_ex.original)
            revised_escaped = escape_latex_special_chars(that_ex.revised)
            example_composed = f"\"{original_escaped}\" \n ➜ \"{str(revised_escaped)}\""
            example_node = _create_node(id=def_node_id+j+1, data=example_composed, label_id=that_ex.label_id, background='#f1f5d3', x=1200+j, y=150*(def_node_id+j+1))
            example_node_lst.append(example_node)
            node_lst.extend(example_node_lst)
            edge_lst.append(_connect_two_nodes(def_node_id, def_node_id+j+1))

        # edge_lst.extend([_connect_two_nodes(label_node["id"], example["id"]) for example in example_node_lst if example["data"]["label_id"] == label_node["data"]["label_id"]])
        

    # connect input node to all label nodes
        edge_lst.extend([_connect_two_nodes(0, label_node_id)])


    node_lst.extend(edge_lst)
    react_flow("taxonomy", elements=node_lst, flow_styles=flowstyles)
    st.session_state["composed_taxonomy_structure"] = node_lst



if __name__ == "__main__":

    st.set_page_config(
        page_title='STEP 5: Visualize Your Taxonomy!',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    step4_essential_properties = ['composed_taxonomy_structure']
    for prop in step4_essential_properties:
        if prop not in st.session_state:
            st.session_state[prop] = None
    
    if ('is_step4_complete' in st.session_state) and (st.session_state.is_step4_complete):
        # (1) only extract selected labels to generate their examples
        st.cache_data.clear() 
        cache_labels_key = f"{st.session_state.domain}_{st.session_state.purpose}_{st.session_state.user_id}_labels"
        selected_cache_labels = [label for label in st.session_state[cache_labels_key] if label.is_selected==True]

        # (2) only extract selected examples for each label
        selected_labels_example_key = [key for key, _ in st.session_state.items() if ('examples' in key) and ('updated' not in key) and ('dict' not in key)]
        selected_cache_examples = []
        for state_key in selected_labels_example_key:
            selected_cache_examples.extend([example for example in st.session_state[state_key] if example.is_selected==True])
        step4_instruction()
        st.markdown("<h3> Your Taxonomy in Flow Chart</h3>", unsafe_allow_html=True)
        st.markdown("<p> Confirm all the elements of labels, context, and examples present in the visualized taxonomy. If any of the element is incorrect and has not been updated, please go back. </p>", unsafe_allow_html=True)
        st.warning("If the visual is not shown, please click back to STEP 4 and revisit STEP 5 again.")
        with st.container(border=True, height=1000):
            construct_taxonomy(st.session_state.domain, st.session_state.purpose, selected_cache_labels, selected_cache_examples)
        # tree_visual(st.session_state.domain, st.session_state.purpose, selected_cache_labels, selected_cache_examples)
        
        st.markdown("<br><h5> Click Finalize Your Taxonomy if every information on the flow chart is correct. </h5>", unsafe_allow_html=True)
        if st.button('Finalize Your Taxonomy!', type="primary"):
            st.cache_data.clear() 
            store_every_responses(st.session_state, is_server=True)
            st.success("Successfully Finalized! Please go to Home page and make sure to refresh if you want to create a new taxonomy!")
    else:
        st.error("You did not complete the previous steps. Please complete all three steps first.")




