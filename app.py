
import os
import requests
import streamlit as st


st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv(
    "EKA_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

# ---------- Styling ----------

st.markdown(
    """
    <style>
    .stApp {
        background: #F7F9FC;
        color: #172B4D;
    }

    .block-container {
        max-width: 1000px;
        padding: 2rem 2rem 3rem;
    }

    /* Make text readable even if browser or theme defaults differ */
    .stApp p,
    .stApp label,
    .stApp .stMarkdown,
    .stApp [data-testid="stChatMessage"] {
        color: #24364B;
    }

    h1, h2, h3 {
        color: #142C4C !important;
    }

    .hero {
        background: linear-gradient(120deg, #E2F5F0, #EDF3FF);
        border: 1px solid #D6E8E7;
        border-radius: 18px;
        padding: 28px;
        margin-bottom: 24px;
    }

    .hero h1 {
        color: #142C4C !important;
        font-size: 2rem;
        margin: 0 0 10px;
    }

    .hero p {
        color: #52647B !important;
        line-height: 1.6;
    }

    /* Readable input field */
    div[data-testid="stTextInput"] input {
        background: #FFFFFF !important;
        color: #172B4D !important;
        border: 1px solid #C9D5E2 !important;
        border-radius: 10px !important;
        min-height: 46px;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #718096 !important;
        opacity: 1;
    }

    /* Consistent teal buttons */
    div.stButton > button,
    div.stFormSubmitButton > button {
        background: #0D9488 !important;
        color: #FFFFFF !important;
        border: 1px solid #0D9488 !important;
        border-radius: 10px !important;
        min-height: 42px;
        font-weight: 600;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background: #0F766E !important;
        border-color: #0F766E !important;
        color: #FFFFFF !important;
    }

    /* White answer and conversation panels */
    div[data-testid="stChatMessage"] {
        background: #FFFFFF;
        border: 1px solid #E0E7EF;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
    }

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    div[data-testid="stExpander"] {
        background: #FFFFFF;
        border: 1px solid #E0E7EF;
        border-radius: 12px;
    }

    /* Source excerpts should wrap instead of overflowing */
    div[data-testid="stCode"],
    pre {
        white-space: pre-wrap !important;
        overflow-wrap: anywhere !important;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ---------- API call ----------
def ask_backend(question):
    """Ask the existing FastAPI backend."""
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "content": data.get("answer", "The API returned no answer."),
            "sources": data.get("sources", []),
            "error": False,
        }

    except requests.Timeout:
        return {
            "content": (
                "The request took too long. Please try again in a moment."
            ),
            "sources": [],
            "error": True,
        }

    except requests.ConnectionError:
        return {
            "content": (
                "I couldn't connect to the knowledge assistant. "
                "Please check that the API server is running."
            ),
            "sources": [],
            "error": True,
        }

    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            detail = f" (HTTP {exc.response.status_code})"

        return {
            "content": f"The request could not be completed{detail}. Please try again.",
            "sources": [],
            "error": True,
        }

    except ValueError:
        return {
            "content": "The API returned an invalid response. Please try again.",
            "sources": [],
            "error": True,
        }


def submit_question(question):
    """Save a question and its answer in the chat history."""
    question = question.strip()
    if not question:
        return

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    result = ask_backend(question)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["content"],
            "sources": result["sources"],
            "error": result["error"],
        }
    )


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 📚 Knowledge Assistant")
    st.caption("Your company policy helper")
    st.divider()

    st.markdown("### How to use")
    st.write("1. Type a question in plain English.")
    st.write("2. Select **Ask question**.")
    st.write("3. Review the answer and its sources.")

    st.divider()
    st.markdown("### About this assistant")
    st.write(
        "Answers are generated from indexed company documents. "
        "If the documents do not contain relevant information, "
        "the assistant should say so."
    )

    st.caption("Avoid entering passwords, secrets, or unnecessary personal data.")

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()


# ---------- Main header ----------
st.markdown(
    """
    <div class="hero">
        <h1>How can I help you today?</h1>
        <p>
            Ask questions about company policies and procedures.
            Get answers with references to the indexed documents.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Example questions ----------
st.markdown('<div class="section-label">Try an example question</div>',
            unsafe_allow_html=True)

examples = [
    "Within how many days must expense claims be submitted?",
    "What documents are required for reimbursement?",
    "Who approves an expense claim?",
    "How soon must lost or stolen company equipment be reported?",
]

columns = st.columns(2)

for index, example in enumerate(examples):
    with columns[index % 2]:
        if st.button(
            example,
            key=f"example_{index}",
            use_container_width=True,
        ):
            st.session_state.pending_question = example

# ---------- Question input ----------
with st.form("question_form", clear_on_submit=True):
    question = st.text_input(
        "Your question",
        placeholder="e.g. What is the expense claim submission deadline?",
        label_visibility="collapsed",
    )

    submitted = st.form_submit_button(
        "🔎 Ask question",
        type="primary",
        use_container_width=True,
    )

if submitted and question.strip():
    st.session_state.pending_question = question.strip()

if st.session_state.pending_question:
    current_question = st.session_state.pending_question
    st.session_state.pending_question = None

    with st.spinner("Searching company documents and preparing an answer..."):
        submit_question(current_question)

    st.rerun()

# ---------- Conversation ----------
if st.session_state.messages:
    st.markdown("---")
    st.subheader("Conversation")

    for index, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])

        else:
            with st.chat_message("assistant", avatar="📚"):
                if message.get("error"):
                    st.error(message["content"])
                else:
                    st.markdown("**Answer**")
                    st.markdown(message["content"])

                sources = message.get("sources", [])

                if sources:
                    with st.expander(
                        f"📄 View supporting sources ({len(sources)})"
                    ):
                        for source in sources:
                            citation = source.get("citation", "?")
                            filename = source.get("source", "Unknown source")

                            st.markdown(f"**[{citation}] {filename}**")

                            if source.get("page") is not None:
                                st.caption(f"Page {source['page']}")

                            excerpt = source.get("excerpt", "")
                            if excerpt:
                                st.markdown("**Document excerpt**")
                                st.text(excerpt)

                            st.divider()

                elif not message.get("error"):
                    st.caption("No source references were returned by the API.")

else:
    st.info(
        "👋 Welcome! Choose an example above or enter your own question "
        "to get started."
    )

# ---------- Footer ----------
st.markdown("---")
st.caption(
    "Enterprise Knowledge Assistant · "
    "Responses are based on indexed documents and should be checked "
    "against their cited sources."
)
