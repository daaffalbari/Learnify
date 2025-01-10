import streamlit as st
import requests
import time

# Initialize session state
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if "units" not in st.session_state:
    st.session_state["units"] = ["Beginner", "Real World Implementation"]

if "generated_course" not in st.session_state:
    st.session_state["generated_course"] = None

if "generated_content" not in st.session_state:
    st.session_state["generated_content"] = None

if "responses" not in st.session_state:
    st.session_state["responses"] = {}

if "submitted" not in st.session_state:
    st.session_state["submitted"] = {}

# Page: Home
if st.session_state["page"] == "home":
    st.title("Your Assistant Study Buddy 🧑‍🎓")  
    st.subheader("Enter a course Main Topics and Sub Topics:")
    st.divider()

    # Input for course title
    course_title = st.text_input("Topics", "Generative AI")

    # Dynamic form for units
    for i in range(len(st.session_state["units"])):
        unit_name = st.session_state["units"][i]
        st.session_state["units"][i] = st.text_input(f"Sub Topics {i+1}", unit_name, key=f"unit_{i}")
        if st.button(f"Remove Sub topics {i+1}", key=f"remove_{i}"):
            del st.session_state["units"][i]

    # Button to add new unit
    if st.button("Add Sub Topics"):
        st.session_state["units"].append("")

    # API payload
    data_payload = {
        "title": course_title,
        "units": st.session_state["units"]
    }

    # Fire up button
    if st.button("Fire up! 🚀"):
        response = requests.post("http://localhost:8000/generate-chapter", json=data_payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                st.session_state["generated_course"] = result.get("data")
                st.session_state["course_title"] = course_title
                st.session_state["page"] = "results"
            else:
                st.error("Failed to generate course.")
        else:
            st.error(f"API call failed with status code {response.status_code}.")

# Page: Results
elif st.session_state["page"] == "results":
    st.title("Generated Course Structure 📚")
    st.write(f"### {st.session_state['course_title']}")
    st.write("---")

    # Display units and chapters
    for unit_index, unit in enumerate(st.session_state["generated_course"]["units"], start=1):
        with st.expander(f"Course {unit_index}: {unit['title']}", expanded=True):
            for chapter_index, chapter in enumerate(unit["chapters"], start=1):
                st.markdown(f"**Chapter {chapter_index}: {chapter['chapter_title']}**")

    # Buttons: Back to Home and Generate All Content

    if st.button("Back to Home"):
        st.session_state["page"] = "home"
        st.session_state["generated_course"] = None

    if st.button("Generate All Course Content 🚀"):
            with st.spinner('Generating Course Content...'):
                progress_bar = st.progress(0)

                # Simulate progress
                time.sleep(0.5)
                progress_bar.progress(50)

                # API call to generate content
                all_chapters_payload = [
                    {"title": chapter['chapter_title'], "youtube_query": chapter['youtube_query']}
                    for unit in st.session_state["generated_course"]["units"]
                    for chapter in unit["chapters"]
                ]
                content_response = requests.post("http://localhost:8000/generate-content", json=all_chapters_payload)

                if content_response.status_code == 200:
                    content_result = content_response.json()
                    if content_result.get("status") == "success":
                        st.session_state["generated_content"] = content_result["data"]
                        st.success("Content generated successfully!")
                    else:
                        st.error("Failed to generate content.")
                else:
                    st.error(f"API call failed with status code {content_response.status_code}.")

                progress_bar.progress(100)
                time.sleep(0.5)

                

    # Display generated content if available
    if st.session_state["generated_content"]:
        content_index = 0
        for unit_index, unit in enumerate(st.session_state["generated_course"]["units"], start=1):
            with st.expander(f"Courses {unit_index}: {unit['title']}", expanded=True):
                for chapter_index, chapter in enumerate(unit["chapters"], start=1):
                    # Validasi indeks untuk menghindari error
                    if content_index >= len(st.session_state["generated_content"]):
                        st.error(f"Content for Chapter {chapter_index} is missing.")
                        continue
                    
                    # Ambil data konten chapter
                    chapter_data = st.session_state["generated_content"][content_index]
                    # st.write("chapter_data", chapter_data)
                    content_index += 1  # Tingkatkan indeks setelah digunakan

                    # Tampilkan judul chapter
                    chapter_title_generated = chapter_data.get("chapter_title", "Untitled Chapter")
                    st.markdown(f"**Chapter {chapter_index}: {chapter['chapter_title']}**")
                    st.markdown(f"### Title: {chapter_title_generated}")

                    # Tampilkan video YouTube
                    youtube_link = chapter_data.get("youtube_link")
                    if youtube_link:
                        st.markdown("#### Video")
                        st.video(youtube_link)
                    else:
                        st.markdown("_No video available for this chapter._")

                    # Tampilkan ringkasan
                    st.markdown("#### Summary")
                    summary = chapter_data.get("summary", "No summary available")
                    st.write(summary)

                    # Tampilkan Concept Check jika tersedia
                    concept_check = chapter_data.get("concept_check", [])
                    if concept_check:
                        st.markdown("#### Concept Check")
                        chapter_key = f"{unit_index}_{chapter_index}"
                        
                        # Inisialisasi state responses
                        if chapter_key not in st.session_state["responses"]:
                            st.session_state["responses"][chapter_key] = {}

                        # Iterasi pertanyaan
                        for q_index, question in enumerate(concept_check, start=1):
                            st.markdown(f"**Question {q_index}: {question['question']}**")
                            options = [
                                question['answer']['option1'],
                                question['answer']['option2'],
                                question['answer']['option3'],
                                question['answer']['option4']
                            ]
                            user_answer = st.radio("Select your answer:", options, key=f"radio_{chapter_key}_{q_index}")
                            true_answer = question['answer']['true_answer']
                            st.session_state["responses"][chapter_key][q_index] = (user_answer, true_answer)

                        # Tombol Submit untuk Concept Check
                        if st.button('Submit', key=f'submit_{chapter_key}'):
                            st.session_state["submitted"][chapter_key] = True

                        # Tampilkan hasil jika sudah disubmit
                        if st.session_state["submitted"].get(chapter_key, False):
                            st.subheader("Quiz Results")
                            score = sum(
                                1 for _, (response, true_answer) in st.session_state["responses"][chapter_key].items()
                                if response == true_answer
                            )
                            st.write(f'Your Score: {score}/{len(concept_check)}')

                            # Tampilkan jawaban benar dan salah
                            st.markdown("#### Answers")
                            for q_index, question in enumerate(concept_check, start=1):
                                user_answer, true_answer = st.session_state["responses"][chapter_key][q_index]
                                st.markdown(f"**Question {q_index}: {question['question']}**")
                                st.markdown(f"Your Answer: {user_answer}")
                                st.markdown(f"Correct Answer: {true_answer}")

                        
