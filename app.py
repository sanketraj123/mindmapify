import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv
load_dotenv()

# Define the API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def configure_groq():
    """Configure the Groq AI with the API key."""
    if not GROQ_API_KEY:
        st.error("API Key is missing. Please provide a valid Groq API key.")
        return None
    try:
        client = Groq(api_key=GROQ_API_KEY)
        return client
    except Exception as e:
        st.error(f"Error configuring Groq API: {str(e)}")
        return None

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if not text.strip():
            st.warning("No text could be extracted from the PDF. Please ensure it's not scanned or image-based.")
            return None
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def create_mindmap_markdown(text, client):
    """Generate mindmap markdown using Groq AI."""
    try:
        # Truncate text if too long
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            st.warning(f"Text was truncated to {max_chars} characters due to length limitations.")
        
        prompt = f"""Create a hierarchical markdown mindmap from the following text. 
Use proper markdown heading syntax (# for main topics, ## for subtopics, ### for details).
Focus on the main concepts and their relationships.
Include relevant details and connections between ideas.
Keep the structure clean and organized.

Format the output exactly like this example:
# Main Topic
## Subtopic 1
### Detail 1
- Key point 1
- Key point 2
### Detail 2
## Subtopic 2
### Detail 3
### Detail 4

Text to analyze:
{text}

Respond only with the markdown mindmap, no additional text."""

        # Use llama-3.3-70b-versatile model (fast and high quality)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=8000,
        )
        
        if not chat_completion.choices or not chat_completion.choices[0].message.content:
            st.error("Received empty response from Groq AI")
            return None
            
        return chat_completion.choices[0].message.content.strip()
        
    except Exception as e:
        error_message = str(e)
        
        if "rate_limit" in error_message.lower() or "429" in error_message:
            st.error("⚠️ **API Rate Limit Exceeded**")
            st.warning("""
            You've hit the rate limit. Groq has generous free tier limits:
            
            **Solutions:**
            1. ⏰ Wait a moment and try again
            2. 🆓 Use 'Simple Generator (no API needed)' option
            3. 🔑 Check your usage at https://console.groq.com
            """)
        else:
            st.error(f"Error generating mindmap: {error_message}")
        
        return None

def create_markmap_html(markdown_content):
    """Create HTML with enhanced Markmap visualization."""
    markdown_content = markdown_content.replace('`', '\\`').replace('${', '\\${')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            #mindmap {{
                width: 100%;
                height: 600px;
                margin: 0;
                padding: 0;
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/d3@6"></script>
        <script src="https://cdn.jsdelivr.net/npm/markmap-view"></script>
        <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.14.3/dist/browser/index.min.js"></script>
    </head>
    <body>
        <svg id="mindmap"></svg>
        <script>
            window.onload = async () => {{
                try {{
                    const markdown = `{markdown_content}`;
                    const transformer = new markmap.Transformer();
                    const {{root}} = transformer.transform(markdown);
                    const mm = new markmap.Markmap(document.querySelector('#mindmap'), {{
                        maxWidth: 300,
                        color: (node) => {{
                            const level = node.depth;
                            return ['#2196f3', '#4caf50', '#ff9800', '#f44336'][level % 4];
                        }},
                        paddingX: 16,
                        autoFit: true,
                        initialExpandLevel: 2,
                        duration: 500,
                    }});
                    mm.setData(root);
                    mm.fit();
                }} catch (error) {{
                    console.error('Error rendering mindmap:', error);
                    document.body.innerHTML = '<p style="color: red;">Error rendering mindmap. Please check the console for details.</p>';
                }}
            }};
        </script>
    </body>
    </html>
    """
    return html_content

def generate_simple_mindmap(text):
    """Generate a simple mindmap markdown as a fallback."""
    lines = text.split('\n')
    mindmap = "# Document Summary\n\n"
    
    sections = [line.strip() for line in lines[:10] if line.strip() and len(line.strip()) > 20]
    
    for i, section in enumerate(sections[:5]):
        if len(section) > 100:
            section = section[:100] + "..."
        mindmap += f"## Section {i+1}\n- {section}\n\n"
    
    return mindmap

def main():
    st.set_page_config(page_title="Mindmapify - AI-Powered Mindmaps", layout="wide")

    # Sidebar
    with st.sidebar:
        st.title("📌 Mindmapify")
        st.write("*Convert PDFs into structured interactive mindmaps using AI.*")
        st.markdown("---")
        st.write("### 🔍 How it Works:")
        st.write("1️⃣ Upload a PDF file 📄")
        st.write("2️⃣ AI extracts key information 🤖")
        st.write("3️⃣ View interactive mindmap 📊")
        st.markdown("---")
        
        api_choice = st.radio("Select AI Provider:", ["Groq AI (fast & generous free tier)", "Simple Generator (no API needed)"])
        
        if api_choice == "Groq AI (fast & generous free tier)":
            api_key = st.text_input("Enter your Groq API Key:", type="password", value=GROQ_API_KEY)
            st.info("💡 **Using Llama 3.3 70B** - Fast and powerful!")
            st.caption("Get your free API key at: https://console.groq.com")
        else:
            st.success("✅ No API key needed - generating basic mindmap")

    # Main app layout
    st.title("📚 Mindmapify - PDF to AI-Powered Mindmap")

    # File upload
    uploaded_file = st.file_uploader("📂 Upload a PDF file", type="pdf")

    if uploaded_file is not None:
        with st.spinner("🔄 Processing PDF..."):
            text = extract_text_from_pdf(uploaded_file)
            if text:
                st.success(f"✅ Successfully extracted {len(text)} characters from PDF")
                
                # Generate mindmap content
                if api_choice == "Groq AI (fast & generous free tier)":
                    client = configure_groq()
                    if client:
                        with st.spinner("🤖 Generating AI-powered mindmap..."):
                            markdown_content = create_mindmap_markdown(text, client)
                        if not markdown_content:
                            st.warning("AI generation failed. Falling back to simple generator.")
                            markdown_content = generate_simple_mindmap(text)
                    else:
                        markdown_content = generate_simple_mindmap(text)
                else:
                    markdown_content = generate_simple_mindmap(text)

                if markdown_content:
                    tab1, tab2 = st.tabs(["📊 Interactive Mindmap", "📝 Markdown View"])

                    with tab1:
                        html_content = create_markmap_html(markdown_content)
                        components.html(html_content, height=700, scrolling=True)

                    with tab2:
                        st.text_area("📝 Markdown Format", markdown_content, height=400)
                        st.download_button("⬇ Download Markdown", data=markdown_content, file_name="mindmap.md", mime="text/markdown")
                        st.download_button("⬇ Download HTML Mindmap", data=html_content, file_name="mindmap.html", mime="text/html")

if __name__ == "__main__":
    main()
