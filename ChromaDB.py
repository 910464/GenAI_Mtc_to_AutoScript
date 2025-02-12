def decode_json_objects(self, json_string):
        json_objects = json_string.split('\n')
        decoded_objects = []
        for obj in json_objects:
            if obj.strip():  # Skip empty lines
                decoded_objects.append(json.loads(obj))
        return decoded_objects

    def get_context_by_id(self, context_key):
        """
        Retrieve the context for a given key from ChromaDB.
        """
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        results = db.get(where=filters)
        if results['documents']:
            # Assuming the first document is the one we want
            doc = results['documents'][0]
            return json.loads(doc)  # Convert JSON string back to dictionary
        return None

    def update_context_in_chromadb(self, context, context_key):
        """
        Update the context for a given key in ChromaDB.
        """
        # Retrieve the existing context
        existing_context = self.get_context_by_id(context_key)
        if existing_context:
            # Compare existing context with the new context
            if existing_context != json.dumps(context):
                # Delete the existing context
                self.delete_context_by_id(context_key)
                # Store the new context
                self.store_context_in_chromadb(context, context_key)
                # print(f"Updated context for key: {context_key}")
            else:
                print(f"Context for key: {context_key} is already up-to-date.")
        else:
            # If no existing context, store the new context
            self.store_context_in_chromadb(context, context_key)
            print(f"Stored new context for key: {context_key}")

    def store_context_in_chromadb(self, context, context_key):
        context_json = json.dumps(context)
        data = [context_json]
        metadata = [{"source": "crawl_function", "context_key": context_key}]
        ids = [context_key]  # Use the context_key directly as the ID

        self.text_store(data=data, metadata=metadata, ids=ids)

    def delete_context_by_id(self, context_key):
        """
        Delete the context for a given key from ChromaDB.
        """
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        # print(f"Filters: {filters}")  # Debug print to check filters

        # Retrieve the documents that match the key
        results = db.get(where=filters)
        # print(f"Results: {results}")  # Debug print to check results

        # Extract the IDs directly from the results
        ids_to_delete = results['ids']
        # print(f"IDs to delete: {ids_to_delete}")  # Debug print to check IDs

        # Delete the documents using the retrieved IDs
        db.delete(ids=ids_to_delete)
        # print(f"Deleted context for key: {context_key}")

    def retrieval_html_context(self, query, context_key):
        retrieval_dir = r"../Data/RetrievalContext"

        # Create the directory if it doesn't exist
        os.makedirs(retrieval_dir, exist_ok=True)

        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        docs = db.get(where=filters)
        docs_with_similarity = {}
        self.context = ""
        for doc in docs['documents']:
            # print(score, doc)
            docs_with_similarity = doc

        retrieved_docs = db.get(where=filters)
        for doc in retrieved_docs['documents']:
            content = doc
            self.context += (content + '\n')
        # Debugging: Print the retrieved context
        # print("Retrieved context:", self.context)

        # Decode JSON objects if necessary
        try:
            filtered_elements = self.decode_json_objects(self.context)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None, None, None

        # Filter elements based on the query using cosine similarity
        filtered_elements = self.filter_elements_with_similarity(filtered_elements, query)

        # Debugging: Print the filtered elements
        # print("Filtered elements:", filtered_elements)

        output_path = f"{retrieval_dir}/retrieved_{self.timestamp}.txt"
        with open(output_path, "a", encoding="utf-8") as file:
            file.write(self.context)
        # print(self.threshold)
        return json.dumps(filtered_elements), docs_with_similarity, self.threshold

    def filter_elements_with_similarity(self, context, query, top_k=20):
        query_embedding = self.embeddings.embed_query(query)
        similarities = []
        unique_elements = set()

        # Flatten the nested list of dictionaries
        flattened_context = [item for sublist in context for item in sublist]

        # Filter elements with the key "element"
        elements = [item for item in flattened_context if "element" in item and item["element"]]
        element_texts = [item["element"] for item in elements]
        element_embeddings = self.embeddings.embed_documents(element_texts)

        query_embedding = np.array(query_embedding).reshape(1, -1)
        element_embeddings = np.array(element_embeddings)
        cosine_similarities = cosine_similarity(query_embedding, element_embeddings)[0]

        for idx, item in enumerate(elements):
            unique_id = f"{item['xpath']}-{item['element']}"
            if unique_id not in unique_elements:
                similarities.append((item, cosine_similarities[idx]))
                unique_elements.add(unique_id)

        similarities.sort(key=lambda x: x[1], reverse=True)
        filtered_elements = [element for element, similarity in similarities[:top_k]]

        return filtered_elements
