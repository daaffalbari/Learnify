import streamlit as st
import requests

# Set the API URL
api_url = "http://localhost:8000/chat"

# Function to communicate with the API
def chat_with_api(user_message):   
    payload = {
        "message": user_message,
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        return response.json() 
    except requests.RequestException as e:
        return {"error": str(e)}

# Set the title of the app
st.title("Buddy: Your Learning Assistant📚")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "home_page_run" not in st.session_state:
    st.session_state.home_page_run = False
if "welcome_message_shown" not in st.session_state:
    st.session_state.welcome_message_shown = False

# Function to handle the button click
def confirm_home_page():
    st.session_state.home_page_run = True

# Check if the home page has been run
if not st.session_state.home_page_run:
    # Display warnings
    st.warning('Anda harus menjalankan home page dulu.')  # "You must run the home page first."
    st.warning('Anda harus membuat konten untuk kursus Anda sebelum dapat mengobrol dengan asisten.')

    # Display the confirmation button
    if st.button("Apakah sudah menjalankan?"):  # "Have you already run it?"
        confirm_home_page()
else:
    # Home page has been run; proceed with the chat interface

    # Tampilkan pesan sambutan sekali saja
    if not st.session_state.welcome_message_shown:
        st.markdown("<h3 style='text-align: center;'>Apakah ada yang ingin saya bantu?</h3>", unsafe_allow_html=True)
        st.session_state.welcome_message_shown = True

    # Tampilkan pesan chat dari session state
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Tangkap input pengguna
    if prompt := st.chat_input("Apa yang ingin Anda diskusikan?"):
        # Tampilkan pesan pengguna
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Dapatkan respons asisten dari API
        response = chat_with_api(prompt)
        if "error" in response:
            answer = response["error"]
        else:
            answer = response.get("answer", "Maaf, terjadi kesalahan dalam memproses permintaan Anda.")

        # Tampilkan respons asisten
        st.chat_message("assistant").markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})