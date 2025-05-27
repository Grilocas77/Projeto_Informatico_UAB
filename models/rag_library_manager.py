import os
import hashlib
import json
import logging
import re
from transformers import AutoTokenizer
from config import MAX_PROMPT_TOKENS
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from config import CHROMA_PATH, EMBEDDING_MODEL, DOCUMENTS_PATH, CHUNK_SIZE, CHUNK_OVERLAP

logging.basicConfig(filename="logs/rag_library_manager.log", level=logging.INFO)

def split_by_semantic_patterns(text):
    """
    Split inteligente por títulos, definições, secções, linhas vazias, etc.
    """
    # Inclui headings, subtítulos, padrões de definição e separadores
    pattern = (
            r"(?=^ *(?:Associação|Agregação|Composição|Ator|Actor|Diagrama|Definição|Resumo|Sintaxe|Exemplo)[\s:–-])"
            r"|(?=^(?:[A-Z][A-Z\s]{5,}\n))"
            r"|(?=^\d+\.\d+\.?.*)"
            r"|(?=^#+ )"
            r"|(?=\n{2,})"
        )
    # Garante que não tenta fazer strip em None
    return [c.strip() for c in re.split(pattern, text, flags=re.MULTILINE) if c and isinstance(c, str) and c.strip()]

def is_informative_chunk(text):
    """
    Heurística para filtrar chunks inúteis antes de indexar.
    - Remove títulos isolados, listas, legendas, só números, referências, etc.
    - Pode ser afinado conforme a natureza dos teus documentos.
    """
    # Demasiado pequeno
    if len(text.strip()) < 40:
        return False
    # Só títulos em capslock
    if re.fullmatch(r'^[A-Z\s]{8,}$', text):
        return False
    # Legendas e referências (figura, tabela, quadro, etc.)
    if re.search(r"(figura|fonte|tabela|quadro|exemplo|resumo)[\s:–-]*\d*", text, re.I):
        return False
    # Referências tipo [1], (1), {1}
    if re.fullmatch(r'(\[?\(?\{?\d+\}?\)?\]?\.? *)+$', text):
        return False
    # Listas puras
    if re.match(r"^[\*\-\+]\s+\w+", text):
        return False
    # Linhas só com números/pontuação
    if re.fullmatch(r'^[\d\s\.,;:-]+$', text):
        return False
    return True

