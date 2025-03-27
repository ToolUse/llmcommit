"""Demo application for AI Commit Blueprint."""

import streamlit as st
from llm_commit_generator.commit_generator import generate_commit_messages

# Set page config
st.set_page_config(
    page_title="AI Commit Message Generator",
    page_icon="✅",
    layout="wide",
)

# Add title and description
st.title("AI Commit Message Generator")
st.subheader("Generate commit messages with AI")

# Add sidebar with options
st.sidebar.title("Settings")
service_type = st.sidebar.radio("Select AI Service", ["ollama", "jan"])
max_chars = st.sidebar.slider("Max Characters", 20, 150, 75)
ollama_model = st.sidebar.text_input("Ollama Model", "llama3.1")

# Main content
git_diff = st.text_area("Paste your git diff here:", height=300)

# Generate button
if st.button("Generate Commit Messages"):
    if git_diff:
        with st.spinner("Generating commit messages..."):
            try:
                commit_messages = generate_commit_messages(
                    diff=git_diff,
                    max_chars=max_chars,
                    service_type=service_type,
                    ollama_model=ollama_model,
                )

                # Display results
                st.success("Generated Commit Messages:")
                for i, message in enumerate(commit_messages, 1):
                    st.markdown(f"**Option {i}:** {message}")

                    # Add a copy button for each message
                    if st.button(f"Use Message {i}", key=f"use_{i}"):
                        st.code(message)
                        st.info(
                            "Copy the message above and use it in your git commit command"
                        )
            except Exception as e:
                st.error(f"Error generating commit messages: {e}")
    else:
        st.warning("Please paste a git diff first.")
