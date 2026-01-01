import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv

# No Docker usage needed for this app
os.environ["AUTOGEN_USE_DOCKER"] = "0"

# Load environment variables from .env
load_dotenv()

if 'output' not in st.session_state:
    st.session_state.output = {
        'assessment': '',
        'action': '',
        'followup': ''
    }

api_key = os.getenv("GOOGLE_API_KEY", "")

# Sidebar status (do not prompt for key; just show status)
if api_key:
    st.sidebar.success("Gemini API key loaded from .env")
else:
    st.sidebar.error("Gemini API key not found in .env (GOOGLE_API_KEY)")

st.sidebar.warning("""
## ⚠️ Important Notice

This application is a supportive tool and does not replace professional mental health care. If you're experiencing thoughts of self-harm or severe crisis:

- Call National Crisis Hotline: 988
- Call Emergency Services: 911
- Seek immediate professional help
""")

st.title("🧠 Mental Wellbeing Agent")

st.info("""
**Meet Your Mental Wellbeing Agent Team:**

🧠 **Assessment Agent** - Analyzes your situation and emotional needs
🎯 **Action Agent** - Creates immediate action plan and connects you with resources
🔄 **Follow-up Agent** - Designs your long-term support strategy
""")

st.subheader("Personal Information")
col1, col2 = st.columns(2)

with col1:
    mental_state = st.text_area("How have you been feeling recently?", 
        placeholder="Describe your emotional state, thoughts, or concerns...")
    sleep_pattern = st.select_slider(
        "Sleep Pattern (hours per night)",
        options=[f"{i}" for i in range(0, 13)],
        value="7"
    )
    
with col2:
    stress_level = st.slider("Current Stress Level (1-10)", 1, 10, 5)
    support_system = st.multiselect(
        "Current Support System",
        ["Family", "Friends", "Therapist", "Support Groups", "None"]
    )

recent_changes = st.text_area(
    "Any significant life changes or events recently?",
    placeholder="Job changes, relationships, losses, etc..."
)

current_symptoms = st.multiselect(
    "Current Symptoms",
    ["Anxiety", "Depression", "Insomnia", "Fatigue", "Loss of Interest", 
     "Difficulty Concentrating", "Changes in Appetite", "Social Withdrawal",
     "Mood Swings", "Physical Discomfort"]
)

if st.button("Get Support Plan"):
    if not api_key:
        st.error("Gemini API key not found. Please add GOOGLE_API_KEY to your .env file.")
    else:
        with st.spinner('🤖 AI Agents are analyzing your situation...'):
            try:
                task = f"""
                Create a comprehensive mental health support plan based on:
                
                Emotional State: {mental_state}
                Sleep: {sleep_pattern} hours per night
                Stress Level: {stress_level}/10
                Support System: {', '.join(support_system) if support_system else 'None reported'}
                Recent Changes: {recent_changes}
                Current Symptoms: {', '.join(current_symptoms) if current_symptoms else 'None reported'}
                """

                system_messages = {
                    "assessment_agent": """
                    You are an experienced mental health professional speaking directly to the user. Your task is to:
                    1. Create a safe space by acknowledging their courage in seeking support
                    2. Analyze their emotional state with clinical precision and genuine empathy
                    3. Ask targeted follow-up questions to understand their full situation
                    4. Identify patterns in their thoughts, behaviors, and relationships
                    5. Assess risk levels with validated screening approaches
                    6. Help them understand their current mental health in accessible language
                    7. Validate their experiences without minimizing or catastrophizing

                    Always use "you" and "your" when addressing the user. Blend clinical expertise with genuine warmth and never rush to conclusions.
                    """,
                    
                    "action_agent": """
                    You are a crisis intervention and resource specialist speaking directly to the user. Your task is to:
                    1. Provide immediate evidence-based coping strategies tailored to their specific situation
                    2. Prioritize interventions based on urgency and effectiveness
                    3. Connect them with appropriate mental health services while acknowledging barriers (cost, access, stigma)
                    4. Create a concrete daily wellness plan with specific times and activities
                    5. Suggest specific support communities with details on how to join
                    6. Balance crisis resources with empowerment techniques
                    7. Teach simple self-regulation techniques they can use immediately

                    Focus on practical, achievable steps that respect their current capacity and energy levels. Provide options ranging from minimal effort to more involved actions.
                    """,
                    
                    "followup_agent": """
                    You are a mental health recovery planner speaking directly to the user. Your task is to:
                    1. Design a personalized long-term support strategy with milestone markers
                    2. Create a progress monitoring system that matches their preferences and habits
                    3. Develop specific relapse prevention strategies based on their unique triggers
                    4. Establish a support network mapping exercise to identify existing resources
                    5. Build a graduated self-care routine that evolves with their recovery
                    6. Plan for setbacks with self-compassion techniques
                    7. Set up a maintenance schedule with clear check-in mechanisms

                    Focus on building sustainable habits that integrate with their lifestyle and values. Emphasize progress over perfection and teach skills for self-directed care.
                    """
                }
                # Simple, reliable multi-step orchestration using Google Generative AI SDK
                genai.configure(api_key=api_key)

                def call_llm(system_prompt: str, user_task: str) -> str:
                    model = genai.GenerativeModel(
                        model_name="gemini-2.5-flash",
                        system_instruction=system_prompt,
                    )
                    resp = model.generate_content(user_task)
                    return getattr(resp, "text", "")

                # 1) Assessment
                assessment_context = ""  # No prior context
                assessment_prompt = (
                    system_messages["assessment_agent"]
                    + "\n\nWrite a concise assessment. Start with: '## Assessment'."
                )
                assessment = call_llm(assessment_prompt, task)
                st.sidebar.success("Assessment generated.")

                # 2) Action plan (use assessment as context)
                action_prompt = (
                    system_messages["action_agent"]
                    + "\n\nYou have access to the user's assessment below as context. Start with: '## Action Plan'.\n\nAssessment Context:\n"
                    + assessment
                )
                action_plan = call_llm(action_prompt, task)
                st.sidebar.success("Action plan generated.")

                # 3) Follow-up (use assessment + action as context)
                followup_prompt = (
                    system_messages["followup_agent"]
                    + "\n\nYou have access to the user's assessment and action plan below as context. Start with: '## Follow-up Strategy'.\n\nAssessment Context:\n"
                    + assessment
                    + "\n\nAction Plan Context:\n"
                    + action_plan
                )
                followup = call_llm(followup_prompt, task)
                st.sidebar.success("Follow-up strategy generated.")

                st.session_state.output = {
                    'assessment': assessment,
                    'action': action_plan,
                    'followup': followup,
                }

                with st.expander("Situation Assessment"):
                    st.markdown(st.session_state.output['assessment'])

                with st.expander("Action Plan & Resources"):
                    st.markdown(st.session_state.output['action'])

                with st.expander("Long-term Support Strategy"):
                    st.markdown(st.session_state.output['followup'])

                st.success('✨ Mental health support plan generated successfully!')

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
