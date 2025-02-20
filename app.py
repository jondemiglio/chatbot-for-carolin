
import streamlit as st
import openai
import PyPDF2
import docx
import pandas as pd

# -------------------------------------------------
# 1. Retrieve API key from st.secrets and set up the client
# -------------------------------------------------
openai.api_key = st.secrets["openai"]["api_key"]

# -------------------------------------------------
# 2. Define a function to extract text from different file types
# -------------------------------------------------
def extract_text(file):
    text = ""
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file.type == "text/plain":
        text = file.read().decode("utf-8")
    elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        xls = pd.ExcelFile(file)
        for sheet_name in xls.sheet_names:
            sheet_df = xls.parse(sheet_name)
            text += f"\nSheet: {sheet_name}\n"
            text += sheet_df.to_markdown(index=False) + "\n"
    return text

# -------------------------------------------------
# 3. Streamlit app configuration
# -------------------------------------------------
st.set_page_config(page_title="Chat with Documents", layout="wide")
st.title("📄 Chat with Your Documents")

# -------------------------------------------------
# 4. Initialize session state variables
# -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "documents" not in st.session_state:
    st.session_state["documents"] = []
if "uploaded_file_names" not in st.session_state:
    st.session_state["uploaded_file_names"] = []

# -------------------------------------------------
# 5. Sidebar for file uploads
# -------------------------------------------------
st.sidebar.header("Upload Documents")
uploaded_files = st.sidebar.file_uploader(
    "Upload PDF, DOCX, TXT, or XLSX files",
    type=["pdf", "docx", "txt", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    with st.spinner("Processing files..."):
        for file in uploaded_files:
            if file.name not in st.session_state["uploaded_file_names"]:
                extracted_text = extract_text(file)
                st.session_state["documents"].append(extracted_text)
                st.session_state["uploaded_file_names"].append(file.name)
    st.sidebar.success("Files uploaded and processed!")


if st.sidebar.button("Clear Chat"):
    st.session_state["messages"] = []
    st.rerun()

# -------------------------------------------------
# 6. Display chat history
# -------------------------------------------------
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------------------------
# 7. Chat input and processing
# -------------------------------------------------
user_input = st.chat_input("Ask something about your documents or anything else...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build the messages context for OpenAI API
    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    if st.session_state["documents"]:
        st.write(f"DEBUG: Documents stored - {len(st.session_state['documents'])} documents")
        combined_docs = "\n".join(st.session_state["documents"])
        limited_docs = combined_docs
        messages.append({"role": "user", "content": f"Full document text: {limited_docs}"})
            
    messages.append({"role": "user", "content": user_input})

    try:
        with st.spinner("Thinking..."):
            response = openai.chat.completions.create(
                model="gpt-4o",  # or "gpt-3.5-turbo" if preferred
                messages=messages,
                temperature=0.7
            )
        answer = response.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
    except Exception as e:
        st.error(f"Error: {e}")

