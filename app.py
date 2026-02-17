from openai import OpenAI
import streamlit as st
import time
from streamlit_js_eval import streamlit_js_eval


st.set_page_config(page_title="Your HR Agent", page_icon=":robot_face:")
st.title("Job Interview Simulator :briefcase: :robot_face:")




if "onboarded" not in st.session_state:
    st.session_state["onboarded"] = False

if "user_message_count" not in st.session_state:
    st.session_state["user_message_count"] = 0

if "feedback_shown" not in st.session_state:
    st.session_state["feedback_shown"] = False

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chat_completed" not in st.session_state:
    st.session_state["chat_completed"] = False


if "name" not in st.session_state:
    st.session_state["name"] = ""

if "experience" not in st.session_state:
    st.session_state["experience"] = ""

if "skills" not in st.session_state:
    st.session_state["skills"] = ""

if "level" not in st.session_state:
    st.session_state["level"] = "Junior"

if "position" not in st.session_state:
    st.session_state["position"] = ""

if "company" not in st.session_state:
    st.session_state["company"] = ""

if "job_description" not in st.session_state:
    st.session_state["job_description"] = ""

def onboard():
    st.session_state["onboarded"] = True

def show_feedback():
    st.session_state["feedback_shown"] = True
    st.info(f"""Thank you for completing the interview, {st.session_state['name']}! Based on your experience and skills, 
            and our conversation, we will provide feedback on your suitability for the {st.session_state['level']} 
            {st.session_state['position']} position at {st.session_state['company']}. Please wait a moment while we generate your feedback.""")

if not st.session_state["onboarded"]:
    
    st.subheader("Personal Information", divider="rainbow")
    st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], max_chars=40, placeholder="Enter your name")
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", height=None, max_chars=200)
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", height=None, max_chars=200)  


    st.subheader("Company & Position", divider="rainbow")
    
    st.session_state["company"] = st.text_input(label="Select company", value=st.session_state["company"], max_chars=40, placeholder="Enter the company name")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.selectbox(
                                label="Choose level",
                                options=["Junior", "Mid", "Senior", "Lead"],
                                index=0
                            )
    with col2:
        st.session_state["position"] = st.text_input(label="Position", value=st.session_state["position"], 
                                                    max_chars=40, placeholder="Enter the position you are applying for")

    st.session_state["job_description"] = st.text_area(label="Job Description", value=st.session_state["job_description"], placeholder="Enter the job description", height=None, max_chars=200)

    if st.button("Start Interview"):
        onboard()


if st.session_state["onboarded"] and not st.session_state["feedback_shown"] and not st.session_state["chat_completed"]:

    st.info(f"""Welcome {st.session_state['name']}! You are interviewing for 
            a {st.session_state['level']} {st.session_state['position']} position 
            at {st.session_state['company']}. :wave: Lets start by introducing yourself""")

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4.1-mini"


    if not st.session_state["messages"]:
        st.session_state["messages"] = [
            {"role": "system", "content": f"""You are an HR executive at {st.session_state['company']} interviewing a candidate for a 
            {st.session_state['level']} {st.session_state['position']} position. The candidate's name is {st.session_state['name']}. They have the following experience:'
            ' {st.session_state['experience']}. They have the following skills: {st.session_state['skills']}. The job description is: {st.session_state['job_description']}. Ask them questions about their experience'
            ' and skills, and provide feedback on their suitability for the position."""}
        ]

    for message in st.session_state["messages"]:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state["user_message_count"] < 5 and not st.session_state["feedback_shown"]:
        if prompt := st.chat_input("Enter your message here...", max_chars=1000):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            if st.session_state["user_message_count"] < 4:
                with st.chat_message("assistant"):
                    response_container = st.empty()

                    with client.responses.stream(
                        model=st.session_state.openai_model,
                        input = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state["messages"]
                        ]) as stream:

                        full_response = ""
                    
                        for event in stream:
                            if event.type == "response.output_text.delta":
                                full_response += event.delta
                                response_container.markdown(full_response + "▌")
                                time.sleep(0.01)  # tiny pause helps visible streaming

                        stream.get_final_response()
                    response_container.markdown(full_response)
                        
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            st.session_state["user_message_count"] = st.session_state["user_message_count"] + 1

    if st.session_state["user_message_count"] >= 5:
        st.session_state["chat_completed"] = True
        

if st.session_state["chat_completed"] and not st.session_state["feedback_shown"]:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Getting Feedback...")


if st.session_state["feedback_shown"]:
    st.subheader("Feedback", divider="rainbow")
    conversation_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state["messages"]])
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    feedback_response = feedback_client.responses.create(
        model = st.session_state.openai_model,
        input = [
            {"role": "system", "content": f"""You are a helpful tool that provides feedback  on an interveeww performance.
             Before the feedback give a score of 1 to 10.
             Follow this format:
             Overall Score: [score out of 10]
             Feedback: [detailed feedback on the candidate's performance, strengths, and areas for improvement]
             Give only the score and feedback without any additional commentary.
             """},
             {"role": "user", "content": f"""This is the interview conversation you need to evaluate. You are only a tool and
              should not provide any personal opinions or additional commentary:\n{conversation_history}"""}
        ]
    )
    st.markdown(f"**Overall Score:** {feedback_response.output_text.split('Feedback:')[0].replace('Overall Score:', '').strip()}")
    st.markdown(f"**Feedback:** {feedback_response.output_text.split('Feedback:')[1].strip()}")

    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")