class RAGLibraryManager:
    def __init__(self,
                 documents_path=DOCUMENTS_PATH,
                 chroma_path=CHROMA_PATH,
                 embedding_model=EMBEDDING_MODEL,
                 chunk_size=CHUNK_SIZE,
                 chunk_overlap=CHUNK_OVERLAP):
        self.documents_path = documents_path
        self.chroma_path = chroma_path
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
        self.tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
        self.max_tokens_per_chunk = MAX_PROMPT_TOKENS
        self.chunks_indexed_path = os.path.join(self.chroma_path, "indexed_docs.json")
        os.makedirs(self.chroma_path, exist_ok=True)

    def build(self, force_rebuild=False, progress_callback=None):
        """Cria ou reconstrói a base vetorial."""
        if force_rebuild:
            self.clear_chroma()
            logging.info("ChromaDB limpa para rebuild total.")

        all_docs = self._load_documents()
        if not all_docs:
            logging.warning("Nenhum documento encontrado para indexar.")
            return

        chunks = self._split_and_clean(all_docs)
        unique_chunks = self._deduplicate_chunks(chunks)
        self._index_chunks(unique_chunks, progress_callback=progress_callback)
        self._save_indexed_docs(all_docs)
        logging.info("Build/Rebuild finalizado com %d chunks únicos.", len(unique_chunks))

    def update(self, progress_callback=None):
        """Update incremental: só indexa documentos novos ou alterados."""
        prev_index = self._load_indexed_docs()
        all_docs = self._load_documents()
        new_or_modified = [doc for doc in all_docs if self._needs_update(doc, prev_index)]
        if not new_or_modified:
            logging.info("Nenhum documento novo ou alterado para indexar.")
            return

        chunks = self._split_and_clean(new_or_modified)
        unique_chunks = self._deduplicate_chunks(chunks)
        self._index_chunks(unique_chunks, progress_callback=progress_callback)
        self._save_indexed_docs(all_docs)
        logging.info("Update incremental finalizado com %d novos chunks.", len(unique_chunks))

    def _index_chunks(self, chunks, progress_callback=None):
        if not chunks:
            logging.info("Nenhum chunk para indexar.")
            return
        db = Chroma(persist_directory=self.chroma_path, embedding_function=self.embeddings)
        total = len(chunks)
        for idx, chunk in enumerate(chunks, 1):
            db.add_documents([chunk])
            # Safe callback para progress bar (Tkinter deve receber via .after())
            if progress_callback:
                try:
                    progress_callback(idx, total)
                except Exception as exc:
                    logging.warning(f"Erro no progress_callback: {exc}")
        db.persist()
        logging.info("Indexação finalizada com sucesso.")

    def _load_documents(self):
        txt_loader = DirectoryLoader(self.documents_path, glob="**/*.txt", loader_cls=TextLoader)
        pdf_loader = DirectoryLoader(self.documents_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
        docs = txt_loader.load() + pdf_loader.load()
        valid_docs = [doc for doc in docs if self._is_valid_document(doc)]
        return valid_docs

    def _split_and_clean(self, docs):
        from langchain.schema import Document
        refined_chunks = []
        for doc in docs:
            text = getattr(doc, "page_content", "")
            if not text or not isinstance(text, str):
                logging.warning(f"Documento sem conteúdo ou não-string: {repr(doc)}")
                continue
            parts = split_by_semantic_patterns(text)
            for part in parts:
                if not part or not isinstance(part, str):
                    logging.warning(f"Parte inválida (None ou não-string): {repr(part)}")
                    continue
                # Limpeza base
                part = re.sub(r"^\s*[A-Z\s]{8,}$", "", part, flags=re.MULTILINE)
                part = re.sub(r"\[?\d{1,3}\]?", "", part)
                part = re.sub(r"(FIGURA|FONTE|TABELA|QUADRO|EXEMPLO|RESUMO).*", "", part, flags=re.IGNORECASE)

                try:
                    tokens = self.tokenizer.encode(part, add_special_tokens=False)
                except Exception:
                    logging.warning(f"Erro ao tokenizar chunk: {repr(part)}")
                    continue

                # Novo: Split forçado a max_tokens_per_chunk (default=512)
                max_tokens = getattr(self, "max_tokens_per_chunk", 512)
                if len(tokens) > max_tokens:
                    # Divide o chunk sempre que ultrapassa o limite do modelo
                    for i in range(0, len(tokens), max_tokens):
                        sub_tokens = tokens[i:i + max_tokens]
                        chunk_text = self.tokenizer.decode(sub_tokens)
                        cleaned = chunk_text.strip()
                        if cleaned and is_informative_chunk(cleaned):
                            fake_doc = Document(page_content=cleaned, metadata=getattr(doc, "metadata", {}))
                            refined_chunks.append(self._clean_chunk(fake_doc))
                else:
                    cleaned = part.strip()
                    if cleaned and is_informative_chunk(cleaned):
                        fake_doc = Document(page_content=cleaned, metadata=getattr(doc, "metadata", {}))
                        refined_chunks.append(self._clean_chunk(fake_doc))
        return refined_chunks

    @staticmethod
    def _deduplicate_chunks(chunks):
        seen = set()
        unique = []
        for chunk in chunks:
            content = getattr(chunk, "page_content", "")
            if not content or not isinstance(content, str):
                continue
            h = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
            if h not in seen:
                seen.add(h)
                unique.append(chunk)
        return unique

    @staticmethod
    def _clean_chunk(chunk):
        text = getattr(chunk, "page_content", "")
        if not text or not isinstance(text, str):
            chunk.page_content = ""
            return chunk
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"(FIGURA|FONTE|CONSIDERANDO|QUADRO|TABELA)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[?\d{1,3}\]?", "", text)
        chunk.page_content = text.strip()
        return chunk

    @staticmethod
    def _is_valid_document(doc):
        # Exemplo: verifica se não está vazio e não é demasiado pequeno
        return hasattr(doc, "page_content") and len(doc.page_content.strip()) > 50

    @staticmethod
    def _needs_update(doc, prev_index):
        # Doc hash ou modificação de timestamp
        meta = getattr(doc, "metadata", {})
        path = meta.get("source", "")
        if not path:
            return True
        stat = os.stat(path)
        doc_hash = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()
        prev = prev_index.get(path, {})
        return prev.get("hash") != doc_hash or prev.get("mtime") != stat.st_mtime

    def _save_indexed_docs(self, docs):
        index = {}
        for doc in docs:
            meta = getattr(doc, "metadata", {})
            path = meta.get("source", "")
            if not path:
                continue
            stat = os.stat(path)
            doc_hash = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()
            index[path] = {"hash": doc_hash, "mtime": stat.st_mtime}
        with open(self.chunks_indexed_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def _load_indexed_docs(self):
        if not os.path.exists(self.chunks_indexed_path):
            return {}
        with open(self.chunks_indexed_path, encoding="utf-8") as f:
            return json.load(f)

    def clear_chroma(self):
        import shutil
        if os.path.exists(self.chroma_path):
            shutil.rmtree(self.chroma_path)
            os.makedirs(self.chroma_path, exist_ok=True)
