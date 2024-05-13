import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import json
from loguru import logger

def home_page():
    
    # Brief Introduction
    instruction_text = """ 
    <h2> 👋🏻 Welcome to our research! </h2>
    <p> The objective of this study is to let human experts collaborate with AI to create a taxonomy of writing intentions with, especially text revision, for your occupation domain. </p>
    """
    st.markdown(instruction_text, unsafe_allow_html=True)
    st.warning("Please carefully read the instruction below to ensure the quality of your work. ")
        
    # Post all instructions
    start_instruction()


def start_instruction():
    st.markdown("""
        <h2> 👉🏻 What consists of a taxonomy? </h2>
        <p> There are three layers of a hierarchical taxonomy that you will build with us: </p>
        <ul>
                <li> <b> (1) Label </b>: a concept of your taxonomy that represents the intentions of writing revisions </li>
                <li> <b> (2) Definition </b>: a brief description of the corresponding label that explains the intention </li>
                <li> <b> (3) Example </b>: the corresponding example of the label in the context of the definition </li>
        </ul>
        <p> You will be working on developing these three layers of the taxonomy in the same order. </p>        
        <h2>  👉🏻 What are the pages on the left sidebar? </h2>        
        <p> You will see several pages named 'STEP X' on the left side bar. Each page is developed to generate each layer of the taxonomy with GPT-4. 
            Please click the page of each STEP accordingly.</p>
        <ol>
            <li> STEP 1: You will provide domain-specific information as inputs to GPT-4. </li>
            <li> STEP 2: GPT-4 will generate labels of your taxonomy according to your inputs from STEP 1. Here, you will validate each of the generated labels and select ones that are indeed important and widely used in your domain. </li>
            <li> STEP 3: Based on the selected labels from STEP 2, GPT-4 will generate examples of each selected label. Similarly, you will validate every one of them and choose ones that are indeed important and widely used in your domain. </li>
            <li> STEP 4: Given the selected labels and the corresponding examples, GPT-4 will generate the definition of the label (based on the examples), or you may provide your own definition of the label.</li>
            <li> STEP 5: you will see a visualized taxonomy of writing revisions according to your selection of the generated three layers. </li>
        </ol>
      """, unsafe_allow_html=True)
    st.warning("WARNING: Don't refresh the page unless you want to restart everything from beginning. If you want to restart, visit Home page and refresh the page.")

    st.markdown("<hr><p> <b> Please only click the checkbox if you fully read and understand the instruction above. </b></p>", unsafe_allow_html=True)
    check_instruction = st.checkbox('I confirm that I have read all instructions above thoroughly and carefully.', value=st.session_state.confirm_home_instruction)
    if check_instruction:
        st.success("We received your consent that you have read all instructions carefully. Please go to the page \'STEP 1: Provide Your Input\'.")
        st.session_state.confirm_home_instruction = True

if __name__ == '__main__':

    logger.add('streamlit_log.log', level='DEBUG')

    st.set_page_config(
        page_title='TaxoGen: Create Your Domain Taxonomy with AI!',
        # layout='wide',
        initial_sidebar_state='expanded',
    )
    
    if 'confirm_home_instruction' not in st.session_state:
        st.session_state.confirm_home_instruction = False
        logger.debug('this is the start of logging.\n')
    
    home_page()
    st.cache_data.clear()