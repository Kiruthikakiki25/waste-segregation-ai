import asyncio
import nest_asyncio
nest_asyncio.apply()
import streamlit as st
import json
from agent import create_agent, run_agent

st.set_page_config(
    page_title="WasteWise",
    page_icon="♻️",
    layout="wide"
)

if "agent" not in st.session_state:
    st.session_state.agent = create_agent()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_waste" not in st.session_state:
    st.session_state.session_waste = {}

agent = st.session_state.agent

st.title("♻️ WasteWise")
st.caption("AI-powered waste segregation and recycler matching for Indian households")

tab1, tab2, tab3, tab4 = st.tabs([
    "Waste Advisor",
    "Recycler Matcher",
    "Value Estimator",
    "Impact Dashboard"
])

with tab1:
    st.subheader("AI Waste Advisor")
    st.write("Describe what waste you have. Example: *old phone, cardboard boxes, plastic bottles*")

    user_input = st.text_area("What waste do you have?", placeholder="e.g. old mobile phone, newspaper, plastic bottles", height=100)

    if st.button("Classify My Waste", type="primary"):
        if user_input.strip():
            with st.spinner("Analysing your waste..."):
                prompt = f"Please classify these waste items and give disposal instructions: {user_input}"
                try:
                    response = run_agent(agent, prompt)
                    st.session_state.chat_history.append({
                        "user": user_input,
                        "agent": str(response)
                    })
                    st.markdown("### Result")
                    st.markdown(str(response))
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
        else:
            st.warning("Please describe your waste items first.")

    if st.session_state.chat_history:
        st.divider()
        st.subheader("Previous Queries")
        for chat in reversed(st.session_state.chat_history[-3:]):
            with st.expander(f"You: {chat['user'][:60]}..."):
                st.markdown(chat["agent"])

with tab2:
    st.subheader("Recycler Matcher")
    st.write("Find nearby kabadiwalas and recyclers who accept your waste type.")

    col1, col2 = st.columns(2)
    with col1:
        waste_types = st.multiselect(
            "Select waste types",
            ["plastic", "paper", "cardboard", "metal", "ewaste", "glass"],
            default=["plastic"]
        )
    with col2:
        location_type = st.radio("Search by", ["City", "Pincode"])

    if location_type == "City":
        city = st.selectbox("Select city", ["Chennai", "Trichy", "Coimbatore", "Madurai"])
        pincode = ""
    else:
        pincode = st.text_input("Enter Pincode", placeholder="e.g. 620018")
        city = ""

    if st.button("Find Recyclers", type="primary"):
        if waste_types:
            with st.spinner("Finding recyclers near you..."):
                types_str = ", ".join(waste_types)
                prompt = f"Find recyclers in {city if city else pincode} who accept {types_str}"
                try:
                    response = run_agent(agent, prompt)
                    st.markdown("### Nearby Recyclers")
                    st.markdown(str(response))
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
        else:
            st.warning("Please select at least one waste type.")

with tab3:
    st.subheader("Fair Value Estimator")
    st.info("⚠️ These are indicative sample rates only — not verified live market prices.")

    col1, col2 = st.columns(2)
    with col1:
        waste_type = st.selectbox(
            "Waste type",
            ["plastic", "paper", "cardboard", "metal", "ewaste", "glass"]
        )
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.1, max_value=1000.0, value=1.0, step=0.5)

    st.markdown("**Current Sample Rates (INR/kg):**")
    rates = {"plastic": 11, "paper": 8, "cardboard": 6, "metal": 25, "ewaste": 55, "glass": 4}
    rate_cols = st.columns(6)
    for i, (k, v) in enumerate(rates.items()):
        rate_cols[i].metric(k.capitalize(), f"₹{v}")

    if st.button("Estimate Value", type="primary"):
        with st.spinner("Calculating..."):
            prompt = f"Estimate the value of {weight} kg of {waste_type}"
            try:
                response = run_agent(agent, prompt)
                if waste_type in st.session_state.session_waste:
                    st.session_state.session_waste[waste_type] += weight
                else:
                    st.session_state.session_waste[waste_type] = weight
                st.markdown("### Estimated Value")
                st.markdown(str(response))
                st.caption("⚠️ Indicative rate only. Actual price may vary by location and recycler.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

with tab4:
    st.subheader("Impact Dashboard")
    st.write("Track your waste segregation activity this session.")

    if not st.session_state.session_waste:
        st.info("No data yet. Use the Value Estimator tab to log waste and see your impact here.")
    else:
        with st.spinner("Calculating your impact..."):
            session_str = json.dumps(st.session_state.session_waste)
            prompt = f"Calculate the environmental impact for this session waste data: {session_str}"
            try:
                response = run_agent(agent, prompt)
                st.markdown("### Your Session Impact")
                st.markdown(str(response))

                st.divider()
                st.subheader("Waste Breakdown This Session")
                cols = st.columns(len(st.session_state.session_waste))
                for i, (wtype, wkg) in enumerate(st.session_state.session_waste.items()):
                    cols[i].metric(wtype.capitalize(), f"{wkg} kg")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

        if st.button("Reset Session"):
            st.session_state.session_waste = {}
            st.rerun()

    st.divider()
    st.caption("Impact estimates are approximate and for awareness purposes only. Built with Strands Agents SDK.")