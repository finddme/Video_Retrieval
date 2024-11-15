import streamlit as st
import requests
import json

# streamlit run streamlit.py --server.port 8899

def main():
    st.title("Video Retrieval System")
    
    # Sidebar
    st.sidebar.title("Navigation")
    option = st.sidebar.selectbox(
        "Choose a function",
        ["Scene Search", "Store Video Data", "Video Summary"]
    )
    
    API_URL = "http://192.168.0.186:8999"
    
    if option == "Scene Search":
        st.header("Scene Search")
        st.write("Search for specific scenes in stored videos.")
        
        query = st.text_input("Enter your search query:")
        if st.button("Search"):
            with st.spinner("Searching for relevant Video ..."):
                if query:
                    try:
                        response = requests.post(
                            f"{API_URL}/scene_search",
                            json={"user_input": query},
                            stream=True
                        )
                        
                        result_placeholder = st.empty()
                        full_response = ""
                        
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                chunk_text = chunk.decode('utf-8')
                                full_response += chunk_text
                                result_placeholder.write(full_response)
                                
                    except Exception as e:
                        st.error(f"Error occurred: {str(e)}")
                else:
                    st.warning("Please enter a search query.")
    
    elif option == "Store Video Data":
        st.header("Store Video Data")
        st.write("Store new video data for retrieval.")
        
        youtube_url = st.text_input("Enter YouTube URL:")
        if st.button("Store Data"):
            with st.spinner("Processing video data..."):
                if youtube_url:
                    try:
                        with st.spinner("Data Storing ..."):
                            response = requests.post(
                                f"{API_URL}/data_store",
                                json={"youtube_url": youtube_url}
                            )
                            if response.status_code == 200:
                                st.success("Data successfully stored!")
                            else:
                                st.error("Failed to store data.")
                    except Exception as e:
                        st.error(f"Error occurred: {str(e)}")
                else:
                    st.warning("Please enter a YouTube URL.")
    
    elif option == "Video Summary":
        st.header("Video Summary")
        st.write("Get a summary of a YouTube video.")
        
        youtube_url = st.text_input("Enter YouTube URL:")
        if st.button("Generate Summary"):
            with st.spinner("Processing Video ..."):
                if youtube_url:
                    try:
                        response = requests.post(
                            f"{API_URL}/summary",
                            json={"youtube_url": youtube_url},
                            stream=True
                        )
                        
                        result_placeholder = st.empty()
                        full_response = ""
                        
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                chunk_text = chunk.decode('utf-8')
                                full_response += chunk_text
                                result_placeholder.write(full_response)
                                
                    except Exception as e:
                        st.error(f"Error occurred: {str(e)}")
                else:
                    st.warning("Please enter a YouTube URL.")

if __name__ == "__main__":
    main()