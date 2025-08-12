import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq # Using Groq as an example for the LLM
import re
import fitz  # The PyMuPDF library

class ResumeRAG:
    """
    A class to perform Retrieval-Augmented Generation (RAG) on resumes
    to rate candidates based on specific criteria.
    """
    def __init__(self, folder_path: str, llm):
        """
        Initializes the RAG pipeline by loading, splitting, and embedding documents.

        Args:
            folder_path (str): The path to the folder containing resume documents.
            llm: An initialized LangChain compatible language model.
        """
        self.folder_path = folder_path
        self.llm = llm
        self.vectorstore = self._load_and_process_documents()
        self.prompt_template = self._get_prompt_template()

    def _load_and_process_documents(self) -> Chroma:
        """
        Loads documents, splits them into chunks, and creates a vector database.
        """
        # 1. Load documents from the specified folder
        print(f"Loading documents from: {self.folder_path}")
        documents = self._load_documents_from_folder()
        print(f"Loaded {len(documents)} documents.")

        if not documents:
            raise ValueError("No documents found in the specified folder.")

        # 2. Create chunks from the loaded documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        splits = text_splitter.split_documents(documents)
        print(f"Split documents into {len(splits)} chunks.")

        # 3. Generate embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        

        # 4. Create and persist the vector database
        print("Creating vector database...")
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        print("Vector database created successfully.")
        return vectorstore

    def _load_documents_from_folder(self) -> List[Document]:
        """Helper function to load PDF and DOCX files."""
        documents = []
        for filename in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, filename)
            loader = None
            if filename.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif filename.endswith('.docx'):
                loader = Docx2txtLoader(file_path)
            else:
                print(f"Unsupported file type skipped: {filename}")
                continue
            
            try:
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading file {filename}: {e}")
        return documents

    def _get_prompt_template(self) -> PromptTemplate:
        """Creates and returns the parametrized prompt template."""
        return PromptTemplate.from_template('''
            You are an expert HR screening assistant. Your task is to analyze the provided resume context and generate two numerical ratings based on specific criteria.

            **Context from Resume:**
            ---
            {context}
            ---

            **Evaluation Criteria:**

            1.  **Work Experience:** The ideal candidate has at least **{required_experience} years** of total work experience.
            2.  **Skills:** The ideal candidate has expertise in the following technologies: **{required_skills}**.

            **Instructions:**

            1.  **For 'work_ex_rating':** Carefully review the context to determine the candidate's total work experience.
                - If the candidate has {required_experience} or more years of experience, rate them between 8 and 10.
                - If they have less, provide a proportionally lower score.
                - If no work experience is mentioned, the score is 0.

            2.  **For 'skills_rating':** Carefully review the context for mentions of the required skills ({required_skills}).
                - The score should reflect how many of the required skills are present. A candidate with all skills should receive a high score (8-10).
                - If proficiency levels are mentioned (e.g., "expert," "advanced"), consider that in your rating.
                - If no relevant skills are mentioned, the score is 0.

            **Output Format:**
            Provide your response ONLY as a JSON object with two keys: "work_ex_rating" and "skills_rating".
            ''')

    def rate_candidate(self, required_experience_years: int, required_skills_list: List[str]) -> dict:
        """
        Retrieves relevant resume sections and uses an LLM to rate the candidate.

        Args:
            required_experience_years (int): The required years of experience.
            required_skills_list (list): A list of required skills.

        Returns:
            dict: A dictionary with 'work_ex_rating' and 'skills_rating'.
        """
        # Convert skills list to a string for the prompt and retriever
        required_skills_str = ", ".join(required_skills_list)
        retriever_query = (
            f"A candidate with at least {required_experience_years} years of work experience "
            f"and expertise in {required_skills_str}."
        )
        
        # Retrieve relevant documents from the vector store
        print(f"\nRetrieving documents for query: '{retriever_query}'")
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5}) # Retrieve more chunks for better context
        relevant_docs = retriever.invoke(retriever_query)
        context_text = "\n\n".join(doc.page_content for doc in relevant_docs)

        # Define the LangChain Expression Language (LCEL) chain
        chain = (
            self.prompt_template
            | self.llm
            | JsonOutputParser()
        )

        # Invoke the chain with all required parameters
        print("Invoking LLM to generate ratings...")
        ratings = chain.invoke({
            "context": context_text,
            "required_experience": required_experience_years,
            "required_skills": required_skills_str
        })
        
        return ratings


def extract_email_from_text(text: str) -> str | None:
    """
    This function is correct and does not need to be changed.
    It finds the first email address in a block of text using regex.
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    match = re.search(email_pattern, text)
    if match:
        return match.group(0)
    return None


def get_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a PDF file using the robust PyMuPDF library."""
    try:
        with fitz.open(pdf_path) as doc:
            full_text = ""
            for page in doc:
                full_text += page.get_text()
        return full_text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""


   
    
    