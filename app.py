import streamlit as st
from google.cloud import aiplatform
import pdfplumber
import google.generativeai as genai
import os

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(filename='chatbot_interactions.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


# Optional in cloud shell terminal:
# 1) Store API KEY in Secret Manager
#     gcloud secrets create MY_API_KEY --replication-policy="automatic"
#     echo -n "YOUR_API_KEY_VALUE" | gcloud secrets versions add MY_API_KEY --data-file=-

# Replace MY_API_KEY with a name for your secret and YOUR_API_KEY_VALUE with your actual API key.

# 2) Grant access to the secret:
#     gcloud secrets add-iam-policy-binding MY_API_KEY \
#     --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
#     --role="roles/secretmanager.secretAccessor"

# Replace YOUR_PROJECT_NUMBER with your actual project number.

# 3) When you deploy on Cloud Run (the three dots from the Artifact Registry, 
# in the options you can handle the secrets. Make sure that the service account in use 
# has granted the Secret Manager Secret Accessor permission)

# Set secret
genai.configure(api_key = os.environ.get('DEVFEST2024_API_KEY')) #here you should put the name of the API KEY you chose

# Function to extract text from PDF using pdfplumber
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Function to get a summary from Gemini-pro API
def summarize_text(text):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([f"Please summarize the following text:\n\n{text}"])  # Increase timeout
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

# Function to question PDF using Gemini-pro API
def question_text(text, question):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([f"Please answer the following question based on the provided text:\n\nText: {text}\n\nQuestion: {question}"])  # Increase timeout
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit app
def main():

    model = genai.GenerativeModel("gemini-1.5-flash")
    st.title("Travel Agency with Gemini")
      
    col1, col2 = st.columns([5,5], gap="small")
    with col1:
      # Ask a generic question
      st.header("What are your travel needs?")

      # Gemini uses 'model' for assistant; Streamlit uses 'assistant'
      def role_to_streamlit(role):
        if role == "model":
          return "assistant"
        else:
          return role

      # Add a Gemini Chat history object to Streamlit session state
      if "chat" not in st.session_state:
          st.session_state.chat = model.start_chat(history = [])

      # Create a container for chat messages
      chat_container = st.container()

      # Display chat messages from history above current input box
      with chat_container:
        for message in st.session_state.chat.history:
            with st.chat_message(role_to_streamlit(message.role)):
                st.markdown(message.parts[0].text)
        message_placeholder = st.empty()

      # Accept user's next message, add to context, resubmit context to Gemini
      if prompt := st.chat_input("Time to ask a question to plan your travel"):

          # Display user's last message
          with chat_container:
            st.chat_message("user").markdown(prompt)
          # Send user entry to Gemini and read the response
          response = st.session_state.chat.send_message(prompt)
          
          # Display last 
          with chat_container:
            with st.chat_message("assistant"):
                st.markdown(response.text)

    # Ask about a PDF content
    with col2:
      st.header("Ask questions to your PDF of travel")

      uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
      
      
      if uploaded_file is not None:
          # Extract text from the uploaded PDF
          text = extract_text_from_pdf(uploaded_file)

          # Limit the text displayed to 500 characters
          display_text = text[:500] + ('...' if len(text) > 500 else '')
          
          # Display the extracted text
          st.subheader("Extracted Text")
          st.text_area("Text from PDF", display_text, height=300)

          # Get a summary
          if st.button("Get Summary"):
              summary = summarize_text(text)
              st.subheader("Summarize it!")
              st.write(summary)

          # Ask a question
          question = st.text_input("Enter your question about the text")
          if st.button("Ask!"):
              if question:
                  answer = question_text(text, question)
                  st.subheader("Answer")
                  st.write(answer)
              else:
                  st.warning("Please enter a question, we can't read your mind (yet).")

if __name__ == "__main__":
    main()