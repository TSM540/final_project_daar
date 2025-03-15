# MoteurRecherche
DAAR | master 2 STL sorbonne université 
# 1. Installation
### 1.1. Windows
```bash   
cd backend
python -m venv env
./env/Scripts/activate
pip install -r req.txt
```
### 1.2. Macos/Linux
``` bash   
cd backend
python3 -m venv env
source ./env/bin/activate
pip3 install -r req.txt
```
Postgres should be installed in your device.

``` bash   
brew install postgresql

```

## 2. Data base
in the backend folder
```bash   
python manage.py makemigrations
python manage.py migrate
```
### 2.1. Commands to execute
These django commands needs to be executed in this specific order so that the project actually works correctly, note that these commands may take some time, depending on your CPU / internet speed so grab a coffee and call your friends ( you probably don't have any)
- Make sure to be in thed ```./backend``` folder
```sh   
mkdir keywords
python manage.py initBooks
python manage.py computeKeywords
python manage.py addKeywords
python manage.py createGraphJaccard
```
### 2.2. Workflow of `./backend/data`
The `./backend/data` directory contains all the logic related to data processing, keyword computation, and similarity graph creation.
#### 2.2.1. `initBooks`
* Fetches book data from the Gutendex API `https://gutendex.com/books/`.
* Extracts metadata such as title, author, language, and subjects, and the link to the book  eg(`https://www.gutenberg.org/cache/epub/26184/pg26184.txt`).
* Stores the data of the books in the database.
* *** Stores The book in the *** ```./backend/books```, folder with the format ```gutenberg_book_id.txt``` for each file, this approach helps simplify the calculations for the keywords, creation of neighbhoor from the jaccard distance, and makes sure that the database is filled only the with relevant information to the book but not the book itself, we make also sure that 
#### 2.2.2. `computeKeywords`

-   Processes keywords from the `./backend/books` directory.
-   Normalizes text (lowercasing, removing stopwords, stemming) using the `spacy` package.
-   Computes the final keyword list, each keyword is mapped with its occurence, and the result is a json file stored `./backend/keywords` directory where you have .
    - {
           keyword:occurence,...
        }

in a summary :
-   Ensures each book has a JSON file by:
    -   Loading language-specific NLP models (English and French).
    -   Extracting text from book files stored in the `books` directory.
    -   Processing each book's text with the appropriate language model.
    -   Applying lemmatization and filtering to extract meaningful keywords.
    -   Counting keyword occurrences and storing them in JSON format.
    -   Saving the keyword data to the `keywords` directory using the book's ID as the filename.

#### 2.2.3. `addKeywords`

- Reads pre-extracted keyword JSON files from the `keywords` directory.
- Each filename corresponds to a book's primary key (e.g., `123.json`).
- Each file contains a JSON dictionary mapping keywords to their occurrence counts.


1.  **Initialization:**
    -   Initializes dictionaries to track keywords and their language associations (English and French).
    -   Each language will have its own keywords, eg( data_keywordsenglish), so each keyword is unique. 

2.  **File Iteration:**
    -   Iterates through each keyword file in the `keywords` directory.
    -   For each file:
        -   **Book ID Extraction:** Extracts the book ID from the filename eg : `123.json`.
        -   **JSON Data Loading:** Loads the keyword data from the JSON file with its occurences.
        -   **Book Retrieval:** Retrieves the corresponding book object from the database.
        -   **Language Categorization:** Categorizes keywords by language (English or French), each language has its own correspondance table (eg : `data_keywordbook${language}`), the point is is mapping each keyword from a specific book, with its occurence.
        -   **Keyword Mapping:** Maps each keyword to book/occurrence pairs, so the table would be (id,occurence,book_id,keyword_id).

### Database Operations

1.   Keywords : 

    -   For all  distinct ${Language} keywords:
        -   Creates `Keywords${Language}` objects.
        -   Creates `KeywordBook${Language}` relationship objects connecting:
            -   Books
            -   Occurrence counts
            -   Keywords
        -  Now each keyword has its unique id.
    




#### 2.2.4. `createGraphJaccard`

-   Computes Jaccard similarity between books based on their keywords.
-   Creates a graph where books with similarity above a threshold (0.6) are linked.
-   Stores neighbor relationships in the `Neighbors` model:
    -   Loads all keyword JSON files from the `keywords` directory.
    -   Creates a dictionary mapping book IDs to their keyword occurrences.
    -   Compares each book with all other books using the Jaccard distance function.
    -   When the distance is below the threshold (indicating similarity), connects books as neighbors.
    -   Creates bi-directional neighbor relationships in the database.
    - Creates an index table mapping each keyword id, to its book id, and with its occurence, the index table is created for each language eg `keywordbook_${language}`

#### 2.3. Jaccard Similarity

-   The Jaccard similarity coefficient is used to determine the similarity between two sets of keywords:
    -   `J(A, B) = |A ∩ B| / |A ∪ B|`
    -   Where:
        -   `A` and `B` are the sets of keywords for two books.
        -   `|A ∩ B|` is the number of common keywords.
        -   `|A ∪ B|` is the total number of unique keywords in both books.
-   A Jaccard score above 0.4 indicates that two books are sufficiently similar to be considered neighbors.
-   Our implementation:
    -   Calculates the difference between keyword occurrence counts.
    -   Divides by the maximum possible difference.
    -   Returns distance (lower values indicate greater similarity).
    -   Uses a threshold of 0.6 for distance.

#### 2.4. Serialization (`serializers.py`)

-   Converts Django model instances into JSON format for API responses.
-   Serializes books, their metadata, and neighbor relationships:
    -   `LanguageSerializer`: Exposes language code.
    -   `PersonSerializer`: Includes author name, birth, and death years.
    -   `SubjectSerializer`: Provides subject names.
    -   `BookSerializer`: Comprehensive book data including authors, languages, and subjects.

#### 2.5. Configuration (`config.py`)

-   Contains global settings like threshold values for Jaccard similarity.
-   Defines paths for keyword storage.

#### 2.6. Views (`views.py`)

-   Handles API endpoints:
    -   `data/books/`: Returns the list of books with filtering options:
        -   Language filtering.
        -   Author name search (classic or regex).
        -   Title search (classic or regex).
        -   Keyword search with language specification.
        -   Download count sorting.
    -   `data/books/neighbors/<int:pk>`: Returns neighbors of a given book:
        -   Retrieves neighbor relationships from the database.
        -   Returns detailed book information for all neighbors.
    -   `server/books/`: General book-related operations.

### 2.3. Workflow of `./backend/server`

#### `views.py`: API Endpoint for Book Lists

-   **Purpose:** Handles API requests to retrieve and sort book lists, and provides book suggestions.
-   **Workflow:**
    1.  Receives a request to `/server/books/`.
    2.  Forwards the request (with URL modification) to the `/data/books/` API to fetch book data.
    3.  Parses query parameters for sorting (by centrality) and order.
    4.  If sorting is requested, utilizes `sort.py` to sort the books using graph-based centrality measures.
    5.  Generates book suggestions using `sort.py`.
    6.  Returns a JSON response containing the sorted book list and suggestions.

#### `sort.py`: Sorting and Suggestion Logic

-   **Purpose:** Implements sorting based on graph centrality and generates book suggestions.
-   **Workflow:**
    1.  **Suggestions:**
        -   Retrieves neighbor books from the `/data/books/neighbors/` API for the top books in the list.
        -   Filters out books already in the list or suggestion list.
        -   Returns a list of unique suggested books.
    2.  **Sorting by Centrality:**
        -   Constructs a graph (weighted or unweighted) based on book subject similarities.
        -   Calculates centrality measures (closeness or betweenness) using graph algorithms.
        -   Sorts books based on their calculated centrality scores.
        -   Returns the sorted list of books.
-   **Graph Representation:**
    -   Books are represented as nodes in the graph.
    -   Edges between nodes represent similarity between books.
    -   **Node Weight:** In a weighted graph, the weight of an edge represents the degree of similarity between two books, calculated by the number of shared subjects.
    -   **Adding Neighbors:** Neighbors are added based on the intersection of the subject lists of the books. If the intersection is not empty, an edge is created between the corresponding nodes.

#### `urls.py`: URL Routing

-   **Purpose:** Defines the URL endpoint for the book list API.
-   **Functionality:** Maps the `/server/books/` URL to the `BooksList` view in `views.py`.

#### `graph.py`: Graph Data Structures and Algorithms

-   **Purpose:** Implements graph data structures and centrality algorithms.
-   **Graph Representation:**
    -   Uses `Node` classes to represent books, storing book data and centrality scores.
    -   `UnweightedGraph` and `WeightedGraph` classes provide graph implementations.
    -   Edges are stored as neighbor relationships within the nodes.
-   **Centrality Algorithms:**
    -   Implements Brandes' algorithm for calculating betweenness centrality in unweighted graphs.
-   **Adding Neighbors:**
    -   `UnweightedGraph`: Adds neighbor nodes to a node's neighbor list.
    -   `WeightedGraph`: Adds neighbor nodes with their corresponding edge weights to a node's neighbor dictionary.

#### `config.py`: Server Configuration

-   **Purpose:** Stores configuration settings for the server.
-   **Functionality:** Defines the base URL for the server API.

#### `centrality.py`: Centrality Calculation

-   **Purpose:** Implements algorithms for calculating closeness and betweenness centrality.
-   **Closeness Centrality:**
    -   Calculates the sum of edge weights to all other nodes.
    -   The closeness centrality is inversely proportional to the sum of these weights.
-   **Betweenness Centrality:**
    -   Calculates the number of shortest paths passing through a node.
    -   Uses Brandes' algorithm for efficient calculation.
-   **Functionality:**
    -   Provides functions to compute both closeness and betweenness centrality measures.
    -   Uses graph data structures from `graph.py`.
## 4. Server startup
in the ```./backend``` folder, execute :
```bash
python manage.py runserver
```
default host is ```localhost:8000``` 
## 5. Frontend startup

``` bash
cd frontend
npm i 
npm run dev
```
default host is ```localhost:3000``` 

## 6. Results 
- each language had it own index table, a total of 95k tokens in both english and french.